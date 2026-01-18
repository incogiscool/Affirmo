#!/usr/bin/env python3
"""
Therapy Robot - Laptop Audio Controller (ElevenLabs)

Reads responses from ESP32 Gateway via Serial
- AI responses: ElevenLabs TTS
- 67 Emote: Plays local audio file

Voice changes based on mode:
  - Evil mode: Adam (deep male)
  - Therapy mode: Sarah (soft female)

Install dependencies:
  pip install pyserial requests pygame

Set your API key:
  export ELEVENLABS_API_KEY="your-key-here"

Run:
  python3 laptop_elevenlabs.py
"""

import serial
import serial.tools.list_ports
import requests
import pygame
import threading
import queue
import sys
import time
import os
import tempfile

# ==================== CONFIGURATION ====================

BAUD_RATE = 115200

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_e91311b22ee997b19e3a10c7506fee71c29f19cab35d5c7e")

# 67 Emote audio file - change this to your file path
EMOTE_67_AUDIO = "67_emote.mp3"  # Put your audio file in same folder

# Voice IDs
VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",
    "sarah": "EXAVITQu4vr4xnSDxMaL",
}

# Current mode and voice
current_mode = "evil"
current_voice = VOICES["adam"]

# Voice settings
STABILITY = 0.5
SIMILARITY_BOOST = 0.75

# ==================== FIND ESP32 ====================

def find_esp32_port():
    """Auto-detect ESP32 serial port"""
    ports = serial.tools.list_ports.comports()
    
    print("Scanning for ESP32...")
    
    for port in ports:
        desc = port.description.lower()
        if any(x in desc for x in ["cp210", "ch340", "usb", "serial", "uart"]):
            print(f"  Found: {port.device} - {port.description}")
            return port.device
    
    print("Available ports:")
    for port in ports:
        print(f"  {port.device}: {port.description}")
    
    return None


# ==================== AUDIO PLAYBACK ====================

audio_queue = queue.Queue()
audio_thread = None

def play_local_audio(filepath):
    """Play a local audio file"""
    if not os.path.exists(filepath):
        print(f"⚠️ Audio file not found: {filepath}")
        return False
    
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        return True
    except Exception as e:
        print(f"Error playing audio: {e}")
        return False


def text_to_speech_elevenlabs(text, voice_id):
    """Convert text to speech using ElevenLabs API"""
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": STABILITY,
            "similarity_boost": SIMILARITY_BOOST
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"ElevenLabs Error: {response.status_code}")
            print(response.text)
            return None
        
        return response.content
    
    except Exception as e:
        print(f"ElevenLabs Error: {e}")
        return None


def play_tts_audio(audio_data):
    """Play TTS audio data using pygame"""
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_data)
        temp_path = f.name
    
    try:
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    finally:
        os.unlink(temp_path)


def audio_worker():
    """Background thread that handles all audio"""
    
    pygame.mixer.init()
    
    while True:
        try:
            item = audio_queue.get(timeout=1)
            if item is None:
                break
            
            audio_type, data = item
            
            if audio_type == "emote_67":
                print(f"\n🎵 Playing 67 emote audio...\n")
                play_local_audio(EMOTE_67_AUDIO)
            
            elif audio_type == "tts":
                text, voice_id = data
                voice_name = "Adam" if voice_id == VOICES["adam"] else "Sarah"
                print(f"\n🔊 [{voice_name}]: {text}\n")
                
                audio_data = text_to_speech_elevenlabs(text, voice_id)
                if audio_data:
                    play_tts_audio(audio_data)
                else:
                    print("   Failed to generate audio")
            
            audio_queue.task_done()
        
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Audio Error: {e}")


def init_audio():
    global audio_thread
    print("Initializing audio system...")
    audio_thread = threading.Thread(target=audio_worker, daemon=True)
    audio_thread.start()
    print("Audio ready!")


def speak(text):
    """Queue text for TTS"""
    audio_queue.put(("tts", (text, current_voice)))


