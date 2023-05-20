import pandas as pd
from pandas_profiling import ProfileReport


def main():
    incomes_raw_df = pd.read_excel('../static/terminal_data_hackathon v4.xlsx',
                                   sheet_name='Incomes', engine='openpyxl')
    profile = ProfileReport(incomes_raw_df)

    profile.to_file(output_file='report.html')


if __name__ == '__main__':
    main()
