import argparse
import numpy as np
import os
import pandas as pd

from utils import compute_distance as haversine

''' This code aggregates a list of villages using two approaches.
        1) -r, range mode, takes in a list of villages, and outputs a list of villages within that range of an origin
        2) the default Aggregate mode, which assembles four TIF-derived data files into a population master file,
           which contains gridded population boundaries, population counts, urbanicity, and distance from the origin

    The files needed for aggregate mode can be obtained by running the Georasterviewer code (for now!), particularly a
    variant on the 'GeoRasterViewer using Bhadrak.ipynb' notebook. 

    NOTE: Cities aren't included in our data, only villages, so I've included a sample arguments below.     
    Bhadrak Centerpoint: 21.0583 86.4658 34.0
    Bhadrak Snapshot Bounds: 
        bhadrak_min_lat = 20.751
        bhadrak_max_lat = 21.365
        bhadrak_min_lon = 86.140 
        bhadrak_max_lon = 86.795
        
    Niali/Aiginia Centerpoint: 20.234 85.964 17.0
        test_min_lat = 20.096
        test_max_lat = 20.372
        test_min_lon = 85.847
        test_max_lon = 86.081

    Runtime arguments: 
        -r/range: Enables range mode, which uses [villages, center_lat, center_lon, radius] to create a list of villages
            in [radius] km from the center. Ignores [header, population, population_density, population_distance].
    
    Always required:    
        villages -- CSV file containing basic location and market data for villages within area in question.
        center_lat -- Float value for the center's latitude. 
        center_lon -- Float value for the center's longitude.
        radius -- Distance in km where retailers can be created.  
    
    Required when not in Range mode: 
        header -- CSV file containing basic bounding data for the region generating retailers. 
        population -- CSV file breaking the region into population by pixel.
        population_density -- CSV file breaking the region into urban/periurban/rural by pixel. 
        population_distance -- CSV file containing distances from origin for each pixel. 

    Output: 
        villages_within_[radius].csv -- all villages from input file within [radius] km of the center point.
        [name]_aggregation.csv -- consolidation of Georasterviewer-created files into dataframe for retailer generation.

    '''


def villages_in_range(villages, origin):
    near_lat = np.array([origin['lat']])
    near_lon = np.array([origin['lon']])
    far_lats = villages.Latitude.values
    far_lons = villages.Longitude.values

    distance = np.ndarray.flatten(haversine(near_lat, near_lon, far_lats, far_lons))
    villages["From_Center"] = distance

    within_range = villages.loc[villages["From_Center"] <= origin['radius']]
    within_range.to_csv("villages_within_{}.csv".format(origin['radius']), index=False)

    # Now we print out some quick data for the user to feed into georasterviewer, with a little extra buffer space
    print("\nGeoraster Values:\n===================\nMin Lat: {}\nMax Lat: {}\nMin Lon: {}\nMax Lon: {}".format(
        within_range['Latitude'].min() + 0.15,
        within_range['Latitude'].max() + 0.15,
        within_range['Longitude'].min() + 0.15,
        within_range['Longitude'].max() + 0.15,
    ))


def grid_data_aggregation(origin, header, population, population_density, distances, file_name):
    # header_data; rows = lats, cols = lons
    lon_lower_left = header.iloc[2][1]
    lat_lower_left = header.iloc[3][1]
    cell_size = header.iloc[4][1]
    num_rows = population.shape[0]
    num_cols = population.shape[1]
    lat_upper_left = lat_lower_left + (num_rows * cell_size)
    labels = ["Row", "Column", "Lat_Lower", "Lat_Upper", "Lon_Lower",
              "Lon_Upper", "Population", "Density", "Distance"]

    # Create individual columns for the DataFrame, then assign.
    rows = [row for row in range(num_rows) for col in range(num_cols)]
    cols = [col for col in range(num_cols)] * num_rows
    data_aggregate = {
        "Row": rows,
        "Column": cols,
        "Population": population.values.flatten(),
        "Density": population_density.values.flatten(),
        "Distance": distances.values.flatten(),
        "Lat_Upper": [lat_upper_left - (row * cell_size) for row in rows],
        "Lat_Lower": [lat_upper_left - ((row + 1) * cell_size) for row in rows],
        "Lon_Lower": [lon_lower_left + (col * cell_size) for col in cols],
        "Lon_Upper": [lon_lower_left + ((col + 1) * cell_size) for col in cols]
    }

    # make a DataFrame from all this info, and then strip out anything past the user-given radius
    # The radius check is extended by 2 to ensure that locations on the curve of the circular radius are still included.
    # Additions of + 0, + 1, and +1.5 all lead to loss of valid location data
    aggregate = pd.DataFrame(data_aggregate, columns=labels)
    aggregate = aggregate.loc[aggregate['Distance'] <= origin['radius'] + 2]
    aggregate.to_csv("{}_aggregation.csv".format(file_name), index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Produces a list of retailers based on population surrounding a center village.')
    parser.add_argument('-r', '--range', help='Generate villages within range of radius', action='store_true')
    parser.add_argument('village_data_file', type=str, help='The path to the input csv file of village markets data.')
    parser.add_argument('origin_lat', type=float, help="The center's latitude.")
    parser.add_argument('origin_lon', type=float, help="The center's longitude.")
    parser.add_argument('radius', type=float, help='Range of km from the center for retailers.')

    parser.add_argument('--header', type=str, help="The path to the header csv file.")
    parser.add_argument('--population', type=str, help="The path to the population csv file.")
    parser.add_argument('--urbanicity', type=str, help='The path to the population density csv file.')
    parser.add_argument('--distance', type=str, help='Path to file of distances from pixel to origin.')
    args = parser.parse_args()

    villages = pd.read_csv(
        args.village_data_file,
        dtype={
            'Location_ID': str,
            'Village_Name': str,
            'District_Name': str,
            'Block': str,
            'Market_Frequency': str,
            'Longitude': float,
            'Latitude': float,
        },
    )
    origin = {
        'lat': args.origin_lat,
        'lon': args.origin_lon,
        'radius': args.radius,
    }

    # if we're in --range mode, we don't need additional input files, we're just running villages_in_range()
    range_mode = args.range
    if range_mode:
        villages_in_range(villages, origin)

    # if we aren't in --range mode, we need all of the files
    else:
        header_file = pd.read_csv(args.header, header=None, delim_whitespace=True, index_col=0)
        population = pd.read_csv(args.population, header=None, delim_whitespace=True)
        pop_density = pd.read_csv(args.urbanicity, header=None, delim_whitespace=True)
        distances = pd.read_csv(args.distance, header=None, delim_whitespace=True)
        file_name = os.path.basename(args.village_data_file)[:-4]
        grid_data_aggregation(origin, header_file, population, pop_density, distances, file_name)
