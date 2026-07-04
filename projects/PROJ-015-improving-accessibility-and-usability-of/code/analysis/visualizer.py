import matplotlib.pyplot as plt
import pandas as pd
from utils.logger import get_logger

class Visualizer:
    def __init__(self):
        self.logger = get_logger("visualizer")

    def plot_boxplot(self, df: pd.DataFrame, x_col: str, y_col: str, out_path: str):
        plt.figure()
        df.boxplot(column=y_col, by=x_col)
        plt.savefig(out_path)
        plt.close()

def main():
    print("Visualizer module loaded.")
