import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Local imports based on API surface
from utils import get_logger, setup_logging

# Configure logging
logger = get_logger(__name__)

def load_data_splits(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load train, val, and test data splits from CSV files."""
    train_path = data_dir / "train_val_test.csv"
    if not train_path.exists():
        # Fallback to separate files if combined doesn't exist
        train_path = data_dir / "train.csv"
        val_path = data_dir / "val.csv"
        test_path = data_dir / "test.csv"
        return pd.read_csv(train_path), pd.read_csv(val_path), pd.read_csv(test_path)
    
    df = pd.read_csv(train_path)
    # Assuming the file has a 'split' column or we need to reconstruct
    # Based on T010.5, it's a single file. We need to know how splits are marked.
    # Standard convention: 'split' column with values 'train', 'val', 'test'
    if 'split' not in df.columns:
        # If not present, we might need to load the indices from JSON
        indices_path = data_dir / "split_indices.json"
        if indices_path.exists():
            with open(indices_path, 'r') as f:
                indices = json.load(f)
            train_idx = indices['train_idx']
            val_idx = indices['val_idx']
            test_idx = indices['test_idx']
            return df.iloc[train_idx], df.iloc[val_idx], df.iloc[test_idx]
        else:
            raise FileNotFoundError("Cannot determine splits. Missing 'split' column or 'split_indices.json'.")
    
    return (
        df[df['split'] == 'train'],
        df[df['split'] == 'val'],
        df[df['split'] == 'test']
    )

def load_predictions(predictions_path: Path) -> Dict[str, Any]:
    """Load model predictions from JSON."""
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    with open(predictions_path, 'r') as f:
        return json.load(f)

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute MAE and R2 score."""
    mae = np.mean(np.abs(y_true - y_pred))
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    return {"mae": float(mae), "r2": float(r2)}

def perform_wilcoxon_test(y_true: np.ndarray, y_pred_gnn: np.ndarray, y_pred_baseline: np.ndarray) -> float:
    """Perform Wilcoxon signed-rank test between GNN and baseline errors."""
    err_gnn = np.abs(y_true - y_pred_gnn)
    err_base = np.abs(y_true - y_pred_baseline)
    stat, p_value = stats.wilcoxon(err_gnn, err_base)
    return float(p_value)

def compute_confidence_interval(errors_gnn: np.ndarray, errors_baseline: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Compute 95% confidence interval for the difference in errors (MAE difference)."""
    diff = errors_gnn - errors_baseline
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    n = len(diff)
    if n < 2:
        return (mean_diff, mean_diff)
    # t-distribution for small samples, normal for large
    alpha = 1 - confidence
    dof = n - 1
    t_val = stats.t.ppf(1 - alpha/2, dof)
    margin = t_val * (std_diff / np.sqrt(n))
    return (float(mean_diff - margin), float(mean_diff + margin))

def determine_sc001_status(mae: float, p_value: float, threshold: float = 30.0) -> str:
    """
    Determine SC-001 status based on Decision Logic:
    If p < 0.05 AND MAE < 30 then "PASS", else "FAIL".
    """
    if p_value < 0.05 and mae < threshold:
        return "PASS"
    return "FAIL"

def compute_effect_size(y_true: np.ndarray, y_pred_gnn: np.ndarray, y_pred_baseline: np.ndarray) -> float:
    """Compute Cohen's d for the difference in errors."""
    err_gnn = np.abs(y_true - y_pred_gnn)
    err_base = np.abs(y_true - y_pred_baseline)
    diff = err_gnn - err_base
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        return 0.0
    return float(mean_diff / std_diff)

def classify_effect_size(cohens_d: float) -> str:
    """Classify effect size: <0.2 negligible, 0.2-0.5 small, 0.5-0.8 medium, >0.8 large."""
    if abs(cohens_d) < 0.2:
        return "negligible"
    elif abs(cohens_d) < 0.5:
        return "small"
    elif abs(cohens_d) < 0.8:
        return "medium"
    else:
        return "large"

def compute_power_analysis(n: int, effect_size: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Compute power analysis results.
    Returns dict with n, effect_size, power_status.
    Simple approximation: power increases with n and effect_size.
    For strict compliance, we check if n >= 50.
    """
    # Simplified power check logic for this task
    # In a full implementation, one would use statsmodels.stats.power
    power_status = "insufficient" if n < 50 else "sufficient"
    return {
        "n": n,
        "effect_size": effect_size,
        "power_status": power_status,
        "alpha": alpha
    }

def enforce_test_size_constraint(test_df: pd.DataFrame, min_size: int = 50) -> None:
    """
    Enforce n>=50 constraint on test set.
    If test set size < 50, halt execution and log error.
    SC-001 requirement.
    """
    n = len(test_df)
    if n < min_size:
        error_msg = (
            f"CRITICAL: Test set size (n={n}) is below the required minimum of {min_size}. "
            f"Cannot proceed with evaluation as statistical power is insufficient (SC-001). "
            f"Please increase the dataset size or adjust the split ratio."
        )
        logger.error(error_msg)
        # Halt execution explicitly
        raise ValueError(error_msg)
    logger.info(f"Test set size check passed: n={n} >= {min_size}")

def save_power_analysis(power_data: Dict[str, Any], output_path: Path) -> None:
    """Save power analysis results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(power_data, f, indent=2)
    logger.info(f"Power analysis saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate GNN model performance.")
    parser.add_argument("--data_dir", type=str, default="data/processed", help="Directory containing processed data.")
    parser.add_argument("--predictions", type=str, default="model_predictions.json", help="Path to predictions file.")
    parser.add_argument("--output_dir", type=str, default="data/processed", help="Directory to save results.")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_logging()

    try:
        # Load data
        logger.info("Loading data splits...")
        train_df, val_df, test_df = load_data_splits(data_dir)
        
        # Enforce test size constraint FIRST (T019)
        enforce_test_size_constraint(test_df, min_size=50)

        # Load predictions
        predictions_path = data_dir / args.predictions
        if not predictions_path.exists():
            # Try common alternative
            predictions_path = Path(args.predictions)
        
        preds = load_predictions(predictions_path)
        
        y_true = test_df['lambda_max'].values
        y_pred_gnn = np.array(preds['gnn_predictions'])
        y_pred_baseline = np.array(preds['baseline_predictions'])

        # Compute metrics
        metrics = compute_metrics(y_true, y_pred_gnn)
        logger.info(f"MAE: {metrics['mae']:.2f}, R2: {metrics['r2']:.4f}")

        # Wilcoxon test
        p_value = perform_wilcoxon_test(y_true, y_pred_gnn, y_pred_baseline)
        logger.info(f"Wilcoxon p-value: {p_value:.4f}")

        # Confidence Interval
        err_gnn = np.abs(y_true - y_pred_gnn)
        err_base = np.abs(y_true - y_pred_baseline)
        ci_low, ci_high = compute_confidence_interval(err_gnn, err_base)
        logger.info(f"95% CI for MAE difference: [{ci_low:.2f}, {ci_high:.2f}]")

        # SC-001 Status
        sc001_status = determine_sc001_status(metrics['mae'], p_value)
        logger.info(f"SC-001 Status: {sc001_status}")

        # Power Analysis
        effect_size = compute_effect_size(y_true, y_pred_gnn, y_pred_baseline)
        power_data = compute_power_analysis(len(test_df), effect_size)
        logger.info(f"Power Analysis: n={power_data['n']}, effect_size={effect_size:.3f}, status={power_data['power_status']}")
        
        # Save Power Analysis
        power_path = output_dir / "power_analysis.json"
        save_power_analysis(power_data, power_path)

        # Save partial metrics
        partial_metrics = {
            "mae": metrics['mae'],
            "r2": metrics['r2'],
            "wilcoxon_p_value": p_value,
            "confidence_interval_95": [ci_low, ci_high],
            "sc001_status": sc001_status,
            "power_analysis": power_data
        }

        metrics_path = output_dir / "metrics_partial.json"
        with open(metrics_path, 'w') as f:
            json.dump(partial_metrics, f, indent=2)
        
        logger.info(f"Evaluation complete. Results saved to {metrics_path}")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()