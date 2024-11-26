# What It Does

**Wi-Fi Scanning:** The ESP32 scans for available Wi-Fi networks and records the SSID and RSSI (signal strength).

**GPS Tracking:** The GPS module provides latitude and longitude information during scanning, which is logged along with the Wi-Fi network data.

**SD Card Logging:** The data (SSID, RSSI, and GPS coordinates) is logged into a file on the SD card (/wifi_log.txt).

**OLED Display:** Displays the SSID, RSSI, and GPS coordinates for each scanned network on the OLED.

## What It Looks Like (for now)

[front](https://github.com/megaBC333/GPSniffer/blob/main/front.jpg)

[back](https://github.com/megaBC333/GPSniffer/blob/main/back.jpg)

## What I Have Planned

**Dedicated standalone PCB**

**Better debugging**

**Better network location estimation based on RSSI**

## Code

```
#include <WiFi.h>
#include <TinyGPS++.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <SPI.h>
#include <SD.h>

// GPS and OLED settings
TinyGPSPlus gps;
HardwareSerial GPSserial(1); // Using hardware serial for GPS
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// SD card and LED settings
#define SD_CS 5
#define LED_BUILTIN 2

// Variables to store the log file
String filename;

void setup() {
  Serial.begin(115200);
  GPSserial.begin(9600, SERIAL_8N1, 16, 17);  // RX, TX for GPS

  // Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 allocation failed");
    for (;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("Initializing...");
  display.display();

  // Initialize SD card
  if (!SD.begin(SD_CS)) {
    Serial.println("SD Card Initialization failed!");
    display.clearDisplay();
    display.print("SD init failed");
    display.display();
    return;
  }
  Serial.println("SD Card Initialized.");

  // Initialize LED
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  // Wait for GPS fix to get valid time
  filename = getGPSFilename();
  Serial.println("Log filename: " + filename);

  display.clearDisplay();
  display.print("Ready");
  display.display();
}

void loop() {
  // GPS data processing
  while (GPSserial.available() > 0) {
    gps.encode(GPSserial.read());
  }

  double latitude = gps.location.isValid() ? gps.location.lat() : 0.0;
  double longitude = gps.location.isValid() ? gps.location.lng() : 0.0;

  // Wi-Fi scanning
  int n = WiFi.scanNetworks();
  Serial.println("Scan done");

  // Update OLED display
  display.clearDisplay();
  display.setCursor(0, 0);
  for (int i = 0; i < n && i < 3; ++i) {  // Show max 3 networks
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

  // Log data to SD card
  logData(n, latitude, longitude);

  delay(2000);  // Wait 2 seconds before the next scan
}

String getGPSFilename() {
  // Wait for a valid GPS date and time
  while (!gps.date.isValid() || !gps.time.isValid()) {
    while (GPSserial.available() > 0) {
      gps.encode(GPSserial.read());
    }
    Serial.println("Waiting for GPS time...");
    delay(1000);
  }

  // Create filename based on GPS date and time
  String year = String(gps.date.year());
  String month = String(gps.date.month());
  String day = String(gps.date.day());
  String hour = String(gps.time.hour());
  String minute = String(gps.time.minute());
  String second = String(gps.time.second());

  // Format filename: log_YYYYMMDD_HHMMSS.txt
  String filename = "/log_" + year + month + day + "_" + hour + minute + second + ".txt";
  return filename;
}

void logData(int n, double latitude, double longitude) {
  File dataFile = SD.open(filename, FILE_APPEND);
  if (dataFile) {
    Serial.println("Logging data...");
    blinkLED(5, 100);  // Blink LED while writing data

    for (int i = 0; i < n; ++i) {
      dataFile.print("SSID: ");
      dataFile.print(WiFi.SSID(i));
      dataFile.print(" | RSSI: ");
      dataFile.print(WiFi.RSSI(i));
      dataFile.print(" | Lat: ");
      dataFile.print(latitude, 6);
      dataFile.print(" | Long: ");
      dataFile.println(longitude, 6);
      dataFile.println("-------------------");
    }
    dataFile.close();
    Serial.println("Data logged successfully.");
  } else {
    Serial.println("Failed to open log file!");
  }
}

void blinkLED(int times, int delayTime) {
  for (int i = 0; i < times; ++i) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(delayTime);
    digitalWrite(LED_BUILTIN, LOW);
    delay(delayTime);
  }
}

```

## Estimate Network Location

You can then run this python script which will prompt you to use the log file that was created to estimate the most likely location of the wifi networks that were scanned based on the RSSI values

```
import pandas as pd
import re
import numpy as np

# Adjust display options to show all rows
pd.set_option("display.max_rows", None)

def parse_log_file(filename):
    """Extract SSID, RSSI, latitude, and longitude from the log file."""
    pattern = r"SSID: (.+?) \| RSSI: (-?\d+) \| Lat: ([\d.-]+) \| Long: ([\d.-]+)"
    data = []

    print("Reading log file...")  # Debugging message

    with open(filename, 'r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                ssid = match.group(1).strip()
                rssi = int(match.group(2))
                lat = float(match.group(3))
                lon = float(match.group(4))
                data.append([ssid, rssi, lat, lon])

    if not data:
        print("No valid data found in the log file.")
        return pd.DataFrame(columns=["SSID", "RSSI", "Latitude", "Longitude"])

    return pd.DataFrame(data, columns=["SSID", "RSSI", "Latitude", "Longitude"])

def inverse_rssi_weight(rssi):
    """Calculate a weight from RSSI, where stronger signals have higher weights."""
    return 1 / (abs(rssi) + 1)  # Avoid division by zero with +1

def weighted_average_location(group):
    """Calculate the weighted average location using RSSI as the weight."""
    if group.empty:
        return pd.Series({"SSID": group.name, "Latitude": np.nan, "Longitude": np.nan})

    weights = group["RSSI"].apply(inverse_rssi_weight)
    lat_weighted_avg = np.average(group["Latitude"], weights=weights)
    lon_weighted_avg = np.average(group["Longitude"], weights=weights)
    return pd.Series({"SSID": group.name, "Latitude": lat_weighted_avg, "Longitude": lon_weighted_avg})

def analyze_networks(filename):
    """Analyze the log file and provide the best estimated location for each SSID."""
    df = parse_log_file(filename)

    if df.empty:
        print("No valid data to analyze.")
        return pd.DataFrame(columns=["SSID", "Latitude", "Longitude"])

    # Group by SSID and calculate the weighted average location
    best_locations = (
        df.groupby("SSID", as_index=False, group_keys=True)
        .apply(weighted_average_location)
        .reset_index(drop=True)
    )

    # Display the results
    print("\nEstimated Locations of Networks:")
    print(best_locations)

    return best_locations

def main():
    """Main function to prompt the user for the log file path and analyze it."""
    print("Wi-Fi Network Location Estimator")
    filename = input("Enter the path to the log file: ").strip()

    try:
        best_approximations = analyze_networks(filename)
    except FileNotFoundError:
        print(f"Error: File not found at '{filename}'. Please check the path and try again.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

```
