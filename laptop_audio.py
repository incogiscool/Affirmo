#!/usr/bin/env python3
"""
Therapy Robot - Laptop Audio Controller

Reads responses from ESP32 Gateway via Serial
Converts text to speech and plays it

Install dependencies:
  pip install pyserial pyttsx3

Run:
  python3 laptop_audio.py
"""

import serial
import serial.tools.list_ports
import pyttsx3
import threading
import queue
import sys
import time

# ==================== CONFIGURATION ====================

BAUD_RATE = 115200

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


# ==================== TEXT TO SPEECH ====================

speech_queue = queue.Queue()
tts_thread = None

def tts_worker():
    """Background thread that handles TTS"""
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    
    while True:
        try:
            text = speech_queue.get(timeout=1)
            if text is None:  # Shutdown signal
                break
            print(f"\n🔊 Speaking: {text}\n")
            engine.say(text)
            engine.runAndWait()
            speech_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"TTS Error: {e}")


def init_tts():
    global tts_thread
    print("Initializing text-to-speech...")
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()
    print("TTS ready!")


def speak(text):
    """Queue text for speech (non-blocking)"""
    speech_queue.put(text)


# ==================== SERIAL HANDLING ====================

def is_garbage(line):
    """Filter out non-response lines"""
    skip_patterns = [
        "════",
        "═══",
        "Sent:",
        "Send status:",
        "RESPONSE FROM ROBOT:",
        "FROM GATEWAY:",
        "To Gateway:",
        "Ready!",
        "Press buttons",
        "GPIO",
        "ESP32",
        "MAC:",
        "ESP-NOW",
        "peer",
        "Waiting",
    ]
    
    for pattern in skip_patterns:
        if pattern in line:
            return True
    
    return False


def handle_line(line):
    """Process incoming serial data"""
    line = line.strip()
    
    if not line:
        return
    
    # Skip garbage lines
    if is_garbage(line):
        print(f"   [skip] {line[:50]}...")
        return
    
    print(f"📥 {line}")
    
    # Mode change
    if line.startswith("MODE:") or line.startswith("Mode:"):
        mode = line.split(":")[1].strip()
        speak(f"Switched to {mode} mode")
        return
    
    # Status messages
    if "DONE" in line:
        speak(line.replace("_", " "))
        return
    
    # AI response - anything longer than 15 chars that isn't filtered
    if len(line) > 15:
        speak(line)


# ==================== MAIN ====================

def main():
    # Find ESP32 port
    port = find_esp32_port()
    
    if not port and len(sys.argv) < 2:
        print()
        print("ESP32 not found. Specify port manually:")
        print("  python3 laptop_audio.py /dev/cu.usbserial-0001")
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
    
    print()
    print("=" * 50)
    print("  🤖 THERAPY ROBOT - Laptop Audio")
    print("=" * 50)
    print("  Listening for responses...")
    print("  Press Ctrl+C to exit")
    print("=" * 50)
    print()
    
    speak("Robot audio ready")
    
    # Main loop
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                handle_line(line)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nShutting down...")
        speech_queue.put(None)  # Signal TTS thread to stop
    finally:
        ser.close()


if __name__ == "__main__":
    main()