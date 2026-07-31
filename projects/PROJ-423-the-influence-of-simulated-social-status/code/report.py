"""
Reporting module for the simulated social status study.
Generates visualizations (forest plots) and summary reports.
"""
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Local imports based on provided API surface
from logger import get_logger
from utils import load_json, ensure_directory, save_json
from config import load_decision_record

logger = get_logger(__name__)

# Ensure seaborn style
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12


def calculate_condition_stats(processed_data_path: str) -> pd.DataFrame:
    """
    Calculates mean, standard error, and 95% CI for each condition combination.
    
    Args:
        processed_data_path: Path to the processed CSV file.
        
    Returns:
        DataFrame with columns: status_level, observed_behavior, mean, std_err, ci_lower, ci_upper, n
    """
    logger.info(f"Loading processed data from {processed_data_path}")
    df = pd.read_csv(processed_data_path)
    
    # Ensure categorical types if not already (in case of raw load)
    # Assuming the preprocessing step handled mapping to 'High'/'Low' etc.
    # We rely on the standard column names from data-model.md
    
    group_cols = ['status_level', 'observed_behavior']
    
    # Check if columns exist
    missing_cols = [c for c in group_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required grouping columns: {missing_cols}. "
                       f"Available: {list(df.columns)}")
        
    if 'risk_taking_score' not in df.columns:
        raise ValueError(f"Missing outcome variable 'risk_taking_score'. "
                       f"Available: {list(df.columns)}")

    stats = df.groupby(group_cols)['risk_taking_score'].agg(
        mean='mean',
        std='std',
        n='count'
    ).reset_index()
    
    # Calculate Standard Error and 95% CI
    # CI = mean +/- t * (std / sqrt(n))
    # For large N, t ~ 1.96. For small N, use t-distribution.
    # We'll use scipy.stats.t for robustness, assuming it's available in deps.
    # If not, fallback to 1.96 approximation.
    try:
        from scipy import stats as scipy_stats
        use_scipy = True
    except ImportError:
        use_scipy = False
        logger.warning("scipy not found. Using Z=1.96 for 95% CI approximation.")

    def calc_ci(group):
        if group['n'] < 2:
            return 0.0, 0.0
        
        se = group['std'] / np.sqrt(group['n'])
        
        if use_scipy:
            # Use t-distribution for small samples
            t_val = scipy_stats.t.ppf(0.975, df=group['n']-1)
        else:
            t_val = 1.96
            
        margin = t_val * se
        return group['mean'] - margin, group['mean'] + margin

    ci_results = stats.apply(lambda row: calc_ci(row), axis=1)
    stats['ci_lower'] = [x[0] for x in ci_results]
    stats['ci_upper'] = [x[1] for x in ci_results]
    
    return stats


def generate_forest_plot(stats_df: pd.DataFrame, output_path: str) -> str:
    """
    Generates a forest plot of condition means with 95% Confidence Intervals.
    
    Args:
        stats_df: DataFrame containing condition statistics (from calculate_condition_stats).
        output_path: Path to save the figure (e.g., 'figures/forest_plot.png').
        
    Returns:
        The path to the saved figure.
    """
    ensure_directory(output_path)
    
    # Sort for consistent plotting (e.g., High status first)
    # Assuming status_level is 'High'/'Low' and behavior is 'Risky'/'Conservative'
    # Define a custom order if needed, otherwise default sort
    stats_df = stats_df.sort_values(by=['status_level', 'observed_behavior'])
    
    # Create a combined label for X-axis if desired, or use two facets
    # A single forest plot usually has one Y-axis for categories and X for value
    stats_df['category'] = stats_df['status_level'].astype(str) + ' - ' + stats_df['observed_behavior'].astype(str)
    
    plt.figure(figsize=(10, 6))
    
    # Plot error bars
    plt.errorbar(
        stats_df['category'],
        stats_df['mean'],
        yerr=[stats_df['mean'] - stats_df['ci_lower'], stats_df['ci_upper'] - stats_df['mean']],
        fmt='o',
        capsize=5,
        linestyle='None',
        color='#2c7bb6',
        ecolor='#d7191c',
        markersize=8,
        markerfacecolor='#2c7bb6',
        markeredgecolor='black'
    )
    
    # Add a reference line at 0 if applicable (though risk score might be scaled)
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    plt.xlabel('Experimental Condition', fontsize=14)
    plt.ylabel('Risk Taking Score (Mean ± 95% CI)', fontsize=14)
    plt.title('Effect of Simulated Social Status on Risk-Taking Behavior', fontsize=16)
    
    # Rotate x-ticks for readability
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Forest plot saved to {output_path}")
    return output_path


def generate_summary_report(stats_df: pd.DataFrame, output_path: str) -> str:
    """
    Generates a JSON summary report of the analysis results.
    
    Args:
        stats_df: DataFrame containing condition statistics.
        output_path: Path to save the JSON report.
        
    Returns:
        The path to the saved report.
    """
    ensure_directory(output_path)
    
    report = {
        "title": "Simulated Social Status Study - Condition Means Summary",
        "generated_at": pd.Timestamp.now().isoformat(),
        "methodology": "Descriptive statistics with 95% Confidence Intervals calculated via t-distribution.",
        "results": []
    }
    
    for _, row in stats_df.iterrows():
        report["results"].append({
            "status_level": row['status_level'],
            "observed_behavior": row['observed_behavior'],
            "n": int(row['n']),
            "mean": float(row['mean']),
            "std_err": float(row['std'] / np.sqrt(row['n'])) if row['n'] > 0 else 0.0,
            "ci_95_lower": float(row['ci_lower']),
            "ci_95_upper": float(row['ci_upper'])
        })
        
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Summary report saved to {output_path}")
    return output_path


def main():
    """
    Main entry point for the reporting pipeline.
    Reads processed data, calculates statistics, and generates the forest plot.
    """
    # Configuration
    processed_data_path = "data/processed/synthetic_data_processed.csv"
    figures_dir = "figures"
    reports_dir = "reports"
    
    output_plot_path = os.path.join(figures_dir, "forest_plot.png")
    output_report_path = os.path.join(reports_dir, "condition_summary.json")
    
    logger.info("Starting reporting pipeline (T032)")
    
    # 1. Calculate Statistics
    try:
        stats_df = calculate_condition_stats(processed_data_path)
        logger.info(f"Calculated statistics for {len(stats_df)} conditions.")
        logger.debug(stats_df.to_string())
    except FileNotFoundError:
        logger.error(f"Processed data file not found at {processed_data_path}. "
                   "Please run the preprocessing pipeline first.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
        
    # 2. Generate Forest Plot
    try:
        generate_forest_plot(stats_df, output_plot_path)
    except Exception as e:
        logger.error(f"Failed to generate forest plot: {e}")
        sys.exit(1)
        
    # 3. Generate JSON Summary
    try:
        generate_summary_report(stats_df, output_report_path)
    except Exception as e:
        logger.error(f"Failed to generate summary report: {e}")
        sys.exit(1)
        
    logger.info("Reporting pipeline completed successfully.")


if __name__ == "__main__":
    main()