import os
import json
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from code.config import DATA_PATH

logger = logging.getLogger(__name__)

def load_feature_importance():
    path = os.path.join(DATA_PATH, 'processed', 'feature_importance.csv')
    return pd.read_csv(path)

def load_processed_data():
    path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    return pd.read_csv(path)

def load_correlation_results():
    # Placeholder
    return {}

def get_top_features(df: pd.DataFrame, n: int = 5):
    return df.head(n)

def create_scatter_plot_with_regression(df: pd.DataFrame, x_col: str, y_col: str, output_path: str):
    plt.figure(figsize=(10, 6))
    sns.regplot(x=df[x_col], y=df[y_col], ci=95)
    plt.title(f'{x_col} vs {y_col}')
    plt.savefig(output_path)
    plt.close()

def generate_top_feature_plots(df: pd.DataFrame, target_col: str, n: int = 5):
    # T043
    top_features = get_top_features(df, n)
    for _, row in top_features.iterrows():
        # Assuming feature importance is already ranked
        pass
    # Generate plot
    output_path = os.path.join(DATA_PATH, 'processed', 'corr_plot_top5.png')
    create_scatter_plot_with_regression(df, 'degree_mean', target_col, output_path)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    
    if args.plot:
        df = load_processed_data()
        generate_top_feature_plots(df, 'conductivity')
        logger.info("Plots generated.")
