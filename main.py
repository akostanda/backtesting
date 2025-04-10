import core.backtester as bt
import core.data_loader as dl
import strategies.sma_cross as sma


def main():
    try:
        # Get the list of 100 the most liquid trading pairs for the last 24 hours
        top_liqui_obg = dl.TopLiquidLoader("https://api.binance.com/api/v3/exchangeInfo", "BTC")
        pairs = top_liqui_obg.get_top_liquid("https://api.binance.com/api/v3/ticker/24hr")

        if not pairs:
            raise ValueError("No trading pairs found!")

        # Download and unpack zips with OHLCV information for a certain period,
        # extract all csv files anf create a list with paths to them
        pairs_csv_paths = []
        csv_loader_obj = dl.CsvLoader("https://data.binance.vision/data/spot/monthly/klines/")

        for pair in pairs:
            try:
                path = csv_loader_obj.extract_ohlcv_zip(pair['pair'], "1m", "2025-02")
                pairs_csv_paths.append(path)
            except Exception as e:
                print(f"The {pair['pair']} wasn't downloaded: {e}")

        if not pairs_csv_paths:
            raise ValueError("No CSV files were downloaded!")

        # Get the data frame and create a parquet file with all pairs information
        data_loader_obj = dl.DataLoader(pairs_csv_paths)
        merged_data = data_loader_obj.create_parquet('btc_1m_feb25')

        if merged_data is None or merged_data.empty:
            raise ValueError("The Data Frame is empty or wasn't created!")

        # Create a SNA Crossover strategy object
        sma_obj = sma.SmaCrossover(merged_data)

        # Get results of backtest
        backtester_obj = bt.Backtester(merged_data, sma_obj)
        backtester_obj.get_backtest_results()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()