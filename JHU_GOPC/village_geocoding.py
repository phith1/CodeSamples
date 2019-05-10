import os
import argparse
import json

import googlemaps
import pandas as pd
import shapefile as sf

''' This code creates a series of JSON files based upon census and location data for villages in Odisha, India. 

    Runtime arguments: 
    village_file -- Excel file (.xls) containing data for village markets within Odisha, India. 
    shape_file -- Shapefile (.shp) containing village locations, for use with Google Maps. 
    api_key -- Google Maps Geocoding API key. A billable account is needed to run the intended data to completion.

    Ancillary data files: 
    GoI_DemogCensus_2011_VillageMarkets.xlsx -- Excel file fed in as village_file. 
    problem_villages.csv -- Homemade list of issue villages, either by not existing or providing unexplainable queries.
    query_fixes.csv -- Lists of edits to village and district names so queries better align with Google Maps' data. 

    Output: 
    xxxxxx.json -- JSON files created by the program. Placed in 'jsonFiles' directory, named by 6-digit village ID. 
        Villages that produced invalid data are given a blank ('') JSON file. 
    village_with_lat_lons -- CSV file copying village_file, but with village lat/lon values added at the end. 
        Villages that were found not to exist within Google Maps are given a lat/lon set of (0.0, 0.0)
    '''

COMPONENTS = {
    'country': 'IN'
}


# Builds a Maps-able address string for use with Geo-coding queries and JSON generation
def build_address(village_name, district=None):
    if district is not None:
        address = '{}, {}, Odisha, India'.format(
            village_name,
            district,
        )
    else:
        address = '{}, Odisha, India'.format(
            village_name
        )
    return address


def get_lat_lon(client, village_name, village_id, boundbox, district=None, block=None):
    # Build the address for the Maps query.
    address = build_address(village_name, district)

    # Convert the bounding box to GMaps-safe format, then complete geo-coding for the village.
    result = client.geocode(
        address=address,
        components=COMPONENTS,
        bounds={
            'northeast': {
                'lat': boundbox[3],
                'lng': boundbox[2]
            },
            'southwest': {
                'lat': boundbox[1],
                'lng': boundbox[0]
            }
        }
    )

    # Access the address's lat/lon; result is traversed oddly due to being saved in JSON format by geocode().
    try:
        lat_lon = result[0]['geometry']['location']
        latitude = lat_lon['lat']
        longitude = lat_lon['lng']

        # Save to JSON file titled within 6-digit village ID.
        filepath = str(village_id)
        json_filename = 'jsonFiles\\{}.json'.format(filepath)
        with open(json_filename, 'w') as outfile:
            json.dump(result, outfile, indent=4)

        # Print out the address for progress monitoring, and return lat/lon/address.
        print('{}, {}, {}, Odisha, India at ( {}, {} )'.format(
            village_name,
            block,
            district,
            # ...Odisha, India at...
            latitude,
            longitude))
        return latitude, longitude, address

    # If accessing lat/lon is unsuccessful...
    except:
        # Fallback onto removing the district and then returning 0.0, 0.0 if the village doesn't exist.
        if district is not None:
            return get_lat_lon(client, village_name, village_id, boundbox)
        else:
            return 0.0, 0.0, address


