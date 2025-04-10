# backtesting
Backtesting trading strategies


## Technologies
* python 3
* vectorbt
* matplotlib
* numpy
* pandas
* Requests


## Instalation
To run the program after downloading, follow these steps:
1. Install Python 3 if you don't have it already:
```bash
  sudo apt install python3
```
2. Install pip (Python package manager) if it's not already installed:
```bash
  sudo apt install python3-pip
```
3. Install required Python libraries:
```bash
  pip install -r requirements.txt
```
3. Install pytest for running tests:
```bash
  pip install pytest
```

## Run
* To run the backtesting program:
```bash
  python3 main.py
```
This will run the program, download CSV files to the 'data' folder, and store the program results in the 'results' folder. Currently, only the SMA Crossover strategy is implemented, so the command runs this strategy by default. Once other strategies are added, you will be able to choose which one to run.
* To run all tests:
```bash
  pytest tests/
```
This will run all the tests, and the results will be displayed in the terminal.