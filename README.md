**NOTE (18/01/26, 9:39 AM) The Affirmo python code is DONE, but I will upload once we get to the venue around 10-11 AM since I cant set it up at home**


## Technical Stuff

We started by experimenting with **QNX** (a real-time operating system) before pivoting to a **Raspberry Pi 4 OS** setup for faster development. Sometimes you have to sacrifice elegance for velocity.

### System Architecture

Our architecture uses a distributed system of microcontrollers communicating through multiple protocols:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AFFIRMO ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐                                     ┌─────────────┐
    │   REMOTE    │          ESP-NOW (Wireless)         │    ROBOT    │
    │   ESP32     │ ◄─────────────────────────────────► │    ESP32    │
    │             │         2.4GHz, ~200m range         │             │
    └─────────────┘                                     └─────────────┘
          │                                                   │
          │ Buttons (GPIO 4, 5, 18, 19, 21)                   │ UART (GPIO 16/17)
          │   • ROAST                                         │
          │   • TOGGLE MODE                                   │
          │   • EMOTE 67                                      ▼
          │   • LEFT ARM                              ┌─────────────┐
          │   • RIGHT ARM                             │ RASPBERRY   │
          │                                           │   PI 4      │
          │                                           │             │
          │                                           │ • Camera V3 │
          │                                           │ • WiFi      │
          │                                           │ • Python    │
          │                                           └─────────────┘
          │                                                  │
          │                                                  │ HTTPS
          │                                                  ▼
          │                                           ┌─────────────┐
          │           USB Serial                      │  OPENROUTER │
          ▼           Connection                      │   (Grok)    │
    ┌─────────────┐ ◄──────────────────────────────── └─────────────┘
    │   LAPTOP    │
    │             │ ────────────────────────────────► ┌─────────────┐
    │ • Python    │           HTTPS                   │ ELEVENLABS  │
    │ • Pygame    │                                   │    TTS      │
    └─────────────┘                                   └─────────────┘
          │
          │ Audio Output
          ▼
    ┌─────────────┐
    │   SPEAKER   │
    │   🔊        │
    └─────────────┘
```

### Hardware Components

| Component         | Model                   | Purpose                                   |
| ----------------- | ----------------------- | ----------------------------------------- |
| Remote Controller | ESP32 WROOM             | Button inputs, wireless transmission      |
| Robot Controller  | ESP32 WROOM             | Servo control, UART relay, LED indicators |
| Brain             | Raspberry Pi 4          | Camera capture, API orchestration         |
| Camera            | Pi Camera V3            | Image capture for AI analysis             |
| Arm Servos        | 2× SG90                 | Left and right arm movement               |
| Mode LEDs         | Red + Green             | Visual mode indication                    |
| Power             | 2× 9V + Buck Converters | 5V regulated power for servos             |

### Communication Protocols

**ESP-NOW** (Between ESP32s)

- Connectionless, peer-to-peer protocol
- Low latency (~1-2ms)
- No WiFi router required
- 250-byte max payload

**UART** (ESP32 ↔ Raspberry Pi)

- 115200 baud rate
- GPIO 17 (TX) → Pi GPIO 15 (RX)
- GPIO 16 (RX) ← Pi GPIO 14 (TX)
- Common ground connection

### Software Stack

The **Raspberry Pi** handles the intelligence — face detection, WiFi communication, and API orchestration. We programmed it in **Python**, leveraging:

- **Picamera2** for camera control
- **Requests** for API communication
- **PySerial** for UART communication

The **laptop** runs a Python script using **Pygame** for audio playback and handles the **ElevenLabs API** integration for text-to-speech with dynamic voice switching:

- **Adam** (deep male voice) for Evil Mode 🔴
- **Sarah** (soft female voice) for Therapy Mode 🟢

### Mechanical Design

We built Affirmo's body from **cardboard**, iterating through several designs to balance stability and expressiveness. The servo motors mount directly to the body with hot glue, with the servo horns attached to the cardboard arms.

```
           ┌─────┐
           │  📷 │  ← Pi Camera (face)
           └──┬──┘
    ══════════╪══════════  ← Arms (cardboard)
         █    │    █
        ┌┴┐   │   ┌┴┐      ← SG90 Servos
        └─┘   │   └─┘
          🔴  │  🟢        ← Mode LEDs
              │
           ───┴───         ← Body (cardboard)
```
