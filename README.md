# What It Does

**Wi-Fi Scanning:** The ESP32 scans for available Wi-Fi networks and records the SSID and RSSI (signal strength).

**GPS Tracking:** The GPS module provides latitude and longitude information during scanning, which is logged along with the Wi-Fi network data.

**SD Card Logging:** The data (SSID, RSSI, and GPS coordinates) is logged into a file on the SD card (/wifi_log.txt).

**OLED Display:** Displays the SSID, RSSI, and GPS coordinates for each scanned network on the OLED.

## What It Looks Like (for now)

[front](https://github.com/megaBC333/GPSniffer/blob/main/front.jpg)

[back](https://github.com/megaBC333/GPSniffer/blob/main/back.jpg)

## Code

```
#include <WiFi.h>
#include <TinyGPS++.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <SPI.h>
#include <SD.h>

// GPS settings
TinyGPSPlus gps;
HardwareSerial ss(1);

// OLED display settings
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// SD card settings
#define SD_CS 5

void setup() {
  // Serial setup
  Serial.begin(115200);
  ss.begin(9600, SERIAL_8N1, 16, 17);  // RX, TX for GPS

  // OLED initialization
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    for (;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("Starting WiFi + GPS Logging");
  display.display();
  delay(2000);

  // SD card initialization
  if (!SD.begin(SD_CS)) {
    Serial.println("SD card initialization failed!");
    display.clearDisplay();
    display.setCursor(0, 0);
    display.print("SD init failed");
    display.display();
    return;
  }
  Serial.println("SD card initialized.");

  // WiFi setup (not connected, just scanning)
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
}

void loop() {
  // GPS processing
  while (ss.available() > 0) {
    gps.encode(ss.read());
  }

  double latitude = gps.location.isValid() ? gps.location.lat() : 0.0;
  double longitude = gps.location.isValid() ? gps.location.lng() : 0.0;

  // Wi-Fi scanning
  int n = WiFi.scanNetworks();
  Serial.println("Scan complete");

  // OLED display update
  display.clearDisplay();
  display.setCursor(0, 0);

  for (int i = 0; i < n && i < 3; ++i) {  // Show max 3 networks on OLED
    display.print(WiFi.SSID(i));
    display.print(" (");
    display.print(WiFi.RSSI(i));
    display.print(")");
    display.println();
  }

  display.print("Lat: ");
  display.println(latitude, 6);
  display.print("Long: ");
  display.println(longitude, 6);
  display.display();

  // SD card logging
  File dataFile = SD.open("/log.txt", FILE_APPEND);
  if (dataFile) {
    Serial.println("Logging data...");  // Debug message to track when writing starts

    for (int i = 0; i < n; ++i) {  // Log all networks to SD card
      dataFile.print("SSID: ");
      dataFile.print(WiFi.SSID(i));
      dataFile.print(" | RSSI: ");
      dataFile.println(WiFi.RSSI(i));
      dataFile.print(" | GPS Latitude: ");
      dataFile.println(latitude, 6);
      dataFile.print(" | GPS Longitude: ");
      dataFile.println(longitude, 6);
      dataFile.println("-------------------");
    }
    dataFile.close();  // Close the file after writing
    Serial.println("Data logged successfully.");  // Confirm logging completion

    delay(100);  // Short delay to allow file writing to complete
  } else {
    Serial.println("Error opening file for writing.");
  }

  delay(5000);  // Wait 5 seconds before next scan
}
