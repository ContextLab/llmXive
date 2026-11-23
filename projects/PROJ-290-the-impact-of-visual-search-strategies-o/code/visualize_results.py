"""
Visualization module for generating plots from the visual search analysis pipeline.
Generates fixation distribution, model coefficients, and power curve plots.
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

from config import get_config
from utils.logging import get_logger

# Ensure consistent plotting style
plt.style.use('seaborn-v0_8-whitegrid')
warnings.filterwarnings('ignore', category=UserWarning)

def ensure_dir(directory_path: Path) -> None:
    """Ensure the specified directory exists, creating it if necessary."""
    directory_path.mkdir(parents=True, exist_ok=True)

def load_features(config: Any) -> Optional[pd.DataFrame]:
    """Load processed features from data/processed/features.csv."""
    features_path = config.PROCESSED_DATA_DIR / "features.csv"
    if not features_path.exists():
        logger = get_logger("visualize_results")
        logger.error(f"Features file not found at {features_path}")
        return None
    try:
        df = pd.read_csv(features_path)
        return df
    except Exception as e:
        logger = get_logger("visualize_results")
        logger.error(f"Failed to load features: {e}")
        return None

def load_lmm_results(config: Any) -> Optional[pd.DataFrame]:
    """Load LMM results from results/lmm_continuous.csv."""
    results_path = config.RESULTS_DIR / "lmm_continuous.csv"
    if not results_path.exists():
        logger = get_logger("visualize_results")
        logger.warning(f"LMM results file not found at {results_path}")
        return None
    try:
        df = pd.read_csv(results_path)
        return df
    except Exception as e:
        logger = get_logger("visualize_results")
        logger.error(f"Failed to load LMM results: {e}")
        return None

def load_power_analysis(config: Any) -> Optional[Dict[str, Any]]:
    """Load power analysis results from results/power_analysis.json."""
    power_path = config.RESULTS_DIR / "power_analysis.json"
    if not power_path.exists():
        logger = get_logger("visualize_results")
        logger.warning(f"Power analysis file not found at {power_path}")
        return None
    try:
        with open(power_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger = get_logger("visualize_results")
        logger.error(f"Failed to load power analysis: {e}")
        return None

def plot_fixation_distribution(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Generate a histogram/density plot of fixation durations (eye vs mouth).
    Expects columns: 'fixation_eye_duration', 'fixation_mouth_duration'.
    """
    logger = get_logger("visualize_results")
    if df is None:
        logger.error("Cannot plot fixation distribution: no data loaded.")
        return False

    required_cols = ['fixation_eye_duration', 'fixation_mouth_duration']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns for fixation plot: {missing}")
        return False

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot distributions
    sns.kdeplot(data=df, x='fixation_eye_duration', label='Eye Region', fill=True, alpha=0.4, ax=ax)
    sns.kdeplot(data=df, x='fixation_mouth_duration', label='Mouth Region', fill=True, alpha=0.4, ax=ax)

    ax.set_xlabel('Fixation Duration (ms)')
    ax.set_ylabel('Density')
    ax.set_title('Distribution of Fixation Durations by ROI')
    ax.legend()

    try:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved fixation distribution plot to {output_path}")
        plt.close(fig)
        return True
    except Exception as e:
        logger.error(f"Failed to save fixation distribution plot: {e}")
        plt.close(fig)
        return False

