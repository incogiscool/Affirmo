# # #!/usr/bin/env python3
# # """
# # Therapy Robot - Laptop Audio Controller (ElevenLabs)

# # Reads responses from ESP32 Gateway via Serial
# # Converts text to speech using ElevenLabs API

# # Install dependencies:
# #   pip install pyserial requests pygame

# # Set your API key:
# #   export ELEVENLABS_API_KEY="your-key-here"

# # Run:
# #   python3 laptop_elevenlabs.py
# # """

# # import serial
# # import serial.tools.list_ports
# # import requests
# # import pygame
# # import threading
# # import queue
# # import sys
# # import time
# # import os
# # import tempfile

# # # ==================== CONFIGURATION ====================

# # BAUD_RATE = 115200

# # ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_e91311b22ee997b19e3a10c7506fee71c29f19cab35d5c7e")

# # # Voice IDs - pick one or get your own from ElevenLabs
# # # https://api.elevenlabs.io/v1/voices
# # VOICES = {
# #     "rachel": "21m00Tcm4TlvDq8ikWAM",      # Female, calm
# #     "drew": "29vD33N1CtxCmqQRPOHJ",        # Male, well-rounded
# #     "clyde": "2EiwWnXFnvU5JabPnv8n",       # Male, war veteran
# #     "paul": "5Q0t7uMcjvnagumLfvZi",        # Male, ground reporter  
# #     "domi": "AZnzlk1XvdvUeBnXmlld",        # Female, strong
# #     "dave": "CYw3kZ02Hs0563khs1Fj",        # Male, conversational
# #     "fin": "D38z5RcWu1voky8WS1ja",         # Male, sailor
# #     "sarah": "EXAVITQu4vr4xnSDxMaL",       # Female, soft
# #     "antoni": "ErXwobaYiN019PkySvjV",      # Male, well-rounded
# #     "thomas": "GBv7mTt0atIp3Br8iCZE",      # Male, calm
# #     "charlie": "IKne3meq5aSn9XLyUdCD",     # Male, casual
# #     "emily": "LcfcDJNUP1GQjkzn1xUU",       # Female, calm
# #     "adam": "pNInz6obpgDQGcFmaJgB",        # Male, deep
# #     "sam": "yoZ06aMxZJJ28mfd3POQ",         # Male, raspy
# # }

# # # Choose your voice
# # VOICE_ID = VOICES["adam"]  # Deep male voice - good for roasts

# # # Voice settings
# # STABILITY = 0.5         # 0-1, lower = more expressive
# # SIMILARITY_BOOST = 0.75 # 0-1, higher = closer to original voice

# # # ==================== FIND ESP32 ====================

# # def find_esp32_port():
# #     """Auto-detect ESP32 serial port"""
# #     ports = serial.tools.list_ports.comports()
    
# #     print("Scanning for ESP32...")
    
# #     for port in ports:
# #         desc = port.description.lower()
# #         if any(x in desc for x in ["cp210", "ch340", "usb", "serial", "uart"]):
# #             print(f"  Found: {port.device} - {port.description}")
# #             return port.device
    
# #     print("Available ports:")
# #     for port in ports:
# #         print(f"  {port.device}: {port.description}")
    
# #     return None


# # # ==================== ELEVENLABS TTS ====================

# # speech_queue = queue.Queue()
# # tts_thread = None

# # def text_to_speech_elevenlabs(text):
# #     """Convert text to speech using ElevenLabs API"""
    
# #     url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
# #     headers = {
# #         "Accept": "audio/mpeg",
# #         "Content-Type": "application/json",
# #         "xi-api-key": ELEVENLABS_API_KEY
# #     }
    
# #     data = {
# #         "text": text,
# #         "model_id": "eleven_monolingual_v1",
# #         "voice_settings": {
# #             "stability": STABILITY,
# #             "similarity_boost": SIMILARITY_BOOST
# #         }
# #     }
    
# #     try:
# #         response = requests.post(url, json=data, headers=headers, timeout=30)
        
