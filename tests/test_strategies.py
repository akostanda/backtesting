import os
import unittest
import pandas as pd
from strategies.sma_cross import SmaCrossover


class TestSmaCrossoverStrategy(unittest.TestCase):
    def setUp(self):
        # Create a frame of 1440 (24 hours in minutes) lines with close prices in increasing tendency
        self.price_data = pd.DataFrame({
            "close": [0.03 + i * 0.0001 for i in range(1440)]
        })
        self.strategy = SmaCrossover(self.price_data, short_window=30, long_window=80, volatility_window=10)

    def test_generate_signals(self):
        signals = self.strategy.generate_signals()

        # Test if the columns are created
        self.assertIn("signal", signals.columns)
        self.assertIn("position", signals.columns)

        # Test the correspondence between the signal column change and the position column
        for index in range(30, len(signals) - 1):
            previous_signal = signals.iloc[index - 1]["signal"]
            current_signal = signals.iloc[index]["signal"]
            next_position = signals.iloc[index + 1]["position"]

            if previous_signal == 0 and current_signal == 1:
                self.assertEqual(next_position, 1, f"Expected position equal 1 at index {index + 1} after signal "
                                                   f"was changed from 0 to 1 at index {index}, but have {next_position}")
            elif previous_signal == 1 and current_signal == 0:
                self.assertEqual(next_position, -1, f"Expected position equal -1 at index {index + 1} after signal "
                                                   f"was changed from 1 to 0 at index {index}, but have {next_position}")

    def test_run_backtest(self):
        backtest = self.strategy.run_backtest()

        # Test if the columns are created
        self.assertIn("sma_short", backtest.columns)
        self.assertIn("sma_long", backtest.columns)
        # Test if the curve was saved
        self.assertTrue(os.path.exists("results/screenshots/sma_curve.png"), "SMA curve png should be created")

    def test_get_metrics(self):
        metrics = self.strategy.get_metrics()
        expected_keys = [
            "total_return", "sharpe_ratio", "max_drawdown",
            "winrate", "expectancy", "exposure_time"
        ]

        for key in expected_keys:
            self.assertIn(key, metrics)
            self.assertIsInstance(metrics[key], float)

        # Prices are rising, so the metrics should correspond to the ranges below
        self.assertGreater(metrics["total_return"], 0, "Total return must be positive")
        self.assertGreater(metrics["sharpe_ratio"], 0, "Sharpe ratio Totmust be positive")
        self.assertLessEqual(metrics["max_drawdown"], 0, "Max drawdown must be negative or zero")
        self.assertTrue(0 <= metrics["winrate"] <= 1, "Winrate must be within [0, 1]")
        self.assertTrue(0 <= metrics["exposure_time"] <= 1, "Exposure time must be within [0, 1]")


if __name__ == '__main__':
    unittest.main()