def plot_model_coefficients(df: pd.DataFrame, output_path: Path) -> bool:
    """
    Generate a bar plot of model coefficients with confidence intervals.
    Expects columns: 'term', 'estimate', 'std_error', 't_statistic', 'p_value'.
    """
    logger = get_logger("visualize_results")
    if df is None:
        logger.error("Cannot plot model coefficients: no data loaded.")
        return False

    required_cols = ['term', 'estimate', 'std_error']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns for coefficient plot: {missing}")
        return False

    # Filter out intercept if present for clarity, or keep if desired
    # Usually we want to see the predictor
    plot_df = df[~df['term'].str.contains('Intercept', case=False, na=False)].copy()

    if plot_df.empty:
        logger.warning("No non-intercept terms found for coefficient plot.")
        # If only intercept exists, plot it
        plot_df = df.copy()

    fig, ax = plt.subplots(figsize=(8, 6))

    # Calculate CI
    plot_df['ci_lower'] = plot_df['estimate'] - 1.96 * plot_df['std_error']
    plot_df['ci_upper'] = plot_df['estimate'] + 1.96 * plot_df['std_error']

    # Sort by estimate for better visualization
    plot_df = plot_df.sort_values('estimate')

    bars = ax.barh(plot_df['term'], plot_df['estimate'], xerr=[plot_df['estimate'] - plot_df['ci_lower'], plot_df['ci_upper'] - plot_df['estimate']], capsize=5, color='steelblue', alpha=0.8)

    # Add zero line
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1)

    ax.set_xlabel('Coefficient Estimate (95% CI)')
    ax.set_ylabel('Predictor')
    ax.set_title('Linear Mixed-Effects Model Coefficients')

    try:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved model coefficients plot to {output_path}")
        plt.close(fig)
        return True
    except Exception as e:
        logger.error(f"Failed to save model coefficients plot: {e}")
        plt.close(fig)
        return False

def plot_power_curve(power_data: Dict[str, Any], output_path: Path) -> bool:
    """
    Generate a power curve plot showing power vs sample size.
    Expects power_data to have keys: 'sample_sizes', 'powers', 'effect_size', 'alpha'.
    """
    logger = get_logger("visualize_results")
    if power_data is None:
        logger.error("Cannot plot power curve: no data loaded.")
        return False

    required_keys = ['sample_sizes', 'powers']
    missing = [k for k in required_keys if k not in power_data]
    if missing:
        logger.error(f"Missing required keys in power data: {missing}")
        return False

    sample_sizes = power_data['sample_sizes']
    powers = power_data['powers']

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.plot(sample_sizes, powers, marker='o', linestyle='-', color='darkgreen', label='Power')
    ax.axhline(y=0.80, color='red', linestyle='--', linewidth=1, label='Target Power (0.80)')
    ax.axvline(x=power_data.get('target_n', sample_sizes[np.argmin(np.abs(np.array(powers) - 0.80))]), color='orange', linestyle=':', linewidth=1, label='Required N')

    ax.set_xlabel('Sample Size (N)')
    ax.set_ylabel('Statistical Power')
    ax.set_title('A Priori Power Analysis Curve')
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)

    try:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved power curve plot to {output_path}")
        plt.close(fig)
        return True
    except Exception as e:
        logger.error(f"Failed to save power curve plot: {e}")
        plt.close(fig)
        return False

def main():
    """Main entry point to generate all required figures."""
    config = get_config()
    logger = get_logger("visualize_results")
    logger.info("Starting figure generation for T039...")

    # Ensure output directory exists
    figures_dir = config.RESULTS_FIGURES_DIR
    ensure_dir(figures_dir)

    # Load data
    features_df = load_features(config)
    lmm_df = load_lmm_results(config)
    power_data = load_power_analysis(config)

    # Generate plots
    success_count = 0
    total_plots = 3

    # 1. Fixation Distribution
    fixation_path = figures_dir / "fixation_dist.png"
    if plot_fixation_distribution(features_df, fixation_path):
        success_count += 1

    # 2. Model Coefficients
    coeffs_path = figures_dir / "model_coeffs.png"
    if plot_model_coefficients(lmm_df, coeffs_path):
        success_count += 1

    # 3. Power Curve
    power_path = figures_dir / "power_curve.png"
    if plot_power_curve(power_data, power_path):
        success_count += 1

    logger.info(f"Figure generation complete: {success_count}/{total_plots} plots created successfully.")

    if success_count < total_plots:
        logger.warning("Some plots failed to generate. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("All required figures generated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()