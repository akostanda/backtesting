import os
import shutil
import unittest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock
from core.backtester import Backtester


class TestBacktester(unittest.TestCase):

    def setUp(self):
        # Create a frame of 1440 (24 hours in minutes) lines with close prices in increasing tendency
        self.price_data = pd.DataFrame({
            "close": [0.03 + i * 0.0001 for i in range(1440)],
            'signal': np.random.choice([0, 1], size=1440, p=[0.95, 0.05])
        })
        # Create metrics that a strategy can return
        self.metrics = {
            'total_return': 10.98,
            'sharpe_ratio':0.015,
            'max_drawdown': -0.5,
            'winrate': 0.13,
            'expectancy': 0.003,
            'exposure_time': 0.0004
        }
        # Create mock strategy
        self.mock_strategy = MagicMock()
        self.mock_strategy.get_metrics.return_value = self.metrics
        self.mock_strategy.run_backtest.return_value = None
        # Create a Backtester object
        self.backtester = Backtester(self.price_data, self.mock_strategy)

        # Clean the output directory before testing
        if os.path.exists("results"):
            shutil.rmtree("results")

    def test_get_backtest_results(self):
        metrics, result = self.backtester.get_backtest_results()

        # Test the metrics return
        self.assertEqual(metrics, self.metrics)
        # Test if csv file was created
        self.assertTrue(os.path.exists(os.path.join("results", "metrics.csv")))
        # Test if portfolio total_return is float
        self.assertIsInstance(result, float)


if __name__ == '__main__':
    unittest.main()