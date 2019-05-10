
import numpy as np
import pandas as pd
import random

import sys
sys.path.append('..')
import geo_raster_viewer
from utils import compute_distance as haversine

''' Very basic and hard-coded data processing lifted from a Jupyter Notebook. Produced as separate script to allow easy
    data generation for HERMES Agrifood post-processing/manipulation.
    '''

# Make our viewer by loading existing data for all of Odisha.
odisha_population = geo_raster_viewer.load("odisha_population")

# If you're interested in a specific region, you can extract it
odisha_min_lat = 17.784
odisha_max_lat = 22.582
odisha_min_lon = 81.359
odisha_max_lon = 87.459

'''
odisha = viewer.extract_region(
    odisha_min_lat,
    odisha_max_lat,
    odisha_min_lon,
    odisha_max_lon,
)
'''

# Clip negative values.
odisha_population.pixel_array = np.clip(odisha_population.pixel_array, 0.0, None)

# Write population to CSV and to ArcGIS-safe Header CSV
#odisha_population.pixels_to_file("odisha_population")
#odisha_population.write_ArcGIS_header("odisha_population")

# Digitize array, add buffer, and write Population Density to CSV
categorized_map = odisha_population.digitize([0, 700, np.inf])
periurban_bhadrak = categorized_map.add_categorical_buffer(around=2, distance=5, level=2)
#periurban_bhadrak.pixels_to_file("odisha_population_density")

'''
# Create distances array and write to CSV
odisha_midpoint_lat = (odisha_min_lat + odisha_max_lat) / 2
odisha_midpoint_lon = (odisha_min_lon + odisha_max_lon) / 2
odisha_distances = odisha_population.get_distances_to_coord([odisha_midpoint_lat, odisha_midpoint_lon])
#np.savetxt("odisha_distances.csv", odisha_distances[0], delimiter=" ")'''

# Now we do a quick calculation of populations served by each wholesaler and drop the ones without lat/lons.
wholesales = pd.read_csv("data/wholesale_data_407.csv")
wholesales.dropna(subset=['Longitude', 'Latitude'], inplace=True)
wholesales.reset_index(inplace=True)
wholesales_service = []

'''
# Get the list of lat/lons
wholesale_markets = list(zip(wholesales['Latitude'].values, wholesales['Longitude'].values))

# Match pixels to the list of locations
closest_wholesales = odisha_population.match_to_closest_location(wholesale_markets)

# We can then get the number of people covered by each location.
# If a wholesaler is too far from the gridded area to cover any people, set Pop_Served to Zero.
people_per_market = odisha_population.sum_by_labels(closest_wholesales)
for wholesale_index in range(0, len(wholesales)):
    if wholesale_index in people_per_market.keys():
        wholesales_service.append(people_per_market[wholesale_index])
    else:
        wholesales_service.append(0)

# And produce an accessible wholesaler list with the population served data.
wholesales["Population_Served"] = wholesales_service
wholesales.to_csv("odisha_wholesale_service_{}.csv".format(len(wholesales)), index=False)
'''


# Now we do a quick calculation of populations served by each village market and drop the ones without lat/lons.
villages = pd.read_csv("data/odisha_village_data.csv")
villages.dropna(subset=['Longitude', 'Latitude'], inplace=True)
villages.reset_index(inplace=True)
villages_service = []

# Get the list of lat/lons
village_markets = list(zip(villages['Latitude'].values, villages['Longitude'].values))

# Match pixels to the list of locations
closest_villages = odisha_population.match_to_closest_location(village_markets)

# We can then get the number of people covered by each location.
people_per_market = odisha_population.sum_by_labels(closest_villages)
for market_index in range(0, len(villages)):
    if market_index in people_per_market.keys():
        villages_service.append(people_per_market[market_index])
    else:
        villages_service.append(0)

