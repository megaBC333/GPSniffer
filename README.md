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
#include <TinyGPS++.h>
#include <Adafruit_SSD1306.h>
#include <SPI.h>
#include <SD.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

TinyGPSPlus gps;  // Create a GPS object
HardwareSerial GPSserial(1); // RX, TX for GPS

File logFile;
const int chipSelect = 5; // SD card CS pin

void setup() {
  Serial.begin(115200);
  GPSserial.begin(9600, SERIAL_8N1, 16, 17); // RX, TX for GPS
  
  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;);
  }
  display.clearDisplay();
  
  // Initialize SD Card
  if (!SD.begin(chipSelect)) {
    Serial.println("SD Card Initialization failed!");
    return;
  }
  
  logFile = SD.open("log.txt", FILE_WRITE);
  if (logFile) {
    logFile.println("Starting WiFi + GPS Logging");
    logFile.close();
  }
  
  Serial.println("Waiting for valid GPS signal...");
}

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

void scanWiFi(double latitude, double longitude) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  
  int numNetworks = WiFi.scanNetworks();
  Serial.println("Scan done.");
  
  if (numNetworks == 0) {
    display.println("No networks found");
    Serial.println("No networks found");
  } else {
    Serial.println(numNetworks);
    display.println("Available Networks:");
    
    // Track strongest RSSI
    int strongestRSSI = -100; // Low initial value
    String strongestSSID;

    for (int i = 0; i < numNetworks; ++i) {
      String ssid = WiFi.SSID(i);
      int rssi = WiFi.RSSI(i);
      
      display.print(i + 1);
      display.print(": ");
      display.print(ssid);
      display.print(" (");
      display.print(rssi);
      display.println(" dBm)");
      
      // Update strongest RSSI info
      if (rssi > strongestRSSI) {
        strongestRSSI = rssi;
        strongestSSID = ssid;
      }

      // Log to SD card
      logFile = SD.open("log.txt", FILE_WRITE);
      if (logFile) {
        logFile.print(ssid);
        logFile.print(", RSSI: ");
        logFile.print(rssi);
        logFile.print(", Latitude: ");
        logFile.print(latitude);
        logFile.print(", Longitude: ");
        logFile.println(longitude);
        logFile.close();
      }

      display.display();  // Update OLED display
      delay(200); // Delay for readability
    }
    
    // Show strongest SSID with coordinates
    display.println("Strongest:");
    display.print(strongestSSID);
    display.print(" (");
    display.print(strongestRSSI);
    display.println(" dBm)");
    display.display();  // Update OLED display
  }

  // Log final data to SD card
  logFile = SD.open("log.txt", FILE_WRITE);
  if (logFile) {
    logFile.println("Logged data to SD card");
    logFile.close();
  }
}
