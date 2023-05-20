import pandas as pd
from pandas_profiling import ProfileReport


def main():
    df = pd.read_excel('../static/terminal_data_hackathon v4.xlsx',
                       sheet_name='Incomes', engine='openpyxl')
    df.drop(df.columns[list(range(10, len(df.columns)))], axis=1, inplace=True)
    profile = ProfileReport(df)

    profile.to_file(output_file='report.html')


if __name__ == '__main__':
    main()
