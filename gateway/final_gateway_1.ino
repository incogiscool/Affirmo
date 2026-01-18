/*
 * ESP32 #1 - GATEWAY (with buttons)
 * 
 * Sends button commands via ESP-NOW to Robot ESP32
 * 
 * Buttons:
 *   GPIO 4  - ROAST
 *   GPIO 5  - EMOTE_67
 *   GPIO 18 - TOGGLE MODE
 *   GPIO 19 - LEFT ARM
 *   GPIO 21 - RIGHT ARM
 */

#include <WiFi.h>
#include <esp_now.h>

// Robot ESP32 MAC Address
uint8_t robotMAC[] = {0x00, 0x70, 0x07, 0x0E, 0xA1, 0x18};

// Button pins
#define BTN_ROAST     4
#define BTN_EMOTE     5
#define BTN_TOGGLE    18
#define BTN_LEFT_ARM  19
#define BTN_RIGHT_ARM 21

#define DEBOUNCE_MS 200

// Message structure
typedef struct {
    char command[245];
} Message;

Message msg;
esp_now_peer_info_t peerInfo;
unsigned long lastPress = 0;

void onDataSent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
    Serial.print("Send status: ");
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? "OK" : "FAIL");
}

void onDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
    Message *incoming = (Message *)data;
    Serial.println(incoming->command);
}

void sendCommand(const char *cmd) {
    strcpy(msg.command, cmd);
    esp_now_send(robotMAC, (uint8_t *)&msg, sizeof(msg));
    Serial.print("Sent: ");
    Serial.println(cmd);
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    pinMode(BTN_ROAST, INPUT_PULLUP);
    pinMode(BTN_EMOTE, INPUT_PULLUP);
    pinMode(BTN_TOGGLE, INPUT_PULLUP);
    pinMode(BTN_LEFT_ARM, INPUT_PULLUP);
    pinMode(BTN_RIGHT_ARM, INPUT_PULLUP);

    WiFi.mode(WIFI_STA);
    Serial.println();
    Serial.println("════════════════════════════════════════");
    Serial.println("     ESP32 GATEWAY");
    Serial.println("════════════════════════════════════════");
    Serial.print("MAC: ");
    Serial.println(WiFi.macAddress());

    if (esp_now_init() != ESP_OK) {
        Serial.println("ESP-NOW init failed!");
        return;
    }

    esp_now_register_send_cb(onDataSent);
    esp_now_register_recv_cb(onDataRecv);

    memcpy(peerInfo.peer_addr, robotMAC, 6);
    peerInfo.channel = 0;
    peerInfo.encrypt = false;

    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("Failed to add peer");
        return;
    }

    Serial.println();
    Serial.println("Buttons:");
    Serial.println("  GPIO 4  = ROAST");
    Serial.println("  GPIO 5  = EMOTE_67");
    Serial.println("  GPIO 18 = TOGGLE");
    Serial.println("  GPIO 19 = LEFT ARM");
    Serial.println("  GPIO 21 = RIGHT ARM");
    Serial.println();
    Serial.println("Ready!");
}

void loop() {
    if (millis() - lastPress < DEBOUNCE_MS) return;

    if (digitalRead(BTN_ROAST) == LOW) {
        sendCommand("ROAST");
        lastPress = millis();
    }
    if (digitalRead(BTN_EMOTE) == LOW) {
        sendCommand("EMOTE_67");
        lastPress = millis();
    }
    if (digitalRead(BTN_TOGGLE) == LOW) {
        sendCommand("TOGGLE");
        lastPress = millis();
    }
    if (digitalRead(BTN_LEFT_ARM) == LOW) {
        sendCommand("LEFT_ARM");
        lastPress = millis();
    }
    if (digitalRead(BTN_RIGHT_ARM) == LOW) {
        sendCommand("RIGHT_ARM");
        lastPress = millis();
    }
}
