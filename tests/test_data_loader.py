import unittest
from unittest.mock import patch, mock_open, MagicMock
from core.data_loader import *


class TestJsonLoader(unittest.TestCase):
    @patch.object(JsonLoader, 'get_json')
    def test_get_json(self, mock_get_json):
        # Create a response from get_json
        expected_json = {"key": "value",
                         "key2": "value2",
                         "key3": "value3"}
        mock_get_json.return_value = expected_json
        #Create a JsonLoader object with any URL
        json_loader = JsonLoader("http://test_url.com")
        returned_json = json_loader.get_json()

        self.assertEqual(returned_json, expected_json)


class TestTradingPairsLoader(unittest.TestCase):
    @patch.object(JsonLoader, 'get_json')
    def test_get_pairs(self, mock_get_json):
        # Simulate the response returned by the exchange API
        mock_get_json.return_value = {
            "symbols": [
                {"symbol": "BTCUSDT", "status": "TRADING", "quoteAsset": "USDT"},
                {"symbol": "ETHBTC", "status": "TRADING", "quoteAsset": "BTC"},
                {"symbol": "SOLBTC", "status": "TRADING", "quoteAsset": "BTC"},
                {"symbol": "ETHUSDT", "status": "TRADING", "quoteAsset": "USDT"},
                {"symbol": "NEOBTC", "status": "BREAK", "quoteAsset": "BTC"},
                {"symbol": "WBTCBTC", "status": "TRADING", "quoteAsset": "BTC"}
            ]
        }
        # Creating a loader for BTC pairs
        trading_pairs_loader = TradingPairsLoader("http://test_url.com", "BTC")
        pairs = trading_pairs_loader.get_pairs()

        self.assertEqual(pairs, ["ETHBTC", "SOLBTC", "WBTCBTC"])


class TestTopLiquidLoader(unittest.TestCase):
    @patch.object(TradingPairsLoader, 'get_pairs')
    @patch('core.data_loader.requests.get')
    def test_get_top_liquid(self, mock_get_json, mock_get_pairs):
        # Set which pairs will be returned from get_pairs
        mock_get_pairs.return_value = ["ETHBTC", "SOLBTC", "WBTCBTC"]
        # set a json return from get_json
        mock_get_json.return_value.json.return_value  = [
            {"symbol": "ETHBTC", "quoteVolume": "1317.6979"},
            {"symbol": "SOLBTC", "quoteVolume": "791.9079"},
            {"symbol": "WBTCBTC", "quoteVolume": "444.7042"}
        ]
        # Creating a loader for the most liquid BTC pairs
        top_liquid_loader = TopLiquidLoader("http://test_url.com", "BTC")
        top_pair = top_liquid_loader.get_top_liquid("http://actual_trades_test_url.com", top_liquid_number=1)

        self.assertEqual(top_pair, [{"pair": "ETHBTC", "volume": 1317.6979}])


if __name__ == '__main__':
    unittest.main()