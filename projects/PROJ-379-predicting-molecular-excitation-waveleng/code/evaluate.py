import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy.stats import wilcoxon, power_analysis

# Import project utilities
from utils import get_logger, setup_logging

# Configure logging
logger = get_logger(__name__)

# Constants
MIN_TEST_SIZE = 50
METRICS_FILE = "data/processed/metrics.json"

def load_data_splits(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train, validation, and test splits from CSV files."""
    train_path = data_dir / "train.csv"
    val_path = data_dir / "val.csv"
    test_path = data_dir / "test.csv"

    if not all(p.exists() for p in [train_path, val_path, test_path]):
        raise FileNotFoundError(f"Data splits not found. Expected: {train_path}, {val_path}, {test_path}")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    return train_df, val_df, test_df

def load_predictions(model_path: Path) -> pd.DataFrame:
    """Load predictions from the model output file."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model predictions not found: {model_path}")
    return pd.read_csv(model_path)

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute MAE and R² score."""
    mae = np.mean(np.abs(y_true - y_pred))
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    return {"mae": float(mae), "r2": float(r2)}

def perform_wilcoxon_test(y_true: np.ndarray, y_pred_gnn: np.ndarray, y_pred_baseline: np.ndarray) -> float:
    """Perform Wilcoxon signed-rank test between GNN and baseline predictions."""
    # Calculate errors
    err_gnn = np.abs(y_true - y_pred_gnn)
    err_baseline = np.abs(y_true - y_pred_baseline)

    stat, p_value = wilcoxon(err_gnn, err_baseline)
    return float(p_value)

def determine_sc001_status(mae: float, p_value: float, threshold: float = 0.05, mae_limit: float = 30.0) -> str:
    """Determine SC-001 status based on MAE and Wilcoxon p-value."""
    if p_value < threshold and mae < mae_limit:
        return "PASS"
    return "FAIL"

def compute_power_analysis(n: int, effect_size: float = 0.5, alpha: float = 0.05) -> Dict[str, Any]:
    """Compute statistical power for the given sample size."""
    # Using Cohen's d approximation for effect size
    # In a real scenario, we might use statsmodels for more precise calculation
    # Here we use a simplified approximation for demonstration
    from statsmodels.stats.power import TTestIndPower
    
    power_analysis_obj = TTestIndPower()
    try:
        power = power_analysis_obj.solve_power(effect_size=effect_size, nobs1=n, alpha=alpha, alternative='two-sided')
    except Exception:
        # Fallback for edge cases
        power = 0.0

    return {
        "n": n,
        "effect_size": effect_size,
        "power": float(power),
        "power_status": "ADEQUATE" if power >= 0.8 else "INADEQUATE"
    }

def enforce_test_size_constraint(test_df: pd.DataFrame) -> None:
    """
    Enforce n >= 50 constraint for the test set.
    Halts execution and logs an error if the test set size is insufficient.
    """
    n = len(test_df)
    if n < MIN_TEST_SIZE:
        error_msg = (
            f"CRITICAL: Test set size (n={n}) is below the required minimum of {MIN_TEST_SIZE}. "
            f"Statistical power is insufficient for valid conclusions (SC-001). "
            f"Execution halted to prevent downstream analysis with insufficient data."
        )
        logger.error(error_msg)
        # Raise an exception to halt the pipeline immediately
        raise RuntimeError(error_msg)
    
    logger.info(f"Test set size check passed: n={n} >= {MIN_TEST_SIZE}")

def main():
    """Main execution function for evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate GNN model performance")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Directory containing data splits")
    parser.add_argument("--predictions", type=str, default="data/processed/predictions.csv", help="Path to predictions file")
    parser.add_argument("--baseline-predictions", type=str, default="data/processed/baseline_predictions.csv", help="Path to baseline predictions file")
    parser.add_argument("--output", type=str, default=METRICS_FILE, help="Path to output metrics JSON")
    
    args = parser.parse_args()
    
    setup_logging()
    
    data_dir = Path(args.data_dir)
    output_path = Path(args.output)
    
    try:
        # Load data splits
        logger.info("Loading data splits...")
        train_df, val_df, test_df = load_data_splits(data_dir)
        
        # ENFORCE TEST SIZE CONSTRAINT (T019)
        enforce_test_size_constraint(test_df)
        
        # Load predictions
        logger.info("Loading predictions...")
        gnn_preds = load_predictions(Path(args.predictions))
        baseline_preds = load_predictions(Path(args.baseline_predictions))
        
        # Ensure we have the correct columns
        if "lambda_max" not in test_df.columns or "prediction" not in gnn_preds.columns or "prediction" not in baseline_preds.columns:
            raise ValueError("Missing required columns in data or predictions.")
        
        y_true = test_df["lambda_max"].values
        y_pred_gnn = gnn_preds["prediction"].values
        y_pred_baseline = baseline_preds["prediction"].values
        
        # Compute metrics
        logger.info("Computing metrics...")
        metrics = compute_metrics(y_true, y_pred_gnn)
        
        # Perform Wilcoxon test
        logger.info("Performing Wilcoxon signed-rank test...")
        p_value = perform_wilcoxon_test(y_true, y_pred_gnn, y_pred_baseline)
        metrics["wilcoxon_p_value"] = p_value
        
        # Determine SC-001 status
        sc001_status = determine_sc001_status(metrics["mae"], p_value)
        metrics["sc001_status"] = sc001_status
        
        # Compute power analysis
        logger.info("Computing power analysis...")
        power_info = compute_power_analysis(len(test_df))
        metrics["power_analysis"] = power_info
        
        # Write results
        logger.info(f"Writing results to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Evaluation complete. SC-001 Status: {sc001_status}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()