def main(villages, shapes, api_key):
    villages = villages.rename(
        columns={
            'Village Name': 'Village_Name',
            'District Name': 'District_Name',
            'Sub District Name': 'Sub_District_Name',
            'CD Block Name': 'CD_Block_Name',
            'Village Code': 'Village_Code'
        }
    )

    # Note for parsing individual shapes:
    # BLOCK_ID, shape[-1: BLOCK_ID] = shape[3: Dist_Name] + '_' + shape[5: Sub_Dist_N]

    # Read the list of spelling fixes at the district level.
    # -- Prior fixes data was lost with hard drive failure. Districts were most important tweaks.
    fixes = pd.read_csv('data\\query_fixes.csv')
    fixes_dist = fixes[['District_Old', 'District_New']]
    fixes_block = fixes[['Block_Old', 'Block_New']]

    # Read the list of problem villages to remove later.
    problems = pd.read_csv('data\\problem_villages.csv')
    problems = problems['Village_Code'].values.tolist()

    # Then refine the read shapefile into records and the list of shapes.
    shape_rec = shapes.records()
    shape_list = shapes.shapes()

    # Set up the google maps client and lists for lat/lons to be recorded and later appended.
    gmaps = googlemaps.Client(key=api_key)
    latitudes = []
    longitudes = []
    queries = []

    # Loop through every village, modifying village/block/district names as needed before finding the bounding box.
    for index, village in villages.iterrows():
        # Many of these variables have leading or trailing whitespace that must be removed.
        village_name = village['Village_Name'].strip()
        block_name = village['CD_Block_Name'].strip()
        dist_name = village['District_Name'].strip()
        v_code = village['Village_Code']

        # Handle district-level and block-level changes from fixes.csv.
        for index, fix in fixes_dist.iterrows():
            if dist_name == fix['District_Old']:
                dist_name = fix['District_New']

        for index, fix in fixes_block.iterrows():
            # Fringe case because Padmapur exists in Bargarh and Rayagada, and Rayagada's should stay as-is.
            if block_name == 'Padmapur' and dist_name == 'Rayagada':
                pass
            elif block_name == fix['Block_Old']:
                block_name = fix['Block_New']

        # Create block_id, used to match a block to a given shape, and loop through all records of shapes.
        block_id = dist_name + '_' + block_name
        added = False

        for shape, bindex in zip(shape_rec, range(len(shape_rec))):
            # If the shape's name (shape[-1]) matches block_id, we've got a match.
            shape_name = shape[3] + "_" + shape[5]
            if shape_name == block_id:
                # Grab the bounding box and use it to pass the village into the geo-coding function.
                bbox = shape_list[bindex].bbox
                latitude, longitude, search = get_lat_lon(
                    client=gmaps,
                    village_name=village_name,
                    village_id=v_code,
                    boundbox=bbox,
                    district=dist_name,
                    block=block_name,
                )

                # Compare village code against problem villages.
                if v_code in problems:
                    # Clear JSON and append empty latlons for matches.
                    json_filename = 'jsonFiles\\{}.json'.format(str(v_code))
                    with open(json_filename, 'w') as outfile:
                        json.dump('', outfile, indent=4)
                    latitudes.append(0.0)
                    longitudes.append(0.0)
                else:
                    # Append valid latlons for non-problem villages.
                    latitudes.append(latitude)
                    longitudes.append(longitude)

                # Append search queries for ease of post-processing and denote village was added.
                queries.append(search)
                added = True
        if added == False:
            # If a village doesn't match any blocks and isn't in final data, alert the user.
            print("{}, in {}_{} not added!".format(village_name, dist_name, block_name))

    # Since we looped through all villages, now time to append lats/lons to new file.
    villages['Latitude'] = latitudes
    villages['Longitude'] = longitudes
    villages['MapsQuery'] = queries

    # But since we have the list of problem locations, we need to remove those from the final data set before writing.
    villages = villages[~villages.Village_Code.isin(problems)]
    villages.to_csv('village_with_lat_lons.csv', index=False)


if __name__ == '__main__':
    # Set up and read command line arguments.
    parser = argparse.ArgumentParser('Adds lat/lons to the village data file using google maps web '
                                     'api using a file of villages and a google maps api key.')
    parser.add_argument('village_file', type=str, help='The path to the input excel file of village markets')
    parser.add_argument('shape_file', type=str, help='The path to the input shape file of village locations')
    parser.add_argument('api_key', type=str, help='The google maps api key to use.')

    args = parser.parse_args()
    village_file = pd.read_excel(args.village_file)
    shape_file = sf.Reader(args.shape_file)
    api = args.api_key

    # If 'jsonFiles' directory doesn't exist, build it for the output.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dirs = [name for name in os.listdir(dir_path)]
    if 'jsonFiles' not in dirs:
        os.mkdir('jsonFiles')

    main(village_file, shape_file, api)
