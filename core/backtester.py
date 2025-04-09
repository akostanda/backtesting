import os
import pandas as pd
import vectorbt as vbt
from strategies.base import StrategyBase


class Backtester:
    """Backtester class evaluates trading strategies and calculates metrics."""
    RESULT_DIR = "results"

    def __init__(self, price_data: pd.DataFrame, strategy: StrategyBase):
        self.price_data = price_data
        self.strategy = strategy

    def get_backtest_results(self):
        # Run backtest and receive a curve
        self.strategy.run_backtest()

        # Calculate key metrics and call run_backtest
        metrics = self.strategy.get_metrics()
        os.makedirs(self.RESULT_DIR, exist_ok=True)
        pd.DataFrame([metrics]).to_csv(os.path.join(self.RESULT_DIR, f"metrics.csv"))

        # Form the portfolio
        portfolio = vbt.Portfolio.from_signals(
            self.price_data["close"],
            self.price_data["signal"],
            freq="1min"
        )
        # Get the portfolio result
        result = portfolio.total_return()

        return metrics, result
