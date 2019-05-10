import argparse
import calendar

import pandas as pd

''' This code parses a file of Odisha Villages with lat/lons, blocks, and Hermes-accessible IDs to build a list of 
    produce shipping details based upon production and seasonality data. 

    Runtime arguments: 
    village_data_file -- CSV file containing basic location and market data for villages within Odisha, India.
    block_production_file -- CSV file containing data on produce quantities from each block in Odisha. 
    seasonality_file -- CSV denoting whether given produce items are in season at each month.  

    Output: 
    manifest - CSV file containing produce shipment/market data for each village in Odisha. 
    '''


def main(villages, block_production, seasonality):
    # Modify beyond 1.0 and empty string to handle multiplying factors for Production Surplus/Deficit.
    multiplying_factor = 1.0
    scenario = ''

    factory_manifests = []
    villages_per_block = villages.groupby('Block_Name').size().to_dict()

    # Create the year data to handle Daily and Weekly Markets
    year_range = pd.date_range(start='1/1/2019', end='12/28/2019')
    year = year_range.to_frame(index=False)

    year["Month"] = year_range.month
    year["Days"] = year_range.day
    # Remove any days numbered 29, 30, 31 and reset the index to accommodate the missing rows
    year = year[(year.Days <= 28)]
    year = year.reset_index(drop=True)
    # Manually set the Weekday using the index
    year["Weekdays"] = year.index % 7
    # Deliveries must be bumped to X.1 to X.2 since time 0.0 breaks HERMES
    year["Start_Days"] = year.index + 0.1
    year["End_Days"] = year["Start_Days"] + 0.1

    months = calendar.month_abbr[1:]
    manifest_columns = ['RouteId', 'StartDay', 'EndDay', 'Month',
                        'Potato', 'Onion', 'Tomato', 'Brinjal', 'Cabbage', 'Notes']

    mondays = year.loc[year["Weekdays"].values == 0]

    progress = 0
    for village in villages.itertuples():
        # get the village's unique district_block search text
        # then get overall block production amounts for the year and if there's nothing, don't add to manifest
        block = village.Block_Name
        search = "{}_{}".format(village.District_Name, block)

        # "Cuttack_Cuttack Sadar" has VMs but no production, "Cuttack_Cuttack" has production but no VMs, so combine.
        if search == "Cuttack_Cuttack Sadar":
            village_production = block_production.loc[block_production['Combo'] == "Cuttack_Cuttack"]
        else:
            village_production = block_production.loc[block_production['Combo'] == search]

        # Setup the DataFrame for this village and the set of days it's shipping on
        factory_manifest = pd.DataFrame(columns=manifest_columns)

        # empty DFs (no shipping) can't be processed normally, must be manually set to 0 across all produce columns
        if village_production.empty:
            factory_manifest["Potato":"Cabbage"] = 0.0
        else:
            # setup the days the village is shipping on
            if village.Market_Frequency == 'Daily':
                # all days
                days = year
            else:  # Weekly
                # Only Mondays
                days = mondays

            # attach list of this village's market days to factory manifest- this is what makes this file huge
            factory_manifest['StartDay'] = days["Start_Days"]
            factory_manifest['EndDay'] = days["End_Days"]
            factory_manifest['Month'] = days["Month"]

            # get breakdowns of number of village market days by month
            sale_days_by_month = days['Month'].value_counts()

            # go product by product and then month by month to fill in the data one column at a time
            for product in ["Potato", "Onion", "Tomato", "Brinjal", "Cabbage"]:
                # get a dataframe of what's available each month and a list to hold the data
                seasonal_year = seasonality.loc[product, 'Jan':'Dec']
                produce_production = []

                for month in months:
                    # figure out if peak/lean/off and only do production calculations if peak/lean, get month sales
                    availability = seasonal_year[month]
                    daily_production = 0.0
                    month_index = months.index(month) + 1
                    monthly_market_days = sale_days_by_month[month_index]

                    if availability != 'off':
                        # then grab the total production per month and prune it down for the single market & day
                        production_column = "{}_{}".format(product, availability)
                        production_per_month = village_production[production_column].values[0]
                        daily_production_fraction = 1 / (villages_per_block[block] * monthly_market_days)
                        daily_production = daily_production_fraction * production_per_month * multiplying_factor

                    # and now we append the value some X times based on how many days this month the market is running
                    produce_production.append([daily_production] * monthly_market_days)

                # flatten the nested list into something we can incorporate into the village's manifest
                flat_production = [item for monthly in produce_production for item in monthly]
                factory_manifest[product] = flat_production

        # set the Route_ID and then append to list of manifests
        factory_manifest['RouteId'] = 'wh2' + village.Location_ID[1:] + "_vm" + village.Location_ID
        factory_manifests.append(factory_manifest)
        print("complete: {}, {} of {}".format(village.Village_Name, progress+1, len(villages)))
        progress += 1

    # Now we add Aiginia Imports to the manifest using a daily market schedule and the same algorithm as before.
    import_days = year
    import_production = block_production.loc[block_production['Combo'] == "Aiginia_Imports"]
    import_manifest = pd.DataFrame(columns=manifest_columns)
    import_manifest['StartDay'] = import_days["Start_Days"]
    import_manifest['EndDay'] = import_days["End_Days"]
    import_manifest['Month'] = import_days["Month"]

    # get breakdowns of number of village market days by month
    import_days_by_month = import_days['Month'].value_counts()

    # go product by product and then month by month to fill in the data one column at a time
    for product in ["Potato", "Onion", "Tomato", "Brinjal", "Cabbage"]:
        # get a dataframe of what's available each month and a list to hold the data
        seasonal_year = seasonality.loc[product, 'Jan':'Dec']
        produce_production = []

        for month in months:
            # figure out if peak/lean/off and get month sales
            availability = seasonal_year[month]
            month_index = months.index(month) + 1
            monthly_market_days = import_days_by_month[month_index]

            # then grab the total production per month and prune it down for the single market & day
            # unlike with the block production, we're calculating regardless of peak/lean/off
            production_column = "{}_{}".format(product, availability)
            production_per_month = import_production[production_column].values[0]
            daily_production_fraction = 1 / monthly_market_days  # Only one importing location!
            daily_production = daily_production_fraction * production_per_month

            # and now we append the value some X times based on how many days this month the market is running
            produce_production.append([daily_production] * monthly_market_days)

        # flatten the nested list into something we can incorporate into the village's manifest
        flat_production = [item for monthly in produce_production for item in monthly]
        import_manifest[product] = flat_production

    # set the Route_ID and then append to list of manifests
    import_manifest['RouteId'] = 'f10000001_wm71905002'
    factory_manifests.append(import_manifest)

    # consolidate list of manifests, set notes to blank string, and write to file
    manifest = pd.concat(factory_manifests, ignore_index=True)
    manifest['Notes'] = ''
    manifest = manifest.drop(columns=['Month'])
    manifest.to_csv('odisha_manifest{}.csv'.format(scenario), index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Creates the manifest.csv file using the factories '
                                     'and a mapping of blocks to production amounts.')
    parser.add_argument('village_data_file', type=str,
                        help='The path to the input csv file of village markets IDs.')
    parser.add_argument('block_production_file', type=str,
                        help='The path to the input csv file of block production amounts.')
    parser.add_argument('seasonality_file', type=str,
                        help='The path to the input csv file of seasonal produce availability.')
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
    block_production = pd.read_csv(
        args.block_production_file,
        dtype={
            'District_Name': str,
            'Block_Name': str,
            'Search': str,
            'Potato_Tons': float,
            'Onion_Tons': float,
            'Tomato_Tons': float,
            'Cabbage_Tons': float,
            'Brinjal_Tons': float,
        },
    )
    seasonality = pd.read_csv(
        args.seasonality_file,
        index_col=0,
    )

    main(villages, block_production, seasonality)
