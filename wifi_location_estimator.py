import re
from collections import defaultdict

# Regular expression to match SSID, RSSI, Latitude, and Longitude
log_entry_pattern = re.compile(
    r"SSID: (.+?) \| RSSI: (-?\d+)\s*\|\s*GPS Latitude: (-?\d+\.\d+)\s*\|\s*GPS Longitude: (-?\d+\.\d+)"
)

# Function to calculate the average latitude and longitude
def average_location(locations):
    avg_lat = sum(lat for lat, _ in locations) / len(locations)
    avg_lon = sum(lon for _, lon in locations) / len(locations)
    return avg_lat, avg_lon

# Function to process the log file
def estimate_wifi_locations(log_file):
    # Dictionary to store network data
    networks = defaultdict(list)

    # Read the log file
    try:
        with open(log_file, 'r') as file:
            log_data = file.read()  # Read the entire log file content
            matches = log_entry_pattern.findall(log_data)  # Find all matches

            for match in matches:
                ssid = match[0]
                rssi = int(match[1])
                latitude = float(match[2])
                longitude = float(match[3])

                # Store RSSI and location (latitude, longitude) for each SSID
                networks[ssid].append((rssi, latitude, longitude))

    except FileNotFoundError:
        print(f"File {log_file} not found. Please check the file path.")
        return

    # Estimate the location of each network
    estimated_locations = {}
    for ssid, data in networks.items():
        # Sort the entries by RSSI in descending order (strongest signal first)
        data.sort(reverse=True, key=lambda x: x[0])

        # Get the top 5 strongest signals (or fewer if not available)
        top_signals = data[:5]

        # Extract the GPS coordinates from the top signals
        locations = [(lat, lon) for _, lat, lon in top_signals]

        # Calculate the average location based on the strongest signals
        estimated_locations[ssid] = average_location(locations)

    return estimated_locations

# Main function to read the log file and output estimated locations
if __name__ == "__main__":
    log_file = input("Enter the path to your log.txt file: ")

    # Estimate Wi-Fi network locations
    wifi_locations = estimate_wifi_locations(log_file)

    if wifi_locations:
        print("\nEstimated Wi-Fi network locations:")
        for ssid, (lat, lon) in wifi_locations.items():
            print(f"SSID: {ssid} -> Estimated Location: Latitude {lat}, Longitude {lon}")
    else:
        print("No valid data to process.")
