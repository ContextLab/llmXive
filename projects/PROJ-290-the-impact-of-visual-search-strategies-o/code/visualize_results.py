"""
T039: Generate visualization figures for the study.

Creates three plots:
1. fixation_dist.png: Distribution of eye-to-mouth fixation ratios.
2. model_coeffs.png: Coefficients and confidence intervals from the LMM.
3. power_curve.png: A priori power analysis curve.

Requires:
- data/processed/features.csv (from T019/T020)
- results/lmm_continuous.csv (from T029a)
- results/power_analysis.json (from T032)
"""
import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import get_logger

# Configure warnings to avoid matplotlib backend issues in some environments
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def ensure_dir(path: Path):
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def load_features(config: Any) -> Optional[pd.DataFrame]:
    """Load processed features."""
    features_path = config.PROCESSED_DATA_DIR / "features.csv"
    if not features_path.exists():
        logging.error(f"Features file not found: {features_path}")
        return None
    return pd.read_csv(features_path)

def load_lmm_results(config: Any) -> Optional[pd.DataFrame]:
    """Load LMM results table."""
    results_path = config.RESULTS_DIR / "lmm_continuous.csv"
    if not results_path.exists():
        logging.error(f"LMM results not found: {results_path}")
        return None
    return pd.read_csv(results_path)

def load_power_analysis(config: Any) -> Optional[Dict[str, Any]]:
    """Load power analysis JSON."""
    power_path = config.RESULTS_DIR / "power_analysis.json"
    if not power_path.exists():
        logging.error(f"Power analysis not found: {power_path}")
        return None
    with open(power_path, 'r') as f:
        return json.load(f)

def plot_fixation_distribution(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """
    Plot distribution of eye-to-mouth fixation ratios.
    Expected column: 'fixation_ratio' or similar.
    """
    logger.info("Generating fixation distribution plot...")
    ensure_dir(output_path.parent)

    # Identify the ratio column
    ratio_col = None
    candidates = ['fixation_ratio', 'eye_mouth_ratio', 'continuous_ratio', 'ratio']
    for c in candidates:
        if c in df.columns:
            ratio_col = c
            break

    if ratio_col is None:
        logger.warning(f"Could not find ratio column. Available: {list(df.columns)}")
        # Try to find any numeric column that looks like a ratio
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            ratio_col = numeric_cols[0]
            logger.warning(f"Using {ratio_col} as proxy for ratio.")
        else:
            logger.error("No numeric columns found to plot.")
            return

    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x=ratio_col, kde=True, color='skyblue', edgecolor='black')
    plt.title(f'Distribution of {ratio_col.replace("_", " ").title()}', fontsize=14)
    plt.xlabel(ratio_col.replace("_", " ").title(), fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Add mean and median lines
    mean_val = df[ratio_col].mean()
    median_val = df[ratio_col].median()
    plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.3f}')
    plt.axvline(median_val, color='green', linestyle='-.', linewidth=2, label=f'Median: {median_val:.3f}')
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved fixation distribution to {output_path}")

def plot_model_coefficients(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """
    Plot model coefficients with confidence intervals.
    Expected columns: 'term', 'estimate', 'std_error', 'pvalue' or similar.
    """
    logger.info("Generating model coefficients plot...")
    ensure_dir(output_path.parent)

    # Identify columns
    term_col, est_col, se_col = None, None, None
    for c in df.columns:
        cl = c.lower()
        if 'term' in cl: term_col = c
        elif 'estimate' in cl or 'coef' in cl: est_col = c
        elif 'std_error' in cl or 'se' in cl: se_col = c

    if not all([term_col, est_col, se_col]):
        logger.warning(f"Could not identify coefficient columns. Available: {list(df.columns)}")
        return

    # Filter for fixed effects if possible (often 'term' contains 'Intercept' or predictor names)
    # We'll plot all terms present
    df_plot = df[[term_col, est_col, se_col]].copy()
    
    # Calculate CI (approx 1.96 * SE for 95% CI)
    df_plot['ci_lower'] = df_plot[est_col] - 1.96 * df_plot[se_col]
    df_plot['ci_upper'] = df_plot[est_col] + 1.96 * df_plot[se_col]

    plt.figure(figsize=(10, 6))
    
    # Sort by estimate for better visualization
    df_plot = df_plot.sort_values(by=est_col)
    df_plot = df_plot.reset_index(drop=True)

    y_pos = range(len(df_plot))
    plt.errorbar(
        y_pos, 
        df_plot[est_col], 
        yerr=[df_plot[est_col] - df_plot['ci_lower'], df_plot['ci_upper'] - df_plot[est_col]], 
        fmt='o', 
        color='navy', 
        ecolor='red', 
        capsize=5, 
        linestyle='None',
        markersize=8
    )
    
    plt.yticks(y_pos, df_plot[term_col])
    plt.axvline(0, color='gray', linestyle='--', linewidth=1)
    plt.xlabel('Coefficient Estimate', fontsize=12)
    plt.ylabel('Predictor', fontsize=12)
    plt.title('Linear Mixed-Effects Model Coefficients', fontsize=14)
    plt.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved model coefficients to {output_path}")

def plot_power_curve(power_data: Dict[str, Any], output_path: Path, logger: logging.Logger):
    """
    Plot power curve from a priori power analysis.
    Expected keys in power_data: 'sample_sizes', 'powers', 'effect_size', 'alpha'
    """
    logger.info("Generating power curve plot...")
    ensure_dir(output_path.parent)

    # Extract data
    sample_sizes = power_data.get('sample_sizes', [])
    powers = power_data.get('powers', [])
    effect_size = power_data.get('effect_size', 0.5)
    alpha = power_data.get('alpha', 0.05)

    if not sample_sizes or not powers:
        logger.warning("Power analysis data missing required arrays.")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(sample_sizes, powers, marker='o', color='darkgreen', linewidth=2, markersize=6)
    
    # Highlight 80% power
    plt.axhline(y=0.8, color='red', linestyle='--', linewidth=1.5, label='Target Power (0.80)')
    plt.axvline(x=sample_sizes[powers.index(min(powers, key=lambda x: abs(x-0.8)))], 
                color='orange', linestyle=':', linewidth=1.5, 
                label=f'N for 80% Power')

    plt.title(f'Power Curve (Effect Size d={effect_size}, α={alpha})', fontsize=14)
    plt.xlabel('Sample Size (N)', fontsize=12)
    plt.ylabel('Statistical Power', fontsize=12)
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved power curve to {output_path}")

def main():
    """Main entry point for T039."""
    config = get_config()
    logger = get_logger(__name__)
    
    logger.info("Starting T039: Visualization Generation")

    # Ensure output directory exists
    ensure_dir(config.FIGURES_DIR)

    # Load data
    df_features = load_features(config)
    df_lmm = load_lmm_results(config)
    power_data = load_power_analysis(config)

    if df_features is None and df_lmm is None and power_data is None:
        logger.error("No input data found. Cannot generate plots.")
        return

    # Generate Plots
    if df_features is not None:
        plot_fixation_distribution(df_features, config.FIGURES_DIR / "fixation_dist.png", logger)
    
    if df_lmm is not None:
        plot_model_coefficients(df_lmm, config.FIGURES_DIR / "model_coeffs.png", logger)
    
    if power_data is not None:
        plot_power_curve(power_data, config.FIGURES_DIR / "power_curve.png", logger)

    logger.info("T039 completed successfully.")

if __name__ == "__main__":
    main()