def play_emote_67():
    """Queue 67 emote audio"""
    audio_queue.put(("emote_67", None))


# ==================== MODE SWITCHING ====================

def set_mode(mode):
    """Switch mode and voice"""
    global current_mode, current_voice
    
    mode = mode.lower()
    
    if mode == "evil":
        current_mode = "evil"
        current_voice = VOICES["adam"]
        print("🔴 Mode: EVIL (Voice: Adam)")
    elif mode == "therapy":
        current_mode = "therapy"
        current_voice = VOICES["sarah"]
        print("🟢 Mode: THERAPY (Voice: Sarah)")


# ==================== SERIAL HANDLING ====================

def is_ai_response(line):
    """Check if this is an AI-generated response"""
    
    if len(line) < 20:
        return False
    
    skip_patterns = [
        "════", "═══", "Sent:", "Send status:",
        "RESPONSE FROM ROBOT:", "FROM GATEWAY:",
        "To Gateway:", "Ready!", "Press buttons",
        "GPIO", "ESP32", "MAC:", "ESP-NOW",
        "peer", "Waiting", "DONE", "MODE:",
        "Mode:", "EMOTE", "CAMERA", "CAM"
    ]
    
    for pattern in skip_patterns:
        if pattern in line:
            return False
    
    return True


def handle_line(line):
    """Process incoming serial data"""
    line = line.strip()
    
    if not line:
        return
    
    print(f"📥 {line}")
    
    # Mode change
    if line.startswith("MODE:") or line.startswith("Mode:"):
        mode = line.split(":")[1].strip().lower()
        set_mode(mode)
        return
    
    # 67 Emote - play local audio (only on "EMOTE 67 DONE", not other messages)
    if line == "EMOTE 67 DONE":
        play_emote_67()
        return
    
    # AI response - TTS
    if is_ai_response(line):
        speak(line)


# ==================== MAIN ====================

def main():
    global current_mode, current_voice
    
    # Check API key
    if ELEVENLABS_API_KEY == "your-key-here":
        print()
        print("=" * 50)
        print("ERROR: Set your ElevenLabs API key!")
        print()
        print("  export ELEVENLABS_API_KEY='your-key-here'")
        print()
        print("Get your key at: https://elevenlabs.io")
        print("=" * 50)
        sys.exit(1)
    
    # Check for 67 emote audio file
    if not os.path.exists(EMOTE_67_AUDIO):
        print()
        print("=" * 50)
        print(f"WARNING: 67 emote audio file not found!")
        print(f"  Expected: {EMOTE_67_AUDIO}")
        print()
        print("Put your audio file in the same folder as this script")
        print("or update EMOTE_67_AUDIO path in the script.")
        print("=" * 50)
        print()
    
    # Find ESP32 port
    port = find_esp32_port()
    
    if not port and len(sys.argv) < 2:
        print()
        print("ESP32 not found. Specify port manually:")
        print("  python3 laptop_elevenlabs.py /dev/cu.usbserial-0001")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    # Init audio
    init_audio()
    
    # Open serial port
    print(f"Connecting to {port}...")
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=0.5)
        time.sleep(2)
    except serial.SerialException as e:
        print(f"Failed to open port: {e}")
        sys.exit(1)
    
    # Set initial mode
    set_mode("evil")
    
    print()
    print("=" * 50)
    print("  🤖 THERAPY ROBOT - Audio Controller")
    print("=" * 50)
    print("  Voices:")
    print("    Evil mode  → Adam (deep male)")
    print("    Therapy    → Sarah (soft female)")
    print()
    print(f"  67 Emote audio: {EMOTE_67_AUDIO}")
    print()
    print("  Press Ctrl+C to exit")
    print("=" * 50)
    print()
    
    # Main loop
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                handle_line(line)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        audio_queue.put(None)
    finally:
        ser.close()
        pygame.mixer.quit()


if __name__ == "__main__":
    main()