# #         if response.status_code != 200:
# #             print(f"ElevenLabs Error: {response.status_code}")
# #             print(response.text)
# #             return None
        
# #         return response.content
    
# #     except Exception as e:
# #         print(f"ElevenLabs Error: {e}")
# #         return None


# # def play_audio(audio_data):
# #     """Play audio data using pygame"""
    
# #     # Save to temp file
# #     with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
# #         f.write(audio_data)
# #         temp_path = f.name
    
# #     try:
# #         pygame.mixer.music.load(temp_path)
# #         pygame.mixer.music.play()
        
# #         # Wait for audio to finish
# #         while pygame.mixer.music.get_busy():
# #             time.sleep(0.1)
# #     finally:
# #         # Clean up temp file
# #         os.unlink(temp_path)


# # def tts_worker():
# #     """Background thread that handles TTS"""
    
# #     pygame.mixer.init()
    
# #     while True:
# #         try:
# #             text = speech_queue.get(timeout=1)
# #             if text is None:  # Shutdown signal
# #                 break
            
# #             print(f"\n🔊 Speaking: {text}\n")
            
# #             audio_data = text_to_speech_elevenlabs(text)
# #             if audio_data:
# #                 play_audio(audio_data)
# #             else:
# #                 print("   Failed to generate audio")
            
# #             speech_queue.task_done()
        
# #         except queue.Empty:
# #             continue
# #         except Exception as e:
# #             print(f"TTS Error: {e}")


# # def init_tts():
# #     global tts_thread
# #     print("Initializing ElevenLabs TTS...")
# #     tts_thread = threading.Thread(target=tts_worker, daemon=True)
# #     tts_thread.start()
# #     print("TTS ready!")


# # def speak(text):
# #     """Queue text for speech (non-blocking)"""
# #     speech_queue.put(text)


# # # ==================== SERIAL HANDLING ====================

# # def is_garbage(line):
# #     """Filter out non-response lines"""
# #     skip_patterns = [
# #         "════", "═══", "Sent:", "Send status:",
# #         "RESPONSE FROM ROBOT:", "FROM GATEWAY:",
# #         "To Gateway:", "Ready!", "Press buttons",
# #         "GPIO", "ESP32", "MAC:", "ESP-NOW",
# #         "peer", "Waiting",
# #     ]
    
# #     for pattern in skip_patterns:
# #         if pattern in line:
# #             return True
# #     return False


# # def handle_line(line):
# #     """Process incoming serial data"""
# #     line = line.strip()
    
# #     if not line:
# #         return
    
# #     if is_garbage(line):
# #         print(f"   [skip] {line[:50]}...")
# #         return
    
# #     print(f"📥 {line}")
    
# #     # Mode change
# #     if line.startswith("MODE:") or line.startswith("Mode:"):
# #         mode = line.split(":")[1].strip()
# #         speak(f"Switched to {mode} mode")
# #         return
    
# #     # Status messages
# #     if "DONE" in line:
# #         speak(line.replace("_", " "))
# #         return
    
# #     # AI response
# #     if len(line) > 15:
# #         speak(line)


# # # ==================== MAIN ====================

# # def main():
# #     # Check API key
# #     if ELEVENLABS_API_KEY == "your-key-here":
# #         print()
# #         print("=" * 50)
# #         print("ERROR: Set your ElevenLabs API key!")
# #         print()
# #         print("  export ELEVENLABS_API_KEY='your-key-here'")
# #         print()
# #         print("Get your key at: https://elevenlabs.io")
# #         print("=" * 50)
# #         sys.exit(1)
    
# #     # Find ESP32 port
# #     port = find_esp32_port()
    
# #     if not port and len(sys.argv) < 2:
# #         print()
# #         print("ESP32 not found. Specify port manually:")
# #         print("  python3 laptop_elevenlabs.py /dev/cu.usbserial-0001")
# #         sys.exit(1)
    
# #     if len(sys.argv) > 1:
# #         port = sys.argv[1]
    
# #     # Init TTS
# #     init_tts()
    
