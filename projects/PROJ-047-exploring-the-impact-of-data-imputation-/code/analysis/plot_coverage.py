"""
Coverage plotting module (T047, T031).
Fixed import error: Dict -> dict.
"""
import os
import sys
import argparse
import json
import pandas as pd
import numpy as np
from typing import Dict as DictType, Any, List, Optional


def load_and_prepare_data(filepath: str) -> pd.DataFrame:
    """
    Load and prepare data for coverage analysis.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    df = pd.read_csv(filepath)
    # Filter out failed runs if necessary, but spec says preserve them.
    # For plotting coverage, we need valid coverage rates.
    df_valid = df[df['coverage_rate'].notna()]
    return df_valid


def run_regression_test(df: pd.DataFrame) -> DictType[str, float]:
    """
    Run a simple linear regression test for coverage vs beta.
    Returns slope, p-value, r-squared.
    """
    # Aggregate by beta
    agg = df.groupby('beta')['coverage_rate'].mean().reset_index()
    
    if len(agg) < 2:
        return {"slope": 0.0, "p_value": 1.0, "r_squared": 0.0}
    
    x = agg['beta'].values
    y = agg['coverage_rate'].values
    
    # Simple linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    return {
        "slope": float(slope),
        "p_value": float(p_value),
        "r_squared": float(r_value**2)
    }


def plot_coverage_vs_beta(df: pd.DataFrame, output_path: str):
    """
    Plot coverage rate vs beta.
    """
    import matplotlib.pyplot as plt
    
    agg = df.groupby('beta')['coverage_rate'].mean().reset_index()
    
    plt.figure(figsize=(10, 6))
    plt.scatter(agg['beta'], agg['coverage_rate'], label='Mean Coverage', color='blue')
    plt.plot(agg['beta'], agg['coverage_rate'], 'b-', alpha=0.5)
    
    # Add regression line
    if len(agg) >= 2:
        slope, intercept, _, _, _ = stats.linregress(agg['beta'], agg['coverage_rate'])
        reg_line = slope * agg['beta'] + intercept
        plt.plot(agg['beta'], reg_line, 'r--', label=f'Regression (slope={slope:.2f})')
    
    plt.xlabel('Beta (MNAR Intensity)')
    plt.ylabel('Coverage Rate')
    plt.title('Coverage Rate vs MNAR Intensity')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def save_regression_results(results: DictType[str, float], filepath: str):
    """
    Save regression results to JSON.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """
    CLI entry point for coverage plotting.
    """
    parser = argparse.ArgumentParser(description="Plot coverage vs beta")
    parser.add_argument("--input", required=True, help="Path to simulation_summary.csv")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--stats-output", default="data/results/coverage_regression.json", help="Output JSON for stats")
    args = parser.parse_args()
    
    try:
        df = load_and_prepare_data(args.input)
        plot_coverage_vs_beta(df, args.output)
        
        stats_results = run_regression_test(df)
        save_regression_results(stats_results, args.stats_output)
        
        print(f"Coverage plot saved to {args.output}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    from scipy import stats
    exit(main())
