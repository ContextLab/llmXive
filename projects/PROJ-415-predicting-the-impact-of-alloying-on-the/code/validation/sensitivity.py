import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import DATA_DIR, REPORTS_DIR, MODELS_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

def load_baseline_shifts() -> pd.DataFrame:
    """
    Load the baseline_shifts.csv produced by T031.
    """
    file_path = DATA_DIR / "curated" / "baseline_shifts.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Baseline shifts file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    if 'baseline_shift' not in df.columns:
        raise ValueError(f"Missing 'baseline_shift' column in {file_path}")
    
    return df

def load_rf_rmse() -> float:
    """
    Load the RF RMSE from models/metrics.json produced by T025.
    """
    file_path = MODELS_DIR / "metrics.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        metrics = json.load(f)
    
    if 'rf_rmse' not in metrics:
        raise KeyError(f"Missing 'rf_rmse' key in {file_path}")
    
    return float(metrics['rf_rmse'])

def calculate_stability_metrics() -> Dict[str, float]:
    """
    Calculate classification stability metrics as per T033.
    
    1. Load baseline_shifts.csv (from T031).
    2. Load sensitivity_sweep.csv (from T032) to get classification rates.
    3. Calculate Standard Deviation (SD) of classification rates across 0.45-0.55 eV.
    4. Load RF RMSE from metrics.json (from T025).
    5. Compute stability_relative_to_rmse = SD / RMSE.
    
    Returns:
        Dict containing:
            - stability_sd: Standard Deviation of classification rates
            - mean_classification_rate: Mean of classification rates
            - stability_relative_to_rmse: Normalized stability metric
    """
    # Load sensitivity sweep results
    sweep_path = REPORTS_DIR / "sensitivity_sweep.csv"
    if not sweep_path.exists():
        raise FileNotFoundError(f"Sensitivity sweep file not found: {sweep_path}")
    
    sweep_df = pd.read_csv(sweep_path)
    
    if 'classification_rate' not in sweep_df.columns:
        raise ValueError(f"Missing 'classification_rate' column in {sweep_path}")
    
    classification_rates = sweep_df['classification_rate'].values
    
    # Check for sufficient variance as per T033 CRITICAL requirement
    # Although the task says "If number of unique baseline_shift values < 5",
    # we are operating on the classification rates here. The number of thresholds
    # is 11 (0.45 to 0.55). We need enough variance in the rates to be meaningful.
    # However, the strict check is on the input data's variance.
    # Let's check the baseline_shifts count for variance context.
    baseline_df = load_baseline_shifts()
    unique_shifts = baseline_df['baseline_shift'].nunique()
    
    if unique_shifts < 5:
        raise SystemExit("Stability Error: Insufficient variance in baseline shifts. Metric cannot be computed.")
    
    # Calculate Standard Deviation
    sd = np.std(classification_rates, ddof=1)  # Sample std dev
    mean_rate = np.mean(classification_rates)
    
    # Load RF RMSE
    rmse = load_rf_rmse()
    
    if rmse == 0:
        # Avoid division by zero; if RMSE is 0, stability relative to RMSE is undefined/infinite
        # In practice, this means perfect prediction, so stability is effectively infinite or 1.0?
        # Let's set it to a large number or handle gracefully. 
        # Given the context, if RMSE is 0, any SD is "large" relative to it.
        # We'll use a small epsilon to avoid crash, but log a warning.
        logger.warning("RF RMSE is zero. Stability relative to RMSE set to infinity.")
        stability_relative = float('inf')
    else:
        stability_relative = sd / rmse
    
    return {
        "stability_sd": float(sd),
        "mean_classification_rate": float(mean_rate),
        "stability_relative_to_rmse": float(stability_relative)
    }

def save_stability_metrics(metrics: Dict[str, float]) -> None:
    """
    Save stability metrics to reports/stability_metrics.json.
    """
    output_path = REPORTS_DIR / "stability_metrics.json"
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Stability metrics saved to {output_path}")

def main():
    """
    Main entry point for T033.
    """
    logger.info("Starting T033: Calculate classification stability")
    
    try:
        metrics = calculate_stability_metrics()
        save_stability_metrics(metrics)
        logger.info("T033 completed successfully.")
        return metrics
    except (FileNotFoundError, ValueError, KeyError, SystemExit) as e:
        logger.error(f"T033 failed: {e}")
        raise

if __name__ == "__main__":
    main()