#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

#define RST_PIN D1       // GPIO5
#define SS_PIN  D2       // GPIO4
#define BUZZER_PIN D8    // GPIO12

const char* ssid = "TESTING";
const char* password = "123456789";

const char* serverName = "http://10.17.107.53:5000/rfid_scan";

MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClient client;

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW); // Buzzer OFF at startup

  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("ESP8266 IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Ready to scan an RFID tag...");
}

void loop() {
  // Check for new RFID card presence
  if (!mfrc522.PICC_IsNewCardPresent()) {
    yield();
    return;
  }

  // Read RFID card serial number
  if (!mfrc522.PICC_ReadCardSerial()) {
    yield();
    return;
  }

  // Convert UID bytes to HEX string
  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uidString += "0";
    uidString += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidString.toUpperCase();

  Serial.print("Scanned UID: ");
  Serial.println(uidString);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, serverName);

    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    http.addHeader("X-From-Device", "true"); // Inform server it's from device

    String postData = "rfid_tag=" + uidString;
    int httpResponseCode = http.POST(postData);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.print("Response: ");
      Serial.println(response);

      DynamicJsonDocument doc(1024);
      DeserializationError error = deserializeJson(doc, response);

      if (!error) {
        String status = doc["status"];
        String message = doc["message"];

        Serial.print("Status from server: ");
        Serial.println(status);
        Serial.print("Message from server: ");
        Serial.println(message);

        if (status == "unauthorized") {
          Serial.println("⚠️ Laptop moved without permission! Sending email and buzzer ON.");
          digitalWrite(BUZZER_PIN, HIGH);
          delay(3000);  // Buzzer ON for 3 seconds
          digitalWrite(BUZZER_PIN, LOW);
        } else if (status == "unknown") {
          Serial.println("❓ Unknown tag detected. No action taken.");
          // No buzzer, no email, no DB logging
        } else {
          Serial.println("ℹ️ Unexpected status received.");
        }
      } else {
        Serial.println("❌ Failed to parse JSON response.");
      }
    } else {
      Serial.print("HTTP Error code: ");
      Serial.println(httpResponseCode);

      if (httpResponseCode == -11) {
        Serial.println("⚠️ Connection lost while sending data. Check WiFi or server status.");
      }
    }

    http.end();
  } else {
    Serial.println("❌ WiFi disconnected.");
  }

  delay(1000);  // Debounce delay to avoid rapid scanning
}
