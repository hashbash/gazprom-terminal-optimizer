import pandas as pd
import models
import config
from simulator import NaiveSimulator


def main():
    df = pd.read_excel('static/terminal_data_hackathon v4.xlsx',
                       sheet_name='Incomes', engine='openpyxl')
    dt_columns = df.columns[2:]
    init_remain_df = df[['TID', 'остаток на 31.08.2022 (входящий)']]

    terminal_list = [models.Terminal(tid=x['TID'],
                                     remain=x['остаток на 31.08.2022 (входящий)'])
                     for x in init_remain_df.to_dict('records')]
    simulator = NaiveSimulator(collection_limit=500, collection_price=config.COLLECTION_PRICE,
                               funding_rate=config.FUNDING_RATE,
                               truck_expenses=config.DAILY_EXPENSES_PER_TRUCK,
                               terminals_list=terminal_list, dt_list=dt_columns, data=df)
    simulator.calculate()


if __name__ == '__main__':
    main()
