"""
Therapy Robot - Raspberry Pi Controller

Listens for commands from ESP32 via UART:
  - ROAST: Take photo, send to AI, return response
  - TOGGLE: Switch between Evil and Therapy mode

Sends responses back to ESP32 via UART
"""

import base64
import requests
import serial
import time
import os

# ==================== CONFIGURATION ====================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your-api-key-here")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3.5-sonnet"

# UART config
SERIAL_PORT = "/dev/serial0"  # Default Pi UART
BAUD_RATE = 115200

# ==================== MODES ====================

MODE_THERAPY = "therapy"
MODE_EVIL = "evil"

current_mode = MODE_THERAPY

PROMPTS = {
    MODE_THERAPY: """You are a warm, caring therapy robot assistant. 
When shown an image of a person, provide gentle reassurance and supportive observations.
Keep responses concise (2-3 sentences), warm, and encouraging.
Focus on being present and supportive.""",

    MODE_EVIL: """You are a savage roast bot with no filter.
When shown an image of a person, deliver a brutal but funny roast.
Keep it to 2-3 sentences. Be creative and ruthless but avoid anything 
truly hurtful about things people can't change.
Think comedy roast, not actual cruelty."""
}

# ==================== CAMERA ====================

camera = None

def init_camera():
    global camera
    from picamera2 import Picamera2
    
    print("Initializing camera...")
    camera = Picamera2()
    config = camera.create_still_configuration(
        main={"size": (640, 480)}
    )
    camera.configure(config)
    camera.start()
    time.sleep(1)
    print("Camera ready!")


def capture_image():
    """Capture image and return as base64"""
    filename = "/tmp/capture.jpg"
    camera.capture_file(filename)
    
    with open(filename, "rb") as f:
        image_base64 = base64.standard_b64encode(f.read()).decode("utf-8")
    
    os.remove(filename)
    print("Photo captured!")
    return image_base64


# ==================== AI ====================

def get_ai_response(image_base64):
    """Send image to OpenRouter and get response"""
    global current_mode
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://therapy-robot.local",
        "X-Title": "Therapy Robot"
    }
    
    prompt_text = "What do you see? " + (
        "Please offer some gentle reassurance." if current_mode == MODE_THERAPY
        else "Roast this person."
    )
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": PROMPTS[current_mode]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }
        ],
        "max_tokens": 150
    }
    
    try:
        print(f"Sending to AI (mode: {current_mode})...")
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            print(response.text)
            return "I'm having trouble thinking right now."
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    except Exception as e:
        print(f"Error: {e}")
        return "Something went wrong with my brain."


# ==================== COMMAND HANDLING ====================

def handle_command(cmd, ser):
    global current_mode
    
    cmd = cmd.strip().upper()
    print(f"\n>>> Command received: {cmd}")
    
    if cmd == "ROAST":
        # Take photo and get AI response
        print("Taking photo...")
        image_base64 = capture_image()
        
        print("Getting AI response...")
        response = get_ai_response(image_base64)
        
        print(f"AI says: {response}")
        
        # Send response back to ESP32
        ser.write(f"{response}\n".encode())
        print("Response sent to ESP32")
        
    elif cmd == "TOGGLE":
        # Switch modes
        if current_mode == MODE_THERAPY:
            current_mode = MODE_EVIL
        else:
            current_mode = MODE_THERAPY
        
        print(f"Mode switched to: {current_mode.upper()}")
        ser.write(f"MODE:{current_mode}\n".encode())
    
    else:
        print(f"Unknown command: {cmd}")


# ==================== MAIN ====================

def main():
    # Check API key
    if OPENROUTER_API_KEY == "your-api-key-here":
        print("=" * 50)
        print("ERROR: Set your OpenRouter API key!")
        print("  export OPENROUTER_API_KEY='your-key'")
        print("=" * 50)
        return
    
    # Initialize camera
    init_camera()
    
    # Open serial port
    print(f"Opening serial port {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    except Exception as e:
        print(f"Failed to open serial: {e}")
        print("Try: sudo raspi-config → Interface Options → Serial Port")
        print("  - Login shell over serial: NO")
        print("  - Serial port hardware: YES")
        return
    
    print("Serial ready!")
    
    print()
    print("=" * 50)
    print("  THERAPY ROBOT - Pi Controller")
    print("=" * 50)
    print(f"  Mode: {current_mode.upper()}")
    print("  Waiting for commands from ESP32...")
    print("=" * 50)
    print()
    
    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                if line.strip():
                    handle_command(line, ser)
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        ser.close()
        if camera:
            camera.stop()
            camera.close()


if __name__ == "__main__":
    main()