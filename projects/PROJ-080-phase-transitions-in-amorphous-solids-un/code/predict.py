import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

from utils import set_seed
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
SEED = 42

def load_analysis_results(input_dir: Path) -> Dict:
    """Load the significance report and threshold derived from US2/US3 setup."""
    report_path = input_dir / "significance_report.json"
    threshold_path = input_dir / "threshold_value.json" # Expected output from T028a

    if not report_path.exists():
        raise FileNotFoundError(f"Significance report not found at {report_path}")
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    if not threshold_path.exists():
        # Fallback or error if T028a didn't produce this specific file
        # Depending on T028a implementation, it might be embedded in another file.
        # Assuming T028a writes a specific file as per spec.
        raise FileNotFoundError(f"Derived threshold not found at {threshold_path}")
    
    with open(threshold_path, 'r') as f:
        threshold_data = json.load(f)
    
    return {
        "report": report,
        "threshold": threshold_data.get("threshold_value")
    }

def derive_threshold(analysis_results: Dict) -> float:
    """
    Returns the derived threshold. 
    In a full pipeline, this would be calculated from the training set F-score max.
    Here we retrieve it from the T028a output.
    """
    return analysis_results["threshold"]

def create_holdout_split(input_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the precursor metrics and split into train/validation based on T028a indices.
    """
    metrics_path = input_dir / "precursor_metrics.csv"
    indices_path = input_dir / "validation_set_indices.json"

    if not metrics_path.exists():
        raise FileNotFoundError(f"Precursor metrics not found at {metrics_path}")
    if not indices_path.exists():
        raise FileNotFoundError(f"Validation indices not found at {indices_path}")

    df = pd.read_csv(metrics_path)

    with open(indices_path, 'r') as f:
        indices_data = json.load(f)

    val_indices = indices_data.get("validation_indices", [])
    train_indices = indices_data.get("train_indices", [])

    if not val_indices or not train_indices:
        raise ValueError("Validation or Training indices are empty.")

    train_df = df.iloc[train_indices].reset_index(drop=True)
    val_df = df.iloc[val_indices].reset_index(drop=True)

    return train_df, val_df

def define_time_to_failure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Define 'time-to-failure' as total strain at catastrophic failure.
    For this dataset, we assume a column 'total_strain_at_failure' exists or 
    can be derived. If not present, we use the 'strain' column max as a proxy 
    for the specific trajectory's failure point, or a labeled column.
    
    Spec: 'time-to-failure' is independent ground truth.
    We assume the dataset has a label 'brittle' vs 'ductile' and a failure strain.
    """
    # Check if failure strain is already present
    if 'failure_strain' in df.columns:
        return df
    
    # If not, we might need to infer from the trajectory data or use a proxy.
    # For this implementation, we assume the 'precursor_metrics.csv' has a 
    # 'yield_strain' or similar that serves as the event time, or we use the 
    # 'strain' at the yield point.
    # However, T028b defines it. We will assume the input DF has a column 
    # 'time_to_failure' or 'failure_strain'. If not, we raise an error 
    # or use a placeholder if the data loader provided it.
    
    # Fallback: If the data loader (T043) provided 'total_strain', use that.
    # Since we are processing metrics, we assume the 'yield_strain' is the 
    # point of interest, but 'time-to-failure' is the total strain.
    # Let's assume the dataset has a 'failure_strain' column.
    
    if 'failure_strain' not in df.columns:
        # Attempt to map common names
        if 'total_strain' in df.columns:
            df['failure_strain'] = df['total_strain']
        else:
            # If strictly missing, we cannot calculate real metrics.
            # We will raise an error to avoid fabrication.
            raise ValueError("Column 'failure_strain' or 'total_strain' not found in input data. Cannot define time-to-failure.")
    
    return df

def sweep_threshold(
    base_threshold: float, 
    df: pd.DataFrame, 
    output_path: Path
) -> pd.DataFrame:
    """
    Sweep D^2_min threshold over {threshold - 0.05, threshold, threshold + 0.05}.
    Calculate FPR, FNR, F1, TP, TN for each.
    """
    set_seed(SEED)
    
    # Define the sweep range as mandated by FR-004
    offsets = [-0.05, 0.0, 0.05]
    thresholds = [base_threshold + offset for offset in offsets]
    
    results = []
    
    # We need ground truth labels. Assuming 'label' column: 1 for brittle (failure), 0 for ductile.
    # Or 'is_brittle'. Let's assume 'label' exists in the metrics DF.
    if 'label' not in df.columns:
        # Try common alternatives
        if 'is_brittle' in df.columns:
            y_true = df['is_brittle'].astype(int)
        else:
            raise ValueError("Ground truth label column ('label' or 'is_brittle') not found in input data.")
    else:
        y_true = df['label'].astype(int)
    
    # Ground truth for failure: 1 if brittle (failure occurs), 0 if ductile.
    # Prediction: 1 if D2_min > threshold (predicts failure), 0 otherwise.
    
    for thresh in thresholds:
        # Predictions
        y_pred = (df['d2_min'] > thresh).astype(int)
        
        # Confusion Matrix components
        TP = ((y_pred == 1) & (y_true == 1)).sum()
        TN = ((y_pred == 0) & (y_true == 0)).sum()
        FP = ((y_pred == 1) & (y_true == 0)).sum()
        FN = ((y_pred == 0) & (y_true == 1)).sum()
        
        # Rates
        # FPR = FP / (FP + TN)
        # FNR = FN / (FN + TP)
        # F1 = 2 * (Precision * Recall) / (Precision + Recall)
        
        fpr = FP / (FP + TN) if (FP + TN) > 0 else 0.0
        fnr = FN / (FN + TP) if (FN + TP) > 0 else 0.0
        
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results.append({
            "threshold": thresh,
            "TP": int(TP),
            "TN": int(TN),
            "FP": int(FP),
            "FN": int(FN),
            "FPR": fpr,
            "FNR": fnr,
            "F1": f1
        })
    
    results_df = pd.DataFrame(results)
    
    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity table written to {output_path}")
    
    return results_df

def main():
    parser = argparse.ArgumentParser(description="Run threshold sensitivity sweep for US3.")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing processed data")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory for output artifacts")
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    try:
        # 1. Load analysis results (threshold from T028a)
        logger.info("Loading derived threshold and analysis results...")
        analysis_results = load_analysis_results(input_path)
        base_threshold = derive_threshold(analysis_results)
        logger.info(f"Using derived base threshold: {base_threshold}")

        # 2. Load data (Validation set or full set if split handled in T028a)
        # T029 depends on T028a which created the split. We load the full metrics 
        # and the split indices to ensure we are evaluating on the correct set 
        # (usually validation set for final reporting, but spec says sweep over 
        # the range to generate the table. We'll use the validation set for the 
        # final sensitivity table if available, or the full set if indices not 
        # strictly required for the sweep itself, but T028a says 'hold-out split'.
        # We will use the validation set for the final metrics to avoid leakage.
        
        logger.info("Loading validation data...")
        train_df, val_df = create_holdout_split(input_path)
        
        # 3. Define time-to-failure (ground truth)
        logger.info("Defining time-to-failure ground truth...")
        val_df = define_time_to_failure(val_df)

        # 4. Perform Sweep
        output_file = output_path / "sensitivity_table.csv"
        logger.info(f"Starting threshold sweep around {base_threshold}...")
        sweep_df = sweep_threshold(base_threshold, val_df, output_file)

        logger.info("Sensitivity analysis complete.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()