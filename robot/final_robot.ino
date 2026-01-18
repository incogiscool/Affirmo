/*
 * ESP32 #2 - ROBOT
 * 
 * Receives commands via ESP-NOW from Gateway
 * Sends commands to Raspberry Pi via UART
 * Controls 2 arm servos
 * LED indicators for mode
 * 
 * Servos:
 *   GPIO 5  - Left Arm
 *   GPIO 18 - Right Arm
 * 
 * LEDs:
 *   GPIO 22 - Red (Evil mode)
 *   GPIO 23 - Green (Therapy mode)
 * 
 * UART to Pi:
 *   GPIO 17 (TX) → Pi GPIO 15 (RX)
 *   GPIO 16 (RX) ← Pi GPIO 14 (TX)
 */

#include <WiFi.h>
#include <esp_now.h>
#include <ESP32Servo.h>

// Gateway ESP32 MAC Address
uint8_t gatewayMAC[] = {0x20, 0xE7, 0xC8, 0xEC, 0xCA, 0x58};

// UART to Pi
#define PI_RX 16
#define PI_TX 17
HardwareSerial PiSerial(2);

// Servo pins
#define SERVO_LEFT  5
#define SERVO_RIGHT 18

// LED pins
#define LED_RED   22
#define LED_GREEN 23

// Servo objects
Servo leftArm;
Servo rightArm;

// Arm positions
#define ARM_DOWN 0
#define ARM_UP   90
int leftArmPos = ARM_DOWN;
int rightArmPos = ARM_DOWN;

// Current mode
bool evilMode = true;

// Message structure
typedef struct {
    char command[245];
} Message;

Message msg;
esp_now_peer_info_t peerInfo;

// Buffer for Pi responses
#define BUFFER_SIZE 500
char piBuffer[BUFFER_SIZE];
int bufferIndex = 0;

void updateLEDs() {
    if (evilMode) {
        digitalWrite(LED_RED, HIGH);
        digitalWrite(LED_GREEN, LOW);
        Serial.println("🔴 LEDs: RED (Evil mode)");
    } else {
        digitalWrite(LED_RED, LOW);
        digitalWrite(LED_GREEN, HIGH);
        Serial.println("🟢 LEDs: GREEN (Therapy mode)");
    }
}

void sendToGateway(const char *text) {
    strncpy(msg.command, text, sizeof(msg.command) - 1);
    msg.command[sizeof(msg.command) - 1] = '\0';
    esp_now_send(gatewayMAC, (uint8_t *)&msg, sizeof(msg));
    Serial.print("→ To Gateway: ");
    Serial.println(msg.command);
}

void toggleLeftArm() {
    if (leftArmPos == ARM_DOWN) {
        leftArmPos = ARM_UP;
        Serial.println("Left arm UP");
    } else {
        leftArmPos = ARM_DOWN;
        Serial.println("Left arm DOWN");
    }
    leftArm.write(leftArmPos);
}

void toggleRightArm() {
    if (rightArmPos == ARM_DOWN) {
        rightArmPos = ARM_UP;
        Serial.println("Right arm UP");
    } else {
        rightArmPos = ARM_DOWN;
        Serial.println("Right arm DOWN");
    }
    rightArm.write(rightArmPos);
}

void doEmote67() {
    Serial.println("Starting 67 emote...");
    
    for (int i = 0; i < 4; i++) {
        leftArm.write(ARM_UP);
        rightArm.write(ARM_DOWN);
        delay(300);
        
        leftArm.write(ARM_DOWN);
        rightArm.write(ARM_UP);
        delay(300);
    }
    
    leftArm.write(ARM_DOWN);
    rightArm.write(ARM_DOWN);
    leftArmPos = ARM_DOWN;
    rightArmPos = ARM_DOWN;
    
    Serial.println("67 emote done");
}

void onDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
    Message *incoming = (Message *)data;
    
    Serial.println();
    Serial.println("══════════════════════════════");
    Serial.print("FROM GATEWAY: ");
    Serial.println(incoming->command);
    Serial.println("══════════════════════════════");
    
    if (strcmp(incoming->command, "ROAST") == 0) {
        Serial.println("→ Sending ROAST to Pi...");
        PiSerial.println("ROAST");
    }
    else if (strcmp(incoming->command, "TOGGLE") == 0) {
        Serial.println("→ Sending TOGGLE to Pi...");
        PiSerial.println("TOGGLE");
        evilMode = !evilMode;
        updateLEDs();
    }
    else if (strcmp(incoming->command, "EMOTE_67") == 0) {
        doEmote67();
        sendToGateway("EMOTE 67 DONE");
    }
    else if (strcmp(incoming->command, "LEFT_ARM") == 0) {
        toggleLeftArm();
    }
    else if (strcmp(incoming->command, "RIGHT_ARM") == 0) {
        toggleRightArm();
    }
}

void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
    Serial.print("   Send status: ");
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? "OK" : "FAIL");
}

void checkPiSerial() {
    while (PiSerial.available()) {
        char c = PiSerial.read();
        
        if (c == '\n') {
            piBuffer[bufferIndex] = '\0';
            
            if (bufferIndex > 0) {
                Serial.println();
                Serial.print("← From Pi (");
                Serial.print(bufferIndex);
                Serial.println(" chars):");
                Serial.println(piBuffer);
                
                sendToGateway(piBuffer);
            }
            
            bufferIndex = 0;
        } 
        else if (c != '\r') {
            if (bufferIndex < BUFFER_SIZE - 1) {
                piBuffer[bufferIndex++] = c;
            }
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    // LEDs
    pinMode(LED_RED, OUTPUT);
    pinMode(LED_GREEN, OUTPUT);
    updateLEDs();

    // Servos
    leftArm.attach(SERVO_LEFT);
    rightArm.attach(SERVO_RIGHT);
    leftArm.write(ARM_DOWN);
    rightArm.write(ARM_DOWN);

    // Buffer
    memset(piBuffer, 0, BUFFER_SIZE);

    // UART to Pi
    PiSerial.begin(115200, SERIAL_8N1, PI_RX, PI_TX);

    // WiFi
    WiFi.mode(WIFI_STA);
    Serial.println();
    Serial.println("══════════════════════════════");
    Serial.println("     ESP32 ROBOT");
    Serial.println("══════════════════════════════");
    Serial.print("MAC: ");
    Serial.println(WiFi.macAddress());

    // ESP-NOW
    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW init failed!");
        return;
    }

    esp_now_register_recv_cb(onDataRecv);
    esp_now_register_send_cb(onDataSent);

    memcpy(peerInfo.peer_addr, gatewayMAC, 6);
    peerInfo.channel = 0;
    peerInfo.encrypt = false;

    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("Failed to add peer");
        return;
    }

    Serial.println();
    Serial.println("Servos: LEFT=GPIO5, RIGHT=GPIO18");
    Serial.println("LEDs: RED=GPIO22, GREEN=GPIO23");
    Serial.println("Pi UART: RX=GPIO16, TX=GPIO17");
    Serial.println();
    Serial.println("Ready!");
}

void loop() {
    checkPiSerial();
    delay(10);
}
