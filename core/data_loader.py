import os
import pandas as pd
import zipfile
import requests
import logging
from io import BytesIO


class JsonLoader:
    """JsonLoader class return a json response based on the given url."""
    def __init__(self, url):
        self.url = url

    def get_json(self, path=None):
        url = path if path is not None else self.url
        response = requests.get(url)

        return response.json()


class TradingPairsLoader(JsonLoader):
    """TradingPairsLoader class extends JsonLoader with the ability to form a list of trading pairs."""
    def __init__(self, url, quote_asset):
        super().__init__(url)
        self.quote_asset = quote_asset

    def get_pairs(self):
        pairs = []
        data = self.get_json()

        for symbol in data['symbols']:
            if symbol['quoteAsset'] == self.quote_asset and symbol['status'] == "TRADING":
                pairs.append(symbol['symbol'])

        return pairs


class TopLiquidLoader(TradingPairsLoader):
    """TopLiquidLoader class extends TradingPairsLoader with the ability to form a list of the most liquid trading pairs
       based on last 24 hours."""
    def __init__(self, url, quote_asset):
        super().__init__(url, quote_asset)
        self.quote_asset = quote_asset

    def get_top_liquid(self, actual_trades_url, top_liquid_number=100):
        # Get all quoteAsset trading pairs
        trading_pairs = self.get_pairs()
        # Get all quoteAsset trading pairs with volumes for the last 24 hours
        all_24h_data = self.get_json(actual_trades_url)
        actual_pairs_volumes = [
            {"pair": ticker['symbol'], "volume": float(ticker['quoteVolume'])}
            for ticker in filter(lambda ticker: ticker['symbol'] in trading_pairs, all_24h_data)
        ]
        # Sort all trading pairs from highest to lowest volume
        actual_pairs_volumes.sort(key=lambda ticker: ticker['volume'], reverse=True)

        return actual_pairs_volumes[:top_liquid_number]


class CsvLoader():
    """CsvLoader class downloads the needed archive with OHLCV information and unzip it."""
    DATA_DIR = "data"

    def __init__(self, base_ohlcv_url):
        self.base_ohlcv_url = base_ohlcv_url
        os.makedirs(self.DATA_DIR, exist_ok=True)

    def download_ohlcv_zip(self, pair, ohlcv_period, year_month):
        download_url = f"{self.base_ohlcv_url}{pair}/{ohlcv_period}/{pair}-{ohlcv_period}-{year_month}.zip"
        path_to_zip = os.path.join(self.DATA_DIR, f"{pair}_{year_month}.zip")

        try:
            with requests.get(download_url) as r:
                r.raise_for_status()
                with open(path_to_zip, 'wb') as f:
                    f.write(r.content)
        except requests.exceptions.RequestException as e:
            print(f"Error while downloading zip for {pair}: {e}")
        except Exception as e:
            print(f"Error while saving zip for {pair}: {e}")

        return path_to_zip

    def extract_ohlcv_zip(self, pair, ohlcv_period, year_month):
        path_to_zip = self.download_ohlcv_zip(pair, ohlcv_period, year_month)

        try:
            with zipfile.ZipFile(path_to_zip, 'r') as zf:
                zf.extractall(self.DATA_DIR)
        except zipfile.BadZipFile:
            print(f"Error: {path_to_zip} is not a correct ZIP archive.")

        os.remove(path_to_zip)

        return os.path.join(self.DATA_DIR, f"{pair}-{ohlcv_period}-{year_month}.csv")


class DataLoader():
    """DataLoader class loads data for all trading pairs and combines them into a single DataFrame.
       Information about all steps is saved in the log file."""
    DATA_DIR = "data"
    LOG_FILE = "data/data_loader.log"

    def __init__(self, pairs_csv_paths):
        self.pairs_csv_paths = pairs_csv_paths
        self._logging_setup()

    def _logging_setup(self):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        logging.basicConfig(filename=self.LOG_FILE, level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("DataLoader initialized.")

    def create_parquet(self, parquet_name):
        data_frames_list = []

        for csv_path in self.pairs_csv_paths:
            try:
                # Loading CSV into pandas DataFrame
                data_frame = pd.read_csv(csv_path, header=None,
                                 names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                        'taker_buy_quote_asset_volume', 'ignore'])

                logging.info(f"Successfully loaded {csv_path}.")

                # Data integrity check for mandatory columns
                mandatory_columns_mask = data_frame[['timestamp', 'open', 'high', 'low', 'close', 'volume']].isnull()
                if mandatory_columns_mask.any().any():
                    logging.warning(f"Warning: Missing values found in {csv_path}, skipping.")
                    continue

                # Adding a DataFrame to the list
                data_frames_list.append(data_frame)

            except Exception as e:
                logging.error(f"Error loading {csv_path}: {e}")
                continue

        if not data_frames_list:
            logging.error("Exit - no valid data to process.")
            return None

        # Merge all DataFrames into one
        merged_data_frames = pd.concat(data_frames_list, ignore_index=True)
        # Save the merged DataFrame as a parquet file with compression
        path_to_parquet = os.path.join(self.DATA_DIR, f"{parquet_name}.parquet")
        merged_data_frames.to_parquet(path_to_parquet, compression='snappy')

        logging.info(f"Data successfully merged and saved to {path_to_parquet}.")

        return merged_data_frames