# From here, we want to find the closest Wholesaler to each Village.
villages_closest_wm_name = []
villages_closest_wm_lat = []
villages_closest_wm_lon = []
villages_closest_wm_distance = []
for village in villages.itertuples():
    # Amass distances, calculate the closest, and append the data to lists.
    distances = haversine(village.Latitude, village.Longitude, wholesales["Latitude"], wholesales["Longitude"])
    closest = np.argmin(np.ndarray.flatten(distances))
    raw_distance = distances[closest][0][0]
    closest_wm = wholesales.iloc[closest]

    villages_closest_wm_name.append(closest_wm['Wholesale_Name'])
    villages_closest_wm_lat.append(closest_wm['Latitude'])
    villages_closest_wm_lon.append(closest_wm['Longitude'])
    villages_closest_wm_distance.append(raw_distance)

# And produce an accessible village market list with the population served and closest wholesaler data.
villages["Closest_Wholesaler"] = villages_closest_wm_name
villages["Wholesaler_Latitude"] = villages_closest_wm_lat
villages["Wholesaler_Longitude"] = villages_closest_wm_lon
villages["Wholesaler_Distance"] = villages_closest_wm_distance
villages["Population_Served"] = villages_service
villages.to_csv("odisha_village_service.csv", index=False)


# And it also doesn't hurt to add in something to assign urbanicity values to a file with lat-lons.
# Particularly, we know we need it for Villages and for Wholesales
odisha_pixels = pd.read_csv("odisha_village_data_aggregation.csv")
village_urbanicity = []
for village in villages.itertuples():
    # Find the corresponding pixel-space block.
    valid_up = village.Longitude <= odisha_pixels['Lon_Upper'].max()
    valid_down = odisha_pixels['Lon_Lower'].min() <= village.Longitude
    valid_left = odisha_pixels['Lat_Lower'].min() <= village.Latitude
    valid_right = village.Latitude <= odisha_pixels['Lat_Upper'].max()
    in_bounds = valid_up and valid_down and valid_left and valid_right

    # An empty row indicates a village isn't contained within Odisha.
    row = odisha_pixels.loc[
        (odisha_pixels['Lat_Lower'] <= village.Latitude)
        & (village.Latitude <= odisha_pixels['Lat_Upper'])
        & (odisha_pixels['Lon_Lower'] <= village.Longitude)
        & (village.Longitude <= odisha_pixels['Lon_Upper'])
        ]

    # Add the village's information to the list if it's within the region.
    urbanicity = 0
    if not row.empty:
        # Record the Urbanicity
        urbanicity = row['Density'].values[0]
    village_urbanicity.append(urbanicity)
villages['Urbanicity'] = village_urbanicity
villages.to_csv("odisha_village_urbanicity.csv", index=False)

wholesale_urbanicity = []
for wholesale in wholesales.itertuples():
    # Find the corresponding pixel-space block.
    valid_up = wholesale.Longitude <= odisha_pixels['Lon_Upper'].max()
    valid_down = odisha_pixels['Lon_Lower'].min() <= wholesale.Longitude
    valid_left = odisha_pixels['Lat_Lower'].min() <= wholesale.Latitude
    valid_right = wholesale.Latitude <= odisha_pixels['Lat_Upper'].max()
    in_bounds = valid_up and valid_down and valid_left and valid_right

    # An empty row indicates a village isn't contained within Odisha.
    row = odisha_pixels.loc[
        (odisha_pixels['Lat_Lower'] <= wholesale.Latitude)
        & (wholesale.Latitude <= odisha_pixels['Lat_Upper'])
        & (odisha_pixels['Lon_Lower'] <= wholesale.Longitude)
        & (wholesale.Longitude <= odisha_pixels['Lon_Upper'])
        ]

    # Add the village's information to the list if it's within the region.
    urbanicity = 0
    if not row.empty:
        # Record the Urbanicity
        urbanicity = row['Density'].values[0]
    wholesale_urbanicity.append(urbanicity)
wholesales['Urbanicity'] = wholesale_urbanicity
wholesales.to_csv("odisha_wholesale_urbanicity.csv", index=False)