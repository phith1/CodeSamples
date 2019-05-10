import argparse
import googlemaps
import pandas as pd
import random

from utils import compute_distance as haversine

''' This code generates a detour index for Odisha using a sample of 600 single-direction routes between villages.
    A 600-route sample provides a 99% confidence interval with a 5% margin of error, which allows us to use this value
    rather than utilizing the Google Directions API, which could cost money with prolonged use. 
    
    NOTE: Sometimes the code breaks during runtime while reading the JSONs. It's completely unclear why, as putting in 
    the GPS coordinates works just fine on user-facing Maps. 

    Runtime arguments: 
    village_data_file -- CSV file containing basic location and market data for villages within Odisha, India.
    api_key -- Google Directions API key to accurately get travel-route distance.

    Output: 
    detour_index -- Float value printed to screen. (Odisha's is 1.425, for reference)
    '''


def maps_directions(start_lat, start_lon, end_lat, end_lon, gmaps):
    # directions API can take many types of input, including strings
    start_string = "{},{}".format(start_lat, start_lon)
    end_string = "{},{}".format(end_lat, end_lon)
    result = gmaps.directions(origin=start_string, destination=end_string)

    # we only care about finding the travelled length in the JSON output, which we convert from meters to km, * 0.001
    manhattan_distance = float(result[0]['legs'][0]['distance']['value']) * 0.001
    euclidean_distance = haversine(float(start_lat), float(start_lon), float(end_lat), float(end_lon))
    ratio = float(manhattan_distance/euclidean_distance)
    return euclidean_distance, manhattan_distance, ratio


def main(villages, api):
    gmaps = googlemaps.Client(key=api)
    village_sample = pd.DataFrame(columns=[
        'Start_Latitude', 'Start_Longitude', 'End_Latitude', 'End_Longitude',
        'Euclidean_Distance', 'Manhattan_Distance', 'Ratio'
    ])

    # get max number of villages for random sampling
    village_count = len(villages['Location_ID'])

    # doing 600 sample routes, can be edited for different population sizes
    for index in range(600):
        # generate random indices and make sure they're not the same
        start_index = random.randrange(0, village_count)
        end_index = random.randrange(0, village_count)
        while start_index == end_index:
            end_index = random.randrange(0, village_count)

        # get the lat/lons of both locations
        start_lat = villages.loc[villages.index[start_index], 'Latitude']
        start_lon = villages.loc[villages.index[start_index], 'Longitude']
        end_lat = villages.loc[villages.index[end_index], 'Latitude']
        end_lon = villages.loc[villages.index[end_index], 'Longitude']

        # get the two distances and manhattan/euclidean ratio
        euclidean, manhattan, ratio = maps_directions(start_lat, start_lon, end_lat, end_lon, gmaps)

        # add everything to a DataFrame and print a line for progress-tracking (and in case that weird error happens)
        village_sample.loc[index] = [start_lat, start_lon, end_lat, end_lon, euclidean, manhattan, ratio]
        print("{} of 600; ({}, {}) to ({}, {})".format(index, start_lat, start_lon, end_lat, end_lon))

    # print out the mean ratio across routes
    print("Average Ratio of Manhattan to Euclidean Distances: {}".format(village_sample['Ratio'].mean()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Produces the detour index for a given file of villages')
    parser.add_argument('village_data_file', type=str, help='The path to the input csv file of village markets data.')
    parser.add_argument('api_key', type=str, help='The google maps api key to use.')
    args = parser.parse_args()

    villages = pd.read_csv(args.village_data_file, dtype=str)
    api = args.api_key

    main(villages, api)
