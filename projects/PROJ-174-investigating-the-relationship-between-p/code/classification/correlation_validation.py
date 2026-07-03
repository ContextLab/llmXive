import os
import sys
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

# Adjust import based on project structure relative to code/
# Assuming this file is inside code/classification/, we go up one level
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_classification_results(results_path: str) -> pd.DataFrame:
    """
    Load the classification metrics CSV containing predicted probabilities and search times.
    Expects columns: 'predicted_probability', 'search_time' (or similar based on T029/T030 output).
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Classification results file not found: {path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['predicted_probability', 'search_time']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    
    # Drop rows with NaN in critical columns
    df = df.dropna(subset=required_cols)
    logger.info(f"Loaded {len(df)} valid records from {path}")
    return df


def compute_continuous_correlation(df: pd.DataFrame) -> dict:
    """
    Compute Pearson and Spearman correlations between predicted probability and search time.
    Returns a dictionary with correlation coefficients and p-values.
    """
    probs = df['predicted_probability'].values
    times = df['search_time'].values

    pearson_r, pearson_p = pearsonr(probs, times)
    spearman_r, spearman_p = spearmanr(probs, times)

    logger.info(f"Pearson r: {pearson_r:.4f} (p={pearson_p:.4f})")
    logger.info(f"Spearman rho: {spearman_r:.4f} (p={spearman_p:.4f})")

    return {
        'pearson_r': float(pearson_r),
        'pearson_p_value': float(pearson_p),
        'spearman_rho': float(spearman_r),
        'spearman_p_value': float(spearman_p),
        'n_samples': int(len(df))
    }


def save_correlation_report(stats: dict, output_path: str):
    """
    Save the correlation statistics to a CSV file.
    """
    df_stats = pd.DataFrame([stats])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_stats.to_csv(output_path, index=False)
    logger.info(f"Saved correlation report to {output_path}")


def run_validation_pipeline(config: dict, results_path: str, output_path: str):
    """
    Main pipeline function for T032: Output continuous correlation between 
    predicted probability and search time as auxiliary validation.
    """
    logger.info("Starting T032: Continuous Correlation Validation")
    
    try:
        df = load_classification_results(results_path)
        stats = compute_continuous_correlation(df)
        save_correlation_report(stats, output_path)
        logger.info("T032 completed successfully.")
        return True
    except Exception as e:
        logger.error(f"T032 failed: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="T032: Validate continuous correlation between prediction and search time.")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config.yaml')
    parser.add_argument('--input', type=str, required=True, help='Path to classification results CSV (predicted_probability, search_time)')
    parser.add_argument('--output', type=str, default='results/correlation_validation.csv', help='Path to output correlation report CSV')
    
    args = parser.parse_args()
    
    # Load config (optional for this specific task, but good practice)
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.warning(f"Could not load config (non-fatal): {e}")
        config = {}

    run_validation_pipeline(config, args.input, args.output)


if __name__ == '__main__':
    main()