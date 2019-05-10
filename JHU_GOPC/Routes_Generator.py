import argparse
import numpy as np
import pandas as pd

from utils import compute_distance as haversine

''' This code parses a file of Odisha Villages with lat/lons, blocks, and Hermes-accessible IDs to build a network of
    bi-directional supply chain routes. Distances are augmented by a Detour Index calculated elsewhere. 

    Runtime arguments: 
    village_data_file -- CSV file containing basic location and market data for villages within Odisha, India.
    wholesale_data_file -- CSV file containing data for wholesale markets within each district of Odisha, India. 
    retailer_data_file -- CSV file containing data for retailers within Odisha, India.  
    loc_id_dict -- CSV file containing location-based ID codes and route-per-VM info. 

    Output: 
    routes - CSV file containing data for each direction of a shipping route between locations. 
    '''


def main(villages, wholesales, retailers, loc_ids):
    route_columns = [
        'RouteName', 'idcode', 'LocName', 'Type', 'RouteOrder', 'TransitHours', 'DistanceKM', 'TruckType',
        'ShipIntervalDays',
        'PullOrderAmountDays', 'ShipLatencyDays', 'PerDiemType', 'PickupDelayFrequency', 'PickupDelayMagnitude',
        'PickupDelaySigma', 'Conditions', 'Notes',
    ]
    detour_index = 1.425

    # Add routes from village warehouses to village markets
    village_routes = []
    for village in villages.itertuples():
        route_name = 'wh2' + village.Location_ID[1:] + "_vm" + village.Location_ID
        start = {
            'RouteName': route_name,
            'idcode': '2' + village.Location_ID[1:],
            'LocName': 'wh_' + village.Village_Name,
            'Type': 'manifestpush',
            'RouteOrder': 0,
            'TransitHours': 0.001,
            'DistanceKM': 0,
            'TruckType': 'multi',
            'ShipLatencyDays': 0.2,
            'ShipIntervalDays': 1,
            'PullOrderAmountDays': 1,
            'PerDiemType': 'Std_PerDiem_None',
        }
        end = {
            'RouteName': route_name,
            'idcode': village.Location_ID,
            'LocName': 'vm_' + village.Village_Name,
            'Type': 'manifestpush',
            'RouteOrder': 1,
            'TransitHours': 0.001,
            'DistanceKM': 0,
            'TruckType': 'multi',
            'ShipLatencyDays': 0.2,
            'ShipIntervalDays': 1,
            'PullOrderAmountDays': 1,
            'PerDiemType': 'Std_PerDiem_None',
        }
        # Make specialized changes to these for Weekly markets
        if village.Market_Frequency == 'Weekly':
            start['ShipIntervalDays'] = 7
            start['PullOrderAmountDays'] = 7
            end['ShipIntervalDays'] = 7
            end['PullOrderAmountDays'] = 7
        village_routes.append(start)
        village_routes.append(end)
    farm_to_vm_routes = pd.DataFrame(village_routes)

    # Add routes from village markets to village market attached clinics
    village_to_clinic_routes = []
    for village in villages.itertuples():
        route_name = 'vm' + village.Location_ID + "_vc4" + village.Location_ID[1:]
        start = {
            'RouteName': route_name,
            'idcode': village.Location_ID,
            'LocName': 'vm_' + village.Village_Name,
            'Type': 'attached',
            'RouteOrder': 0,
            'TransitHours': '',
            'DistanceKM': '',
            'TruckType': '',
            'ShipLatencyDays': '',
            'ShipIntervalDays': '',
            'PullOrderAmountDays': '',
            'PerDiemType': '',
        }
        end = {
            'RouteName': route_name,
            'idcode': '4' + village.Location_ID[1:],
            'LocName': 'vc_' + village.Village_Name,
            'Type': 'attached',
            'RouteOrder': 1,
            'TransitHours': '',
            'DistanceKM': '',
            'TruckType': '',
            'ShipLatencyDays': '',
            'ShipIntervalDays': '',
            'PullOrderAmountDays': '',
            'PerDiemType': '',
        }
        village_to_clinic_routes.append(start)
        village_to_clinic_routes.append(end)
    vm_to_clinic_routes = pd.DataFrame(village_to_clinic_routes)

    # Add routes from villages to wholesales
    distances = haversine(
        villages["Latitude"].values,
        villages["Longitude"].values,
        wholesales["Latitude"].values,
        wholesales["Longitude"].values
    )
    min_distances = np.min(distances, axis=0)
    closest = np.argmin(distances, axis=0)
    wholesale_names = wholesales.iloc[closest[0, :]]["Wholesale_Name"].values
    wholesale_ids = wholesales.iloc[closest[0, :]]["Location_ID"].values

    vm_to_wholesale_routes = []
    vm_to_wholesale_data_iterator = zip(villages.itertuples(), wholesale_names, wholesale_ids, min_distances[0])

    # Each route must be created some X times to account for shipping quantities.
    for village, wholesale_name, wholesale_id, distance in vm_to_wholesale_data_iterator:
        # Find the district_block code and reference against loc_ids using village's Market Frequency.
        village_unique_code = "{}_{}".format(village.District_Name, village.Block_Name)
        if village.Market_Frequency == "Daily":
            num_routes = loc_ids.loc[loc_ids['Combo'] == village_unique_code, 'DailyRoutesPerVM'].values[0]
        else:
            num_routes = loc_ids.loc[loc_ids['Combo'] == village_unique_code, 'WeeklyRoutesPerVM'].values[0]

        # Then we loop some X number of times to create the route again and again.
        for route_num in range(num_routes):
            route_name = 'vm' + village.Location_ID + '_wm' + wholesale_id + '_{}'.format(route_num)
            transit_time = round(float(distance * detour_index) / 30.0, 3)  # 30 kmph
            if distance == 0:
                distance = 0.001
            if transit_time == 0:
                transit_time == 0.001
            start = {
                'RouteName': route_name,
                'idcode': village.Location_ID,
                'LocName': 'vm_' + village.Village_Name,
                'Type': 'schedpersistentfetch',
                'RouteOrder': 0,
                'TransitHours': transit_time,
                'DistanceKM': distance,
                'TruckType': '4wheel',
                'ShipLatencyDays': 0.291,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            end = {
                'RouteName': route_name,
                'idcode': wholesale_id,
                'LocName': 'wm_' + wholesale_name,
                'Type': 'schedpersistentfetch',
                'RouteOrder': 1,
                'TransitHours': transit_time,
                'DistanceKM': distance,
                'TruckType': '4wheel',
                'ShipLatencyDays': 0.291,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            # Make specialized changes to these for Weekly markets
            if village.Market_Frequency == 'Weekly':
                start['ShipIntervalDays'] = 7
                start['PullOrderAmountDays'] = 7
                end['ShipIntervalDays'] = 7
                end['PullOrderAmountDays'] = 7
            vm_to_wholesale_routes.append(start)
            vm_to_wholesale_routes.append(end)
    vm_to_wholesale_routes = pd.DataFrame(vm_to_wholesale_routes)

    # Add routes from wholesales to attached clinics
    wholesale_to_attached_clinic_routes = []
    for wholesale in wholesales.itertuples():
        route_name = 'wm' + wholesale.Location_ID + '_wc8' + wholesale.Location_ID[1:]
        start = {
            'RouteName': route_name,
            'idcode': wholesale.Location_ID,
            'LocName': 'wm_' + wholesale.Wholesale_Name,
            'Type': 'attached',
            'RouteOrder': 0,
            'TransitHours': '',
            'DistanceKM': '',
            'TruckType': '',
            'ShipLatencyDays': '',
            'ShipIntervalDays': '',
            'PullOrderAmountDays': '',
            'PerDiemType': '',
        }
        end = {
            'RouteName': route_name,
            'idcode': '8' + wholesale.Location_ID[1:],
            'LocName': 'wc_' + wholesale.Wholesale_Name,
            'Type': 'attached',
            'RouteOrder': 1,
            'TransitHours': '',
            'DistanceKM': '',
            'TruckType': '',
            'ShipLatencyDays': '',
            'ShipIntervalDays': '',
            'PullOrderAmountDays': '',
            'PerDiemType': '',
        }
        wholesale_to_attached_clinic_routes.append(start)
        wholesale_to_attached_clinic_routes.append(end)
    wholesale_to_attached_clinic_routes = pd.DataFrame(wholesale_to_attached_clinic_routes)

    # Add routes from wholesales to retailers
    wholesale_to_retail_routes = []
    for retailer in retailers.itertuples():
        route_name = 'wm{}_re{}'.format(retailer.Wholesaler_ID, retailer.ID)
        transit_time = round(float(retailer.Distance * detour_index) / 30.0, 3)  # 30 kmph
        start = {
            'RouteName': route_name,
            'idcode': retailer.ID,
            'LocName': 're_{}'.format(retailer.Name),
            'Type': 'schedvarfetch',
            'RouteOrder': 0,
            'TransitHours': transit_time,
            'DistanceKM': retailer.Distance,
            'TruckType': 'moto',
            'ShipLatencyDays': 0.5,
            'ShipIntervalDays': 1,
            'PullOrderAmountDays': 1,
            'PerDiemType': 'Std_PerDiem_None',
        }
        end = {
            'RouteName': route_name,
            'idcode': retailer.Wholesaler_ID,
            'LocName': 'wm_' + retailer.Wholesaler_Name,
            'Type': 'schedvarfetch',
            'RouteOrder': 1,
            'TransitHours': transit_time,
            'DistanceKM': retailer.Distance,
            'TruckType': 'moto',
            'ShipLatencyDays': 0.5,
            'ShipIntervalDays': 1,
            'PullOrderAmountDays': 1,
            'PerDiemType': 'Std_PerDiem_None',
        }
        wholesale_to_retail_routes.append(start)
        wholesale_to_retail_routes.append(end)
    wholesale_to_retail_routes = pd.DataFrame(wholesale_to_retail_routes)

    tier_ones = wholesales.loc[wholesales['Tier'] == 1]
    tier_twos = wholesales.loc[wholesales['Tier'] == 2]
    tier_threes = wholesales.loc[wholesales['Tier'] == 3]
    tier_nonthrees = wholesales.loc[wholesales['Tier'] != 3]
    wholesale_hierarchy_routes = []

    # First, we need to create bidirectional routes between all Tier 1 wholesalers.
    # Since we're doing a basic loop, each route will get two bidirectional loops.
    for one in tier_ones.itertuples():
        # So we get all the distances from a Tier 1 and all other Tier 1s...
        distances = haversine(one.Latitude, one.Longitude, tier_ones["Latitude"], tier_ones["Longitude"])
        for distance in distances:
            # Then we loop through and build routes for each Tier 1:1 connection that has a nonzero distance.
            where_index = np.where(distances == distance)[0][0]
            raw_distance = distance[0][0]

            # If nonzero distance, then we're not making a route from a wholesaler to itself.
            if raw_distance != 0:
                end_id = tier_ones.iloc[where_index]["Location_ID"]
                end_name = tier_ones.iloc[where_index]["Wholesale_Name"]
                route_name = 'wm{}_wm{}'.format(one.Location_ID, end_id)
                transit_time = round(float(raw_distance * detour_index) / 30.0, 3)  # 30 kmph

                start = {
                    'RouteName': route_name,
                    'idcode': one.Location_ID,
                    'LocName': 'wm_{}_wm_{}'.format(one.Wholesale_Name, end_name),
                    'Type': 'pull',
                    'RouteOrder': 0,
                    'TransitHours': transit_time,
                    'DistanceKM': raw_distance,
                    'TruckType': 'multi',
                    'ShipLatencyDays': 0.833,
                    'ShipIntervalDays': 1,
                    'PullOrderAmountDays': 1,
                    'PerDiemType': 'Std_PerDiem_None',
                }
                end = {
                    'RouteName': route_name,
                    'idcode': end_id,
                    'LocName': 'wm_{}_wm_{}_return'.format(one.Wholesale_Name, end_name),
                    'Type': 'pull',
                    'RouteOrder': 1,
                    'TransitHours': transit_time,
                    'DistanceKM': raw_distance,
                    'TruckType': 'multi',
                    'ShipLatencyDays': 0.833,
                    'ShipIntervalDays': 1,
                    'PullOrderAmountDays': 1,
                    'PerDiemType': 'Std_PerDiem_None',
                }
                wholesale_hierarchy_routes.append(start)
                wholesale_hierarchy_routes.append(end)

    # Next, each Tier 2 needs a bidirectional route with its closest Tier 1.
    # Since we aren't dealing with a uniform subset like Tier 1-1, we manually produce both route loops.
    for two in tier_twos.itertuples():
        distances = haversine(two.Latitude, two.Longitude, tier_ones["Latitude"], tier_ones["Longitude"])
        closest = np.argmin(np.ndarray.flatten(distances))
        raw_distance = distances[closest][0][0]

        # If nonzero distance, then we're not making a route from a wholesaler to itself.
        if raw_distance != 0:
            end_name = tier_ones.iloc[closest]['Wholesale_Name']
            end_id = tier_ones.iloc[closest]['Location_ID']
            route_name = 'wm{}_wm{}'.format(two.Location_ID, end_id)
            transit_time = round(float(raw_distance * detour_index) / 30.0, 3)  # 30 kmph

            # First we go from Tier 2 to Tier 1 and back.
            start = {
                'RouteName': route_name,
                'idcode': two.Location_ID,
                'LocName': 'wm_{}_wm_{}'.format(two.Wholesale_Name, end_name),
                'Type': 'pull',
                'RouteOrder': 0,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.833,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            end = {
                'RouteName': route_name,
                'idcode': end_id,
                'LocName': 'wm_{}_wm_{}_return'.format(two.Wholesale_Name, end_name),
                'Type': 'pull',
                'RouteOrder': 1,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.833,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            wholesale_hierarchy_routes.append(start)
            wholesale_hierarchy_routes.append(end)

            # Now we go from Tier 1 to Tier 2 and back.
            route_name = 'wm{}_wm{}'.format(end_id, two.Location_ID)
            start = {
                'RouteName': route_name,
                'idcode': end_id,
                'LocName': 'wm_{}_wm_{}'.format(end_name, two.Wholesale_Name),
                'Type': 'pull',
                'RouteOrder': 0,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.854,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            end = {
                'RouteName': route_name,
                'idcode': two.Location_ID,
                'LocName': 'wm_{}_wm_{}_return'.format(end_name, two.Wholesale_Name),
                'Type': 'pull',
                'RouteOrder': 1,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.854,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            wholesale_hierarchy_routes.append(start)
            wholesale_hierarchy_routes.append(end)

    # Finally, each Tier 3 needs a bidirectional route with its closest Tier 1 OR 2, hence tier_nonthrees.
    # We still manually produce both bidirectional loops.
    for three in tier_threes.itertuples():
        distances = haversine(three.Latitude, three.Longitude, tier_nonthrees["Latitude"], tier_nonthrees["Longitude"])
        closest = np.argmin(np.ndarray.flatten(distances))
        raw_distance = distances[closest][0][0]

        # If nonzero distance, then we're not making a route from a wholesaler to itself.
        if raw_distance != 0:
            end_name = tier_nonthrees.iloc[closest]['Wholesale_Name']
            end_id = tier_nonthrees.iloc[closest]['Location_ID']
            route_name = 'wm_{}_wm_{}'.format(three.Location_ID, end_id)
            transit_time = round(float(raw_distance * detour_index) / 30.0, 3)  # 30 kmph

            # First we go from Tier 3 to Tier 1/2 and back.
            start = {
                'RouteName': route_name,
                'idcode': three.Location_ID,
                'LocName': 'wm_{}_wm_{}'.format(three.Wholesale_Name, end_name),
                'Type': 'pull',
                'RouteOrder': 0,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.833,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            end = {
                'RouteName': route_name,
                'idcode': end_id,
                'LocName': 'wm_{}_wm_{}_return'.format(three.Wholesale_Name, end_name),
                'Type': 'pull',
                'RouteOrder': 1,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.833,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            wholesale_hierarchy_routes.append(start)
            wholesale_hierarchy_routes.append(end)

            # Now we go from Tier 1/2 to Tier 3 and back.
            route_name = 'wm_{}_wm_{}'.format(end_id, three.Location_ID)
            start = {
                'RouteName': route_name,
                'idcode': end_id,
                'LocName': 'wm_{}_wm_{}'.format(end_name, three.Wholesale_Name),
                'Type': 'pull',
                'RouteOrder': 0,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.854,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            end = {
                'RouteName': route_name,
                'idcode': three.Location_ID,
                'LocName': 'wm_{}_wm_{}_return'.format(end_name, three.Wholesale_Name),
                'Type': 'pull',
                'RouteOrder': 1,
                'TransitHours': transit_time,
                'DistanceKM': raw_distance,
                'TruckType': 'multi',
                'ShipLatencyDays': 0.854,
                'ShipIntervalDays': 1,
                'PullOrderAmountDays': 1,
                'PerDiemType': 'Std_PerDiem_None',
            }
            wholesale_hierarchy_routes.append(start)
            wholesale_hierarchy_routes.append(end)

    wholesale_to_wholesale_routes = pd.DataFrame(wholesale_hierarchy_routes)

    # Combine all routes and fill in the common column values
    routes = pd.concat([farm_to_vm_routes,
                        vm_to_clinic_routes,
                        vm_to_wholesale_routes,
                        wholesale_to_attached_clinic_routes,
                        wholesale_to_retail_routes,
                        wholesale_to_wholesale_routes], ignore_index=True)
    routes['PickupDelayFrequency'] = ''
    routes['PickupDelayMagnitude'] = ''
    routes['PickupDelaySigma'] = ''
    routes['Conditions'] = ''
    routes['Notes'] = ''
    routes[route_columns].to_csv('routes.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Produces the routes file using village and wholesale data')
    parser.add_argument('village_data_file', type=str, help='The path to the input csv file of village markets data.')
    parser.add_argument('wholesale_data_file', type=str,
                        help='The path to the input csv file of the wholesale market data.')
    parser.add_argument('retailer_data_file', type=str,
                        help='The path to the input csv file of the retailer data.')
    parser.add_argument('loc_id_file', type=str,
                        help='The path to the csv file containing location-based ID codes and route-per-VM info.')
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
        }
    )
    wholesales = pd.read_csv(
        args.wholesale_data_file,
        dtype={
            'Location_ID': str,
            'Wholesale_Name': str,
            'District_Name': str,
            'Longitude': float,
            'Latitude': float,
        }
    )
    retailers = pd.read_csv(args.retailer_data_file)
    loc_ids = pd.read_csv(args.loc_id_file)

    main(villages, wholesales, retailers, loc_ids)
