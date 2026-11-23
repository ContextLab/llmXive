import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from code.config import RESULTS_DIR, RAW_EVALUATIONS_FILE, STABILITY_METRICS_FILE, CORRELATION_RESULTS_FILE, REGRESSION_RESIDUALS_FILE, PERMUTATION_RESULTS_FILE, FINAL_REPORT_FILE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def write_raw_evaluations(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """Write raw evaluation results to CSV."""
    if filepath is None:
        filepath = str(RESULTS_DIR / RAW_EVALUATIONS_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Written raw evaluations to {filepath} ({len(df)} rows)")

def append_raw_evaluations(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """Append raw evaluation results to CSV."""
    if filepath is None:
        filepath = str(RESULTS_DIR / RAW_EVALUATIONS_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        df.to_csv(filepath, mode='a', header=False, index=False)
    else:
        df.to_csv(filepath, index=False)
    logger.info(f"Appended {len(df)} rows to {filepath}")

def write_stability_metrics(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """Write stability metrics to CSV."""
    if filepath is None:
        filepath = str(RESULTS_DIR / STABILITY_METRICS_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Written stability metrics to {filepath} ({len(df)} rows)")

def write_correlation_results(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """Write correlation results to CSV."""
    if filepath is None:
        filepath = str(RESULTS_DIR / CORRELATION_RESULTS_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Written correlation results to {filepath} ({len(df)} rows)")

def write_regression_residuals(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """Write regression residuals to CSV."""
    if filepath is None:
        filepath = str(RESULTS_DIR / REGRESSION_RESIDUALS_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Written regression residuals to {filepath} ({len(df)} rows)")

def write_permutation_results(df: pd.DataFrame, filepath: Optional[str] = None) -> None:
    """
    Write permutation test results to CSV.
    
    Schema:
      dataset_id (int), model_a (str), model_b (str), statistic (float),
      raw_p_value (float), adj_p_value (float), significant (bool)
    
    This function consumes the output from T026 (adjusted p-values) and T025 (raw results)
    and writes the final permutation results as required by T027.
    """
    if filepath is None:
        filepath = str(RESULTS_DIR / PERMUTATION_RESULTS_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Validate required columns exist
    required_cols = ['dataset_id', 'model_a', 'model_b', 'statistic', 'raw_p_value', 'adj_p_value', 'significant']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in permutation results: {missing_cols}")
    
    # Ensure correct types
    df['dataset_id'] = df['dataset_id'].astype(int)
    df['statistic'] = df['statistic'].astype(float)
    df['raw_p_value'] = df['raw_p_value'].astype(float)
    df['adj_p_value'] = df['adj_p_value'].astype(float)
    df['significant'] = df['significant'].astype(bool)
    
    df.to_csv(filepath, index=False)
    logger.info(f"Written permutation results to {filepath} ({len(df)} rows)")
    
    # Log summary
    significant_count = df['significant'].sum()
    logger.info(f"Significant differences found: {significant_count}/{len(df)}")

def write_final_report(content: str, filepath: Optional[str] = None) -> None:
    """Write final report to Markdown file."""
    if filepath is None:
        filepath = str(RESULTS_DIR / FINAL_REPORT_FILE)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Written final report to {filepath}")