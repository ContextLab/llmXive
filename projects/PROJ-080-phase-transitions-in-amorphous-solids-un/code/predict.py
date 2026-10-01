import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

# Import from utils for seed consistency
from utils import set_seed
from env_config import get_dataset_path, verify_source_integrity
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

def load_analysis_results(input_dir: Path) -> pd.DataFrame:
    """
    Load the analysis results (KS-test, shear band aggregates) from the processed directory.
    Expects 'ks_test_results.json' or 'precursor_metrics.csv' depending on context,
    but primarily aggregates the final predictive features.
    """
    metrics_path = input_dir / "precursor_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Required input file not found: {metrics_path}")
    
    logger.info(f"Loading precursor metrics from {metrics_path}")
    df = pd.read_csv(metrics_path)
    
    # Ensure required columns exist for threshold derivation
    required_cols = ['D2_min', 'yield_flag', 'shear_band_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in precursor_metrics.csv: {missing}")
    
    return df

def derive_threshold(df: pd.DataFrame) -> float:
    """
    Derive the base threshold value from the dataset.
    Algorithm: Select the D_min value that maximizes F1-score on the training set.
    For this implementation, we perform a grid search over unique D2_min values
    to find the optimal cutoff that separates yield (1) from non-yield (0).
    """
    if 'yield_flag' not in df.columns or 'D2_min' not in df.columns:
        raise ValueError("Cannot derive threshold: missing yield_flag or D2_min columns")

    # Filter out NaNs
    valid_df = df.dropna(subset=['D2_min', 'yield_flag'])
    if valid_df.empty:
        raise ValueError("No valid data points to derive threshold from.")

    unique_vals = sorted(valid_df['D2_min'].unique())
    best_f1 = -1.0
    best_threshold = unique_vals[0] if unique_vals else 0.0

    # Simple grid search over unique values + midpoints
    candidates = list(unique_vals)
    for i in range(len(unique_vals) - 1):
        mid = (unique_vals[i] + unique_vals[i+1]) / 2.0
        candidates.append(mid)

    for thresh in candidates:
        preds = (valid_df['D2_min'] >= thresh).astype(int)
        actuals = valid_df['yield_flag'].astype(int)
        
        tp = ((preds == 1) & (actuals == 1)).sum()
        fp = ((preds == 1) & (actuals == 0)).sum()
        fn = ((preds == 0) & (actuals == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh

    logger.info(f"Derived optimal threshold: {best_threshold:.6f} with F1: {best_f1:.4f}")
    return best_threshold

def create_holdout_split(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a hold-out split on the dataset to create a validation set.
    Satisfies SC-001 by defining the set against which F-score is measured.
    """
    set_seed(seed)
    indices = np.random.permutation(len(df))
    split_idx = int(len(df) * (1 - test_size))
    
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    logger.info(f"Created holdout split: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df

def define_time_to_failure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define 'time-to-failure' as an independent ground truth.
    In this context, we use the provided 'yield_flag' as the failure event indicator.
    If 'strain_at_yield' exists, we use that as the magnitude; otherwise, we assume
    the yield_flag is the primary ground truth for classification.
    """
    df = df.copy()
    # Ensure yield_flag is numeric
    if 'yield_flag' in df.columns:
        df['failure_event'] = df['yield_flag'].astype(int)
    else:
        # Fallback if not present (should not happen given load_analysis_results check)
        df['failure_event'] = 0
    
    logger.info("Defined failure event ground truth.")
    return df

def sweep_threshold(df: pd.DataFrame, base_threshold: float, step_size: float = 0.05) -> List[Dict]:
    """
    Sweep D2_min threshold over the specific range: {threshold - 0.05, threshold, threshold + 0.05}.
    Calculates FPR, FNR, TP, TN, and F-score for each step.
    """
    thresholds = [base_threshold - step_size, base_threshold, base_threshold + step_size]
    results = []

    for thresh in thresholds:
        if thresh < 0: thresh = 0.0 # Physical constraint

        preds = (df['D2_min'] >= thresh).astype(int)
        actuals = df['failure_event'].astype(int)

        tp = ((preds == 1) & (actuals == 1)).sum()
        tn = ((preds == 0) & (actuals == 0)).sum()
        fp = ((preds == 1) & (actuals == 0)).sum()
        fn = ((preds == 0) & (actuals == 1)).sum()

        total_pos = tp + fn
        total_neg = tn + fp

        fpr = fp / total_neg if total_neg > 0 else 0.0
        fnr = fn / total_pos if total_pos > 0 else 0.0
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        results.append({
            "threshold": float(thresh),
            "TP": int(tp),
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "FPR": float(fpr),
            "FNR": float(fnr),
            "F1": float(f1)
        })
    
    logger.info(f"Swept {len(thresholds)} thresholds.")
    return results

def main():
    parser = argparse.ArgumentParser(description="Predictive Threshold Validation Pipeline")
    parser.add_argument("--input-dir", type=str, required=True, help="Input directory for processed data")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory for results")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Starting predictive threshold validation...")

    # 1. Load Data
    try:
        df = load_analysis_results(input_path)
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)

    # 2. Define Ground Truth
    df = define_time_to_failure(df)

    # 3. Create Holdout Split
    train_df, test_df = create_holdout_split(df)

    # Save validation set indices
    val_indices = {
        "test_indices": test_df.index.tolist(),
        "train_indices": train_df.index.tolist(),
        "train_size": len(train_df),
        "test_size": len(test_df)
    }
    val_path = output_path / "validation_set_indices.json"
    with open(val_path, 'w') as f:
        json.dump(val_indices, f, indent=2)
    logger.info(f"Saved validation set indices to {val_path}")

    # 4. Derive Threshold (on train set)
    base_threshold = derive_threshold(train_df)

    # 5. Evaluate on Test Set (Holdout)
    # Apply sweep on the TEST set to get unbiased metrics
    sweep_results = sweep_threshold(test_df, base_threshold)

    # 6. Generate Outputs
    # Save sensitivity table
    sens_df = pd.DataFrame(sweep_results)
    sens_csv_path = output_path / "sensitivity_table.csv"
    sens_df.to_csv(sens_csv_path, index=False)
    logger.info(f"Saved sensitivity table to {sens_csv_path}")

    # Save prediction results (best result from test set)
    # We pick the result closest to the base threshold for the final report
    final_result = next((r for r in sweep_results if abs(r['threshold'] - base_threshold) < 0.001), sweep_results[0])
    
    pred_results = {
        "base_threshold": float(base_threshold),
        "validation_split": {
            "train_size": len(train_df),
            "test_size": len(test_df)
        },
        "best_metrics_on_test": final_result
    }
    
    pred_path = output_path / "prediction_results.json"
    with open(pred_path, 'w') as f:
        json.dump(pred_results, f, indent=2)
    logger.info(f"Saved prediction results to {pred_path}")

    logger.info("Predictive threshold validation completed successfully.")

if __name__ == "__main__":
    main()