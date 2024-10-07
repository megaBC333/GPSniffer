# What It Does

**Wi-Fi Scanning:** The ESP32 scans for available Wi-Fi networks and records the SSID and RSSI (signal strength).

**GPS Tracking:** The GPS module provides latitude and longitude information during scanning, which is logged along with the Wi-Fi network data.

**SD Card Logging:** The data (SSID, RSSI, and GPS coordinates) is logged into a file on the SD card (/wifi_log.txt).

**OLED Display:** Displays the SSID, RSSI, and GPS coordinates for each scanned network on the OLED.

**Tracking Strongest RSSI:** The updateNetworkInfo function tracks the highest RSSI value for each Wi-Fi network. If a stronger signal is detected for a known SSID, it updates the saved RSSI and the GPS coordinates.

## What It Looks Like (for now)

[front](https://github.com/megaBC333/GPSniffer/blob/main/front.jpg)

[back](https://github.com/megaBC333/GPSniffer/blob/main/back.jpg)

## Code

```
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <TinyGPS++.h>
#include <SPI.h>
#include <SD.h>

// SD Card
#define SD_CS 5

// OLED display
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// GPS
TinyGPSPlus gps;
HardwareSerial GPSserial(1);

// Structure to keep track of network data and strongest RSSI
struct NetworkInfo {
  String ssid;
  int bestRSSI;
  double bestLat;
  double bestLong;
};

std::vector<NetworkInfo> networks;

// SD Card logging file
File logFile;

// Function to log network info to SD card
void logToSD(String ssid, int rssi, double latitude, double longitude) {
  logFile = SD.open("/wifi_log.txt", FILE_APPEND);
  if (logFile) {
    logFile.print("SSID: ");
    logFile.print(ssid);
    logFile.print(" | RSSI: ");
    logFile.print(rssi);
    logFile.print(" | Location: ");
    logFile.print(latitude, 6);
    logFile.print(", ");
    logFile.println(longitude, 6);
    logFile.close();
  } else {
    Serial.println("Error opening log file.");
  }
}

// Function to update strongest RSSI and GPS coordinates for each network
void updateNetworkInfo(String ssid, int rssi, double latitude, double longitude) {
  bool found = false;
  for (auto &net : networks) {
    if (net.ssid == ssid) {
      found = true;
      if (rssi > net.bestRSSI) {  // If new RSSI is stronger, update data
        net.bestRSSI = rssi;
        net.bestLat = latitude;
        net.bestLong = longitude;
      }
    }
  }
  if (!found) {  // If it's a new network, add it to the list
    NetworkInfo newNet = {ssid, rssi, latitude, longitude};
    networks.push_back(newNet);
  }
}

// Function to scan for Wi-Fi networks
void scanWiFi(double latitude, double longitude) {
  int n = WiFi.scanNetworks();
  if (n == 0) {
    Serial.println("No networks found.");
  } else {
    for (int i = 0; i < n; ++i) {
      String ssid = WiFi.SSID(i);
      int rssi = WiFi.RSSI(i);
      updateNetworkInfo(ssid, rssi, latitude, longitude);  // Track strongest RSSI

      // Log each scan result to SD card
      logToSD(ssid, rssi, latitude, longitude);

      // Display on OLED
      display.clearDisplay();
      display.setTextSize(1);
      display.setCursor(0, 0);
      display.print("SSID: ");
      display.println(ssid);
      display.print("RSSI: ");
      display.println(rssi);
      display.print("Lat: ");
      display.println(latitude, 6);
      display.print("Long: ");
      display.println(longitude, 6);
      display.display();
      delay(2000);  // Wait for 2 seconds before scanning next network
    }
  }
}

// Setup
void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;);
  }
  display.display();
  delay(2000);
  display.clearDisplay();

  // Initialize GPS
  GPSserial.begin(9600, SERIAL_8N1, 16, 17); // RX=16, TX=17

  // Initialize SD card
  if (!SD.begin(SD_CS)) {
    Serial.println("SD Card initialization failed!");
    return;
  }
  logFile = SD.open("/wifi_log.txt", FILE_WRITE);
  if (logFile) {
    logFile.println("Starting WiFi + GPS Logging");
    logFile.close();
  }
}

// Loop
void loop() {
  // Check for GPS data and parse it
  while (GPSserial.available() > 0) {
    gps.encode(GPSserial.read());
  }

  // Get GPS location
  double latitude = 0.0;
  double longitude = 0.0;
  if (gps.location.isValid()) {
    latitude = gps.location.lat();
    longitude = gps.location.lng();
  }

  // Scan for Wi-Fi networks and log/display results
  scanWiFi(latitude, longitude);

  delay(10000);  // Wait 10 seconds before scanning again
}
