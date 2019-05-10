import argparse
import pandas as pd


def main(villages):
    factories = pd.DataFrame(
        {
            'idcode': 'f_1' + villages.Location_ID.str[1:],
            'Name': villages.Village_Name.values,
        },
        columns=['idcode', 'Name'],
    )
    factories['Targets'] = '2' + factories['idcode'].str[3:]
    # Hard-code in the state-level imports before adding the consistent columns.
    factories = factories.append({'idcode': 'f_10000001',
                                  'Name': 'Aiginia_Imports',
                                  'Targets': '71905001', }, ignore_index=True)
    factories['Vaccines'] = 'All'
    factories['StartupLatencyDays'] = 0

    # Ensure weekly/daily production intervals are maintained and handle Aiginia Imports.
    production_intervals = []
    for village in villages.itertuples():
        if village.Market_Frequency == "Daily":
            production_intervals.append("1")
        else:
            production_intervals.append("7")
    factories['ProductionIntervalDays'] = pd.Series(production_intervals)
    factories.loc[factories['idcode'] == 'f_10000001', 'ProductionIntervalDays'] = 1
    factories['OverstockScale'] = 1
    factories['DemandType'] = 'Projection'
    factories.to_csv('factories.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Creates the factories.csv file using the village data file.')
    parser.add_argument('village_data_file', type=str,
                        help='The path to the input csv file of village markets data.')
    args = parser.parse_args()

    village_file = pd.read_csv(args.village_data_file, dtype=str)

    main(village_file)