# #     # Open serial port
# #     print(f"Connecting to {port}...")
# #     try:
# #         ser = serial.Serial(port, BAUD_RATE, timeout=0.5)
# #         time.sleep(2)
# #     except serial.SerialException as e:
# #         print(f"Failed to open port: {e}")
# #         sys.exit(1)
    
# #     print()
# #     print("=" * 50)
# #     print("  🤖 THERAPY ROBOT - ElevenLabs Audio")
# #     print("=" * 50)
# #     print(f"  Voice: {VOICE_ID}")
# #     print("  Listening for responses...")
# #     print("  Press Ctrl+C to exit")
# #     print("=" * 50)
# #     print()
    
# #     speak("Robot audio ready")
    
# #     # Main loop
# #     try:
# #         while True:
# #             if ser.in_waiting > 0:
# #                 line = ser.readline().decode('utf-8', errors='ignore')
# #                 handle_line(line)
# #             time.sleep(0.01)
    
# #     except KeyboardInterrupt:
# #         print("\nShutting down...")
# #         speech_queue.put(None)
# #     finally:
# #         ser.close()
# #         pygame.mixer.quit()


# # if __name__ == "__main__":
# #     main()

# #!/usr/bin/env python3
# """
# Therapy Robot - Laptop Audio Controller (ElevenLabs)

# Reads responses from ESP32 Gateway via Serial
# Converts text to speech using ElevenLabs API

# Voice changes based on mode:
#   - Evil mode: Adam (deep male)
#   - Therapy mode: Sarah (soft female)

# Install dependencies:
#   pip install pyserial requests pygame

# Set your API key:
#   export ELEVENLABS_API_KEY="your-key-here"

# Run:
#   python3 laptop_elevenlabs.py
# """

# import serial
# import serial.tools.list_ports
# import requests
# import pygame
# import threading
# import queue
# import sys
# import time
# import os
# import tempfile

# # ==================== CONFIGURATION ====================

# BAUD_RATE = 115200

# ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "sk_e91311b22ee997b19e3a10c7506fee71c29f19cab35d5c7e")

# # Voice IDs
# VOICES = {
#     "adam": "pNInz6obpgDQGcFmaJgB",        # Male, deep - for evil/roast
#     "sarah": "EXAVITQu4vr4xnSDxMaL",       # Female, soft - for therapy
# }

# # Current mode and voice
# current_mode = "evil"  # Start in evil mode (matches Pi default)
# current_voice = VOICES["adam"]

# # Voice settings
# STABILITY = 0.5
# SIMILARITY_BOOST = 0.75

# # ==================== FIND ESP32 ====================

# def find_esp32_port():
#     """Auto-detect ESP32 serial port"""
#     ports = serial.tools.list_ports.comports()
    
#     print("Scanning for ESP32...")
    
#     for port in ports:
#         desc = port.description.lower()
#         if any(x in desc for x in ["cp210", "ch340", "usb", "serial", "uart"]):
#             print(f"  Found: {port.device} - {port.description}")
#             return port.device
    
#     print("Available ports:")
#     for port in ports:
#         print(f"  {port.device}: {port.description}")
    
#     return None


# # ==================== ELEVENLABS TTS ====================

# speech_queue = queue.Queue()
# tts_thread = None

# def text_to_speech_elevenlabs(text, voice_id):
#     """Convert text to speech using ElevenLabs API"""
    
#     url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
#     headers = {
#         "Accept": "audio/mpeg",
#         "Content-Type": "application/json",
#         "xi-api-key": ELEVENLABS_API_KEY
#     }
    
#     data = {
#         "text": text,
#         "model_id": "eleven_monolingual_v1",
#         "voice_settings": {
#             "stability": STABILITY,
#             "similarity_boost": SIMILARITY_BOOST
#         }
#     }
    
#     try:
#         response = requests.post(url, json=data, headers=headers, timeout=30)
        
#         if response.status_code != 200:
#             print(f"ElevenLabs Error: {response.status_code}")
#             print(response.text)
#             return None
        
#         return response.content
    
