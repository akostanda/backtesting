import pandas as pd
from abc import ABC, abstractmethod


class StrategyBase(ABC):
    def __init__(self, price_data: pd.DataFrame):
        self.price_data = price_data

    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def run_backtest(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_metrics(self) -> dict:
        pass
