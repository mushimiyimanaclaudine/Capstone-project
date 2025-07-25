#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

#define RST_PIN D3    // Reset pin for RC522
#define SS_PIN  D4    // Slave select pin for RC522
#define BUZZER_PIN D2 // Buzzer pin

MFRC522 mfrc522(SS_PIN, RST_PIN);

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const String serverUrl = "http://YOUR_SERVER_IP:YOUR_PORT/api/rfid_event";  // Flask/Python server endpoint

// Example of authorized RFID tag UIDs
String authorizedUIDs[] = {
  "DE 3A 59 D2",  // Laptop 1
  "E3 9A 12 4F"   // Laptop 2
};

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected.");
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  String tagUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    tagUID += String(mfrc522.uid.uidByte[i], HEX);
    if (i < mfrc522.uid.size - 1) tagUID += " ";
  }

  tagUID.toUpperCase();
  Serial.println("Tag Scanned: " + tagUID);

  bool authorized = false;
  for (String uid : authorizedUIDs) {
    if (uid == tagUID) {
      authorized = true;
      break;
    }
  }

  if (authorized) {
    Serial.println("Access granted.");
    digitalWrite(BUZZER_PIN, LOW);
  } else {
    Serial.println("Unauthorized tag detected!");
    digitalWrite(BUZZER_PIN, HIGH);
    delay(1000);
    digitalWrite(BUZZER_PIN, LOW);
    sendToServer(tagUID);
  }

  delay(2000);
  mfrc522.PICC_HaltA();
}

void sendToServer(String uid) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    http.begin(client, serverUrl);  // ✅ Updated API usage
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{\"uid\": \"" + uid + "\"}";
    int httpCode = http.POST(jsonData);

    if (httpCode > 0) {
      Serial.printf("Data sent to server. HTTP response code: %d\n", httpCode);
    } else {
      Serial.printf("Failed to send data. Error: %s\n", http.errorToString(httpCode).c_str());
    }

    http.end();
  } else {
    Serial.println("WiFi not connected.");
  }
}