#     except Exception as e:
#         print(f"ElevenLabs Error: {e}")
#         return None


# def play_audio(audio_data):
#     """Play audio data using pygame"""
    
#     with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
#         f.write(audio_data)
#         temp_path = f.name
    
#     try:
#         pygame.mixer.music.load(temp_path)
#         pygame.mixer.music.play()
        
#         while pygame.mixer.music.get_busy():
#             time.sleep(0.1)
#     finally:
#         os.unlink(temp_path)


# def tts_worker():
#     """Background thread that handles TTS"""
    
#     pygame.mixer.init()
    
#     while True:
#         try:
#             item = speech_queue.get(timeout=1)
#             if item is None:
#                 break
            
#             text, voice_id = item
            
#             voice_name = "Adam" if voice_id == VOICES["adam"] else "Sarah"
#             print(f"\n🔊 [{voice_name}]: {text}\n")
            
#             audio_data = text_to_speech_elevenlabs(text, voice_id)
#             if audio_data:
#                 play_audio(audio_data)
#             else:
#                 print("   Failed to generate audio")
            
#             speech_queue.task_done()
        
#         except queue.Empty:
#             continue
#         except Exception as e:
#             print(f"TTS Error: {e}")


# def init_tts():
#     global tts_thread
#     print("Initializing ElevenLabs TTS...")
#     tts_thread = threading.Thread(target=tts_worker, daemon=True)
#     tts_thread.start()
#     print("TTS ready!")


# def speak(text):
#     """Queue text for speech with current voice"""
#     speech_queue.put((text, current_voice))


# # ==================== MODE SWITCHING ====================

# def set_mode(mode):
#     """Switch mode and voice"""
#     global current_mode, current_voice
    
#     mode = mode.lower()
    
#     if mode == "evil":
#         current_mode = "evil"
#         current_voice = VOICES["adam"]
#         print("🔴 Mode: EVIL (Voice: Adam)")
#     elif mode == "therapy":
#         current_mode = "therapy"
#         current_voice = VOICES["sarah"]
#         print("🟢 Mode: THERAPY (Voice: Sarah)")


# # ==================== SERIAL HANDLING ====================

# def is_garbage(line):
#     """Filter out non-response lines"""
#     skip_patterns = [
#         "════", "═══", "Sent:", "Send status:",
#         "RESPONSE FROM ROBOT:", "FROM GATEWAY:",
#         "To Gateway:", "Ready!", "Press buttons",
#         "GPIO", "ESP32", "MAC:", "ESP-NOW",
#         "peer", "Waiting",
#     ]
    
#     for pattern in skip_patterns:
#         if pattern in line:
#             return True
#     return False


# def handle_line(line):
#     """Process incoming serial data"""
#     line = line.strip()
    
#     if not line:
#         return
    
#     if is_garbage(line):
#         print(f"   [skip] {line[:50]}...")
#         return
    
#     print(f"📥 {line}")
    
#     # Mode change
#     if line.startswith("MODE:") or line.startswith("Mode:"):
#         mode = line.split(":")[1].strip().lower()
#         set_mode(mode)
#         speak(f"Switched to {mode} mode")
#         return
    
#     # Status messages
#     if "DONE" in line:
#         speak(line.replace("_", " "))
#         return
    
#     # AI response
#     if len(line) > 15:
#         speak(line)


# # ==================== MAIN ====================

# def main():
#     global current_mode, current_voice
    
#     # Check API key
#     if ELEVENLABS_API_KEY == "your-key-here":
#         print()
#         print("=" * 50)
#         print("ERROR: Set your ElevenLabs API key!")
#         print()
#         print("  export ELEVENLABS_API_KEY='your-key-here'")
#         print()
#         print("Get your key at: https://elevenlabs.io")
#         print("=" * 50)
#         sys.exit(1)
    
#     # Find ESP32 port
#     port = find_esp32_port()
    
#     if not port and len(sys.argv) < 2:
#         print()
#         print("ESP32 not found. Specify port manually:")
#         print("  python3 laptop_elevenlabs.py /dev/cu.usbserial-0001")
#         sys.exit(1)
    
