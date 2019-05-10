import argparse
import math
import numpy as np
import pandas as pd

from utils import compute_distance as haversine

''' This code generates a list of stores given a list of villages and wholesalers. 
    NOTE: The wholesaler file MUST include Population_Served, by running code with "GeoRasterViewer Agrifood Prep.ipynb"

    Runtime arguments: 
    village_file -- CSV containing data on villages and the populations they serve within the region.
    wholesale_file -- CSV containing data on wholesalers and the populations they serve within the region.
    retailer_file -- CSV containing data on retailers and the populations they serve within the region.
    loc_id_dict -- CSV file containing location-based ID codes and route-per-VM info. 

    Output: 
    stores -- CSV consolidating farms, village markets, wholesales, retailers, and attached clinics.     
    '''


def main(village_data, wholesale_data, retailer_data, loc_ids):
    stores_columns = [
        'idcode', 'NAME', 'CATEGORY', 'FUNCTION', 'Device Utilization Rate', 'UseVialsLatency', 'UseVialsInterval',
        'Latitude', 'Longitude', 'OdishaPop', 'SiteCostPerYear', 'SiteCostCur', 'SiteCostBaseYear', 'Inventory', 'Notes',
        'ExportPotPop', 'ExportOnPop', 'ExportTomPop', 'ExportBrPop', 'ExportCabPop', 'BufferStockFraction'
    ]
    farms = pd.DataFrame(columns=stores_columns)
    village_markets = pd.DataFrame(columns=stores_columns)
    villages_attached = pd.DataFrame(columns=stores_columns)
    wholesales = pd.DataFrame(columns=stores_columns)
    wholesale_attached = pd.DataFrame(columns=stores_columns)
    retailers = pd.DataFrame(columns=stores_columns)

    # Variables for easy research scenario generation!, deviate from Empty Strings to add cold storage to VM/WM.
    file_bookend = ''
    for_vm_inv = ''
    for_wm_inv = ''

    # Farms/Warehouses
    farms['idcode'] = '2' + village_data.Location_ID.str[1:]
    farms['NAME'] = 'wh_' + village_data.Village_Name
    farms['CATEGORY'] = 'Farm'
    farms['FUNCTION'] = 'Distribution'
    farms['UseVialsLatency'] = 0
    farms['OdishaPop'] = ''
    farms['Inventory'] = 'fake_fridge+multi'
    farms['SiteCostPerYear'] = 0
    farms['UseVialsInterval'] = ''
    farms['BufferStockFraction'] = 0

    # Village Markets
    village_markets['idcode'] = village_data.Location_ID
    village_markets['NAME'] = 'vm_' + village_data.Village_Name
    village_markets['CATEGORY'] = 'VillageMarket'
    village_markets['FUNCTION'] = 'Distribution'
    village_markets['UseVialsLatency'] = 0
    village_markets['OdishaPop'] = ''
    village_markets['Inventory'] = 'fake_fridge+trader+3*laborer+driver' + for_vm_inv
    village_markets['SiteCostPerYear'] = 20000
    village_markets['UseVialsInterval'] = ''
    village_markets['BufferStockFraction'] = 0

    # Handle the Daily(1) vs Weekly(7) UseVialsInterval for Weekly VMs/Warehouses
    use_vials_interval = []
    for village in village_data.itertuples():
        if village.Market_Frequency == "Weekly":
            use_vials_interval.append("7")
        else:
            use_vials_interval.append("1")
    farms['UseVialsInterval'] = use_vials_interval
    village_markets['UseVialsInterval'] = use_vials_interval

    # Village Markets Attached Clinics
    villages_attached['idcode'] = '4' + village_data.Location_ID.str[1:]
    villages_attached['NAME'] = 'vc_' + village_data.Village_Name
    villages_attached['CATEGORY'] = 'Retail'
    villages_attached['FUNCTION'] = 'Surrogate'
    villages_attached['UseVialsLatency'] = 0.25
    villages_attached['OdishaPop'] = ''
    villages_attached['Inventory'] = ''
    villages_attached['SiteCostPerYear'] = 0
    villages_attached['UseVialsInterval'] = 1
    villages_attached['BufferStockFraction'] = ''

    # Handle the 5% calculation.
    vc_pop_served = []
    for village in village_data.itertuples():
        if village.Population_Served == 0:
            vc_pop_served.append(1)
        else:
            vc_pop_served.append(0.05 * float(village.Population_Served))
    villages_attached['OdishaPop'] = vc_pop_served

    # Village markets lat/lons
    for i, village in enumerate(villages.itertuples()):
        latitude = village.Latitude
        longitude = village.Longitude
        farms.at[i, 'Latitude'] = latitude
        farms.at[i, 'Longitude'] = longitude
        village_markets.at[i, 'Latitude'] = latitude
        village_markets.at[i, 'Longitude'] = longitude
        villages_attached.at[i, 'Latitude'] = latitude
        villages_attached.at[i, 'Longitude'] = longitude

    # Wholesales
    wholesales['idcode'] = wholesale_data.Location_ID
    wholesales['NAME'] = 'wm_' + wholesale_data.Wholesale_Name
    wholesales['CATEGORY'] = 'Wholesale'
    wholesales['FUNCTION'] = 'Distribution'
    wholesales['UseVialsLatency'] = 0
    wholesales['Latitude'] = wholesale_data.Latitude
    wholesales['Longitude'] = wholesale_data.Longitude
    wholesales['OdishaPop'] = ''
    wholesales['Inventory'] = ''
    wholesales['SiteCostPerYear'] = 200000
    wholesales['UseVialsInterval'] = 1
    wholesales['BufferStockFraction'] = 0

    # Assigns trucks to wholesale's inventory based on how many trucks are allocated to the block, rounded up.
    wholesale_inventory = []
    wholesale_data['Code'] = wholesale_data['District_Name'] + "_" + wholesale_data['Block_Name']
    code_counts = wholesale_data.groupby('Code').size().to_dict()
    for wholesale in wholesale_data.itertuples():
        code = '{}_{}'.format(wholesale.District_Name, wholesale.Block_Name)
        trucks_per_block = loc_ids.loc[loc_ids['Combo'] == code, 'TrucksPerBlock'].values[0]
        wm_per_block = code_counts[code]
        trucks_for_wholesale = math.ceil(trucks_per_block / wm_per_block)
        if trucks_for_wholesale == 0:
            trucks_for_wholesale = 1
        wholesale_inventory.append(
            'fake_fridge+{}*4wheel+221*multi+trader+30*laborer+5*officestaff+driver{}'.format(trucks_for_wholesale,
                                                                                              for_wm_inv))
    wholesales['Inventory'] = wholesale_inventory

    # Wholesale Attached Clinics
    wholesale_attached['idcode'] = '8' + wholesale_data.Location_ID.str[1:]
    wholesale_attached['NAME'] = 'wc_' + wholesale_data.Wholesale_Name
    wholesale_attached['CATEGORY'] = 'Retail'
    wholesale_attached['FUNCTION'] = 'Surrogate'
    wholesale_attached['UseVialsLatency'] = 0.375
    wholesale_attached['Latitude'] = wholesale_data.Latitude
    wholesale_attached['Longitude'] = wholesale_data.Longitude
    wholesale_attached['OdishaPop'] = ''
    wholesale_attached['Inventory'] = ''
    wholesale_attached['SiteCostPerYear'] = 0
    wholesale_attached['UseVialsInterval'] = 1
    wholesale_attached['BufferStockFraction'] = ''

    # Need to handle Pop Served based off whether Wholesale Attached is within testing region or not.
    # 5% of Population Served if within testing region, otherwise 100%.
    # Distance is hard-coded in as Bhadrak region's centerpoint: 21.0583 lat, 86.4658 lon, 34.0 km radius
    wc_pop_served = []
    for wholesale in wholesale_data.itertuples():
        distance = np.ndarray.flatten(haversine(wholesale.Latitude, wholesale.Longitude, 21.0583, 86.4658))
        if distance <= 34.0:
            wc_pop_served.append(0.05 * float(wholesale.Population_Served))
        else:
            wc_pop_served.append(wholesale.Population_Served)
    wholesale_attached['OdishaPop'] = wc_pop_served

    # Retailers
    retailers['idcode'] = retailer_data.ID
    retailers['NAME'] = 're_Retailer' + retailer_data.Name
    retailers['CATEGORY'] = 'Retail'
    retailers['FUNCTION'] = 'Administration'
    retailers['UseVialsLatency'] = 0.583
    retailers['Latitude'] = retailer_data.Latitude
    retailers['Longitude'] = retailer_data.Longitude
    retailers['OdishaPop'] = retailer_data.Population_Served
    retailers['Inventory'] = 'fake_fridge+moto+trader+laborer+driver'
    retailers['SiteCostPerYear'] = 2000
    retailers['UseVialsInterval'] = 1
    retailers['BufferStockFraction'] = 0

    # Some columns can be filled in for everything at the end
    stores = pd.concat([farms,
                        village_markets,
                        villages_attached,
                        wholesales,
                        wholesale_attached,
                        retailers],
                       ignore_index=True)
    stores['Device Utilization Rate'] = 1
    stores['SiteCostCur'] = 'INR'
    stores['SiteCostBaseYear'] = 2018
    stores['Notes'] = ''
    stores['ExportPotPop'] = 0
    stores['ExportOnPop'] = 0
    stores['ExportTomPop'] = 0
    stores['ExportBrPop'] = 0
    stores['ExportCabPop'] = 0
    stores[stores_columns].to_csv('odisha_stores{}.csv'.format(file_bookend), index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Creates the stores.csv file using the village and wholesale data.')
    parser.add_argument('village_data_file', type=str,
                        help='The path to the input csv file of village markets data.')
    parser.add_argument('wholesale_data_file', type=str,
                        help='The path to the input csv file of the wholesale market data.')
    parser.add_argument('retailer_data_file', type=str,
                        help='The path to the input csv file of the retailer data.')
    parser.add_argument('loc_id_file', type=str,
                        help='The path to the csv file containing location-based ID codes and Trucks-Per-Block info.')
    args = parser.parse_args()

    villages = pd.read_csv(args.village_data_file, dtype=str)
    wholesalers = pd.read_csv(
        args.wholesale_data_file,
        dtype={
            'Location_ID': str,
            'Name': str,
            'District_Name': str,
            'Longitude': float,
            'Latitude': float,
            'Population_Served': float,
        }
    )

    retailers = pd.read_csv(
        args.retailer_data_file,
        dtype={
            'Location_ID': str,
            'Name': str,
            'Latitude': float,
            'Longitude': float,
            'Urbanicity': int,
            'Closest Wholesaler': str,
            'Wholesaler Name': str,
            'Distance': float,
            'Population_Served': float,
        }
    )
    loc_ids = pd.read_csv(args.loc_id_file)

    main(villages, wholesalers, retailers, loc_ids)

