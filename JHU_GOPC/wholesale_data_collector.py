import argparse
import pandas as pd
import shapefile as sf
from shapely import geometry

''' This code parses a file of Odisha wholesale village markets (Mandis) by district, adding block designations. 
    NOTE: Population_Served data is incorporated through the GeoRasterViewer code.  

    Runtime arguments: 
    wholesale_file -- CSV file containing District/Mandi names as well as Lat/Lon coordinates.
    id_file -- CSV breaking down unique 4-digit ID codes based on a location's block and district. 
    shape_file -- Path to shapefile to verify Blocks.
    fix_file -- CSV file with corrections from shapefile blocks into village blocks

    Output: 
    wholesale_data -- CSV with unique Wholesale Location ID, District and Market names, and Lat/Lon coordinates.   
    '''


def main(wholesales, codes, block_shapes, shape_names):
    # Manage column names for comparison
    wholesales['District_Name'] = wholesales['District_Name'].apply(lambda x: x.strip())
    wholesales['Wholesale_Name'] = wholesales['Wholesale_Name'].apply(lambda x: x.strip())
    wholesales = wholesales.rename(
        columns={
            'LONGITUDE': 'Longitude',
            'LATITUDE': 'Latitude',
            'Tier ': 'Tier',
        }
    )
    codes['District'] = codes['District'].apply(lambda x: x.strip())

    # Now we figure out which Block each wholesale is in, by using the Shapefile.
    shape_rec = block_shapes.records()
    shape_list = block_shapes.shapes()

    # Produce two dicts holding all blocks as (name, polygon) and (name, externalRing) key-value pairs
    block_dict = {}
    block_externals = {}
    for shape, rec in zip(shape_list, shape_rec):
        block_name = rec[5]
        poly = geometry.Polygon([p for p in shape.points])
        poly_ext = geometry.LinearRing(poly.exterior.coords)
        block_dict[block_name] = poly
        block_externals[block_name] = poly_ext

    # Loop through all wholesales and pair each with its corresponding block.
    blocks = []
    wrong_blocks = shape_names['Shape_Block'].tolist()
    for index, wholesale in wholesales.iterrows():
        # We need Lat/Lon of the wholesaler, formatted specifically as Lon/Lat.
        latitude = wholesale['Latitude']
        longitude = wholesale['Longitude']
        pinpoint = geometry.Point(float(longitude), float(latitude))

        # Then loop through each shape and check until the wholesale's point is inside a polygon.
        for block in block_dict.keys():
            if block_dict[block].contains(pinpoint):
                # If our Block is known to be a matching name, we can append.
                if block not in wrong_blocks:
                    blocks.append(block)
                    break

                # Otherwise we append our equivalent name.
                for num, mismatch in shape_names.iterrows():
                    if block == mismatch['Shape_Block']:
                        blocks.append(mismatch['Data_Block'])
                        break
                break

        # If we don't have a match (unlikely but possible), we need to find the closest polygon instead.
        else:
            # We create a dummied point and block to hold data beyond the loop below.
            closest_point = geometry.Point(0, 0)
            found_block = ""

            # Loop through the blocks and figure out which external point is closest to our wholesaler.
            for block in block_externals.keys():
                # Get the coordinate of the closest point of a given block outline.
                exterior = block_externals[block]
                projection = exterior.project(pinpoint)
                iter_nearest = exterior.interpolate(projection)

                # Compare and update if closer than saved point/block data.
                if pinpoint.distance(closest_point) > pinpoint.distance(iter_nearest):
                    closest_point = iter_nearest
                    found_block = block

            # If our Block name matches Shapefile's, append. Otherwise, append our equivalent name.
            if found_block not in wrong_blocks:
                blocks.append(found_block)
            else:
                for num, mismatch in shape_names.iterrows():
                    if found_block == mismatch['Shape_Block']:
                        blocks.append(mismatch['Data_Block'])
                        break

    # And finally add the list of blocks and unique ID designations to the list of wholesalers!
    wholesales['Block_Name'] = blocks
    wholesales['code'] = wholesales.District_Name + "_" + wholesales.Block_Name

    wholesales['Location_ID'] = ''
    for code in wholesales.groupby('code').groups.items():
        # Set index to 1 and isolate dist_block codes and indices of relevant wholesales.
        index = 1
        unique_code = code[0]
        wholesales_with_code = list(code[1])

        # Access the ID directory and get the four digits code set up.
        combo = codes.loc[codes["Combo"] == unique_code]
        district_code = combo.iloc[0]['District_Code']
        block_code = combo.iloc[0]['Block_Code']

        # Now we assign the full code, 7 (wholesale market) + dist/block codes + 3 digits for index.
        for wholesales_index in wholesales_with_code:
            full_id = '7{:02}{:02}{:03}'.format(district_code, block_code, index)
            wholesales.loc[wholesales_index, 'Location_ID'] = full_id
            index = index + 1

    # Write useful Wholesale information.
    useful_columns = ['Location_ID', 'Wholesale_Name', 'Block_Name', 'District_Name', 'Tier', 'Longitude', 'Latitude']
    wholesales.loc[:, useful_columns].to_csv("wholesale_data_{}.csv".format(len(wholesales)), index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Extracts useful wholesale information from the wholesale '
                                     'file and assigns each wholesale a unique ID')
    parser.add_argument('wholesale_file', type=str, help='The path to the input csv file of wholesale markets.')
    parser.add_argument('id_file', type=str, help='The path to the csv file of district/block names to numbers.')
    parser.add_argument('shape_file', type=str, help='The path to the shapefile for Odisha\'s blocks.')
    parser.add_argument('fix_file', type=str, help='The path to the csv file of shapefile to block name corrections.')
    args = parser.parse_args()

    wholesales_data = pd.read_csv(args.wholesale_file)
    codes_data = pd.read_csv(args.id_file)
    block_data = sf.Reader(args.shape_file)
    block_fixes = pd.read_csv(args.fix_file)

    main(wholesales_data, codes_data, block_data, block_fixes)
