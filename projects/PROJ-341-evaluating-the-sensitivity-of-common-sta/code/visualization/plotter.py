import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def load_thresholds(filepath: str) -> List[Dict]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)

def load_error_rates(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        return pd.DataFrame()
    return pd.read_csv(filepath)

def plot_error_rate_vs_sample_size(df: pd.DataFrame, test_type: str, output_path: str):
    """Plot error rate vs sample size for a specific test."""
    df_test = df[df['test_type'] == test_type]
    if df_test.empty:
        return

    plt.figure(figsize=(10, 6))
    for es in df_test['effect_size'].unique():
        sub = df_test[df_test['effect_size'] == es]
        plt.errorbar(sub['n'], sub['rate'], yerr=sub['upper_ci'] - sub['lower_ci'], 
                     label=f'es={es}', fmt='-o')
    
    plt.axhline(y=0.05, color='r', linestyle='--', label='Alpha=0.05')
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Error Rate / Power')
    plt.title(f'{test_type} - Error Rate vs Sample Size')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def plot_all_tests_comparison(df: pd.DataFrame, output_path: str):
    """Compare all tests at low sample sizes."""
    low_n = df[df['n'] < 30]
    if low_n.empty:
        return

    plt.figure(figsize=(10, 6))
    for test in low_n['test_type'].unique():
        sub = low_n[low_n['test_type'] == test]
        plt.plot(sub['n'], sub['rate'], label=test, marker='o')
    
    plt.xlabel('Sample Size (n)')
    plt.ylabel('Error Rate / Power')
    plt.title('Comparison of Tests at Low Sample Sizes')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def generate_all_plots():
    """Generate all plots."""
    df = load_error_rates("data/simulation/error_rates_summary.csv")
    if df.empty:
        print("No data to plot.")
        return
    
    os.makedirs("data/visualization", exist_ok=True)
    
    for test in df['test_type'].unique():
        plot_error_rate_vs_sample_size(df, test, f"data/visualization/{test}_vs_n.png")
    
    plot_all_tests_comparison(df, "data/visualization/test_comparison.png")
    print("Plots generated.")

def main():
    generate_all_plots()

if __name__ == '__main__':
    main()