#     if len(sys.argv) > 1:
#         port = sys.argv[1]
    
#     # Init TTS
#     init_tts()
    
#     # Open serial port
#     print(f"Connecting to {port}...")
#     try:
#         ser = serial.Serial(port, BAUD_RATE, timeout=0.5)
#         time.sleep(2)
#     except serial.SerialException as e:
#         print(f"Failed to open port: {e}")
#         sys.exit(1)
    
#     # Set initial mode
#     set_mode("evil")
    
#     print()
#     print("=" * 50)
#     print("  🤖 THERAPY ROBOT - ElevenLabs Audio")
#     print("=" * 50)
#     print("  Voices:")
#     print("    Evil mode  → Adam (deep male)")
#     print("    Therapy    → Sarah (soft female)")
#     print()
#     print("  Listening for responses...")
#     print("  Press Ctrl+C to exit")
#     print("=" * 50)
#     print()
    
#     speak("Robot audio ready")
    
#     # Main loop
#     try:
#         while True:
#             if ser.in_waiting > 0:
#                 line = ser.readline().decode('utf-8', errors='ignore')
#                 handle_line(line)
#             time.sleep(0.01)
    
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#         speech_queue.put(None)
#     finally:
#         ser.close()
#         pygame.mixer.quit()


# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
Therapy Robot - Laptop Audio Controller (ElevenLabs)

Reads responses from ESP32 Gateway via Serial
ONLY speaks AI-generated responses (roasts/therapy)

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

# Voice IDs
VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",        # Male, deep - for evil/roast
    "sarah": "EXAVITQu4vr4xnSDxMaL",       # Female, soft - for therapy
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


# ==================== ELEVENLABS TTS ====================

speech_queue = queue.Queue()
tts_thread = None

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


def play_audio(audio_data):
    """Play audio data using pygame"""
    
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


def tts_worker():
    """Background thread that handles TTS"""
    
    pygame.mixer.init()
    
    while True:
        try:
            item = speech_queue.get(timeout=1)
            if item is None:
                break
            
            text, voice_id = item
            
            voice_name = "Adam" if voice_id == VOICES["adam"] else "Sarah"
            print(f"\n🔊 [{voice_name}]: {text}\n")
            
            audio_data = text_to_speech_elevenlabs(text, voice_id)
            if audio_data:
                play_audio(audio_data)
            else:
                print("   Failed to generate audio")
            
            speech_queue.task_done()
        
        except queue.Empty:
            continue
        except Exception as e:
            print(f"TTS Error: {e}")


def init_tts():
    global tts_thread
    print("Initializing ElevenLabs TTS...")
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    print("TTS ready!")


def speak(text):
    """Queue text for speech with current voice"""
    speech_queue.put((text, current_voice))


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
    
    # Skip short lines
    if len(line) < 20:
        return False
    
    # Skip known system messages
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
    
    # Likely an AI response
    return True


def handle_line(line):
    """Process incoming serial data"""
    line = line.strip()
    
    if not line:
        return
    
    print(f"📥 {line}")
    
    # Mode change - update voice but don't speak
    if line.startswith("MODE:") or line.startswith("Mode:"):
        mode = line.split(":")[1].strip().lower()
        set_mode(mode)
        return
    
    # Only speak AI responses
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
    
    # Find ESP32 port
    port = find_esp32_port()
    
    if not port and len(sys.argv) < 2:
        print()
        print("ESP32 not found. Specify port manually:")
        print("  python3 laptop_elevenlabs.py /dev/cu.usbserial-0001")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    # Init TTS
    init_tts()
    
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
    print("  🤖 THERAPY ROBOT - ElevenLabs Audio")
    print("=" * 50)
    print("  Voices:")
    print("    Evil mode  → Adam (deep male)")
    print("    Therapy    → Sarah (soft female)")
    print()
    print("  Only speaks AI responses")
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
        speech_queue.put(None)
    finally:
        ser.close()
        pygame.mixer.quit()


if __name__ == "__main__":
    main()