import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# Load the CSV data
def load_csv_data(file_path):
    return pd.read_csv(file_path)

# Function to geocode locations with retry mechanism
def geocode_location(location, retries=3, timeout=10):
    geolocator = Nominatim(user_agent="company_location_plotter")
    
    for _ in range(retries):
        try:
            location_obj = geolocator.geocode(location, timeout=timeout)
            if location_obj:
                return location_obj.latitude, location_obj.longitude
            else:
                return None, None  # If the location cannot be geocoded
        except GeocoderTimedOut:
            print(f"Geocoding timed out for {location}. Retrying...")
            time.sleep(2)  # Wait for 2 seconds before retrying
        except Exception as e:
            print(f"An error occurred while geocoding {location}: {e}")
            return None, None

    print(f"Failed to geocode {location} after {retries} retries.")
    return None, None

# Function to create the map and add markers for each company
def plot_on_map(data):
    # Create an initial map centered on India (you can adjust the coordinates if needed)
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

    # Iterate through the rows and add markers
    for index, row in data.iterrows():
        company = row['Company Name']
        location = row['Location']
        emission = row['Carbon Emission']
        year = row['Year']

        # Geocode the location to get lat, long
        lat, lon = geocode_location(location)

        if lat and lon:
            # Add a marker for each company
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>Company:</b> {company}<br><b>Location:</b> {location}<br><b>Year:</b> {year}<br><b>CO₂ Emission:</b> {emission}",
                icon=folium.Icon(color="blue")
            ).add_to(m)

    return m

# Main function to run the plotting
def main():
    # Load the data from the CSV file
    data = load_csv_data("cleaned_data.csv")

    # Plot the data on the map
    m = plot_on_map(data)

    # Save the map as an HTML file
    m.save("company_emissions_map.html")
    print("✅ Map saved as company_emissions_map.html")

# Run the main function
main()
