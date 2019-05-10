import argparse
import pandas as pd

''' This code parses a file of Odisha Villages to assign HERMES-accessible village IDs. These IDs are created using the
    according to the key defined in the ID file. 
    
    Assumed pipeline of file executions is as follows: 
    1) village_geocoding.py      -- to get latitude/longitude values
    2) village_data_collector.py -- to assign Hermes Location_IDs, Market Frequencies, Blocks

    Runtime arguments: 
    village_file -- CSV file containing basic, location, and block data for village markets within Odisha, India.
    id_file -- CSV file with ID numbers corresponding to specific districts and blocks within Odisha.

    Output: 
    village_data -- CSV file with new Location ID, Village/District/Block Names, Market Frequency, and Lat/Longitude. 
    village_master_file -- CSV file with Census Data, Lat/Lons, Block, Market Frequency, and Hermes Location IDs.  
    '''

def main(villages, codes):
    # Strip and trim the names for comparison, also port CD Block Name over to Block column
    villages['District_Name'] = villages['District_Name'].apply(lambda x: x.strip())
    villages['Block_Name'] = villages['CD_Block_Name'].apply(lambda x: x.strip())
    villages['Village_Name'] = villages['Village_Name'].apply(lambda x: x.strip())

    # Set Daily or Weekly markets status
    villages['Market_Frequency'] = 'Weekly'
    villages.loc[villages['Mandis/Regular Market (Status A(1)/NA(0))'] == 1, 'Market_Frequency'] = 'Daily'

    # Create IDs for each village based on district and block
    villages['code'] = villages.District_Name + "_" + villages.Block_Name
    villages['Location_ID'] = ''
    for code in villages.groupby('code').groups.items():
        # set index to 1 and isolate dist_block codes and indices of relevant villages
        index = 1
        unique_code = code[0]
        villages_with_code = list(code[1])

        # access the ID directory and get the four digits code set up
        combo = codes.loc[codes["Combo"] == unique_code]
        district_code = combo.iloc[0]['District_Code']
        block_code = combo.iloc[0]['Block_Code']

        # now we assign the full code, 3 (village market) + dist/block codes + 3 digits for index
        for village_index in villages_with_code:
            full_id = '3{:02}{:02}{:03}'.format(district_code, block_code, index)
            villages.loc[village_index, 'Location_ID'] = full_id
            index = index + 1

    useful_columns = ['Location_ID', 'Village_Name', 'Block_Name', 'District_Name',
                      'Market_Frequency', 'Latitude', 'Longitude', ]
    villages.loc[:, useful_columns].to_csv("village_data.csv", index=False)
    villages.to_csv("village_master_file.csv", index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Extracts useful information village information from the '
                                     'demographic census and assigns each village a unique ID')
    parser.add_argument('village_file', type=str, help='The path to the CSV file of village markets with lat/lons.')
    parser.add_argument('id_file', type=str, help='The path to the CSV file of district/block names to numbers')
    args = parser.parse_args()

    villages = pd.read_csv(args.village_file)
    codes = pd.read_csv(args.id_file)

    main(villages, codes)
