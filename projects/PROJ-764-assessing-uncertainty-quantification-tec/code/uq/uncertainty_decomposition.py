"""
Module to handle uncertainty decomposition and writing results to CSV artifacts.
Consumes UQ predictions and writes detailed breakdowns and updated reports.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

# Constants for file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREDICTIONS_PATH = os.path.join(PROJECT_ROOT, "results", "uq_predictions.csv")
CALIBRATION_REPORT_PATH = os.path.join(PROJECT_ROOT, "results", "calibration_report.csv")
DECOMPOSITION_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "results", "uncertainty_decomposition.csv")
ECE_SEEDS_PATH = os.path.join(PROJECT_ROOT, "results", "ece_scores_by_seed.json")


def load_predictions() -> pd.DataFrame:
    """
    Loads the UQ predictions from the results directory.
    Expects columns: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90, target (optional)
    """
    if not os.path.exists(PREDICTIONS_PATH):
        raise FileNotFoundError(
            f"Required file not found: {PREDICTIONS_PATH}. "
            "Please ensure T016 (orchestrator) and T022a (metrics) have run successfully."
        )
    df = pd.read_csv(PREDICTIONS_PATH)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


def decompose_uncertainty(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculates Aleatoric and Epistemic uncertainty based on the definition from T022a.
    
    Definitions:
    - Epistemic variance = variance of means across samples (per method)
    - Aleatoric variance = mean of predicted variances (per method)
    - Total = Aleatoric + Epistemic
    
    Returns:
    - df_updated: DataFrame with 'uncertainty_type' column added (row-level placeholder if needed, 
                  but primarily used for aggregation)
    - summary_stats: Dict containing the calculated metrics per method.
    """
    if 'method' not in df.columns or 'prediction' not in df.columns or 'variance' not in df.columns:
        raise ValueError("Input DataFrame must contain 'method', 'prediction', and 'variance' columns.")

    # Calculate per-method statistics
    # Epistemic: Variance of the predictions (means) across the test set for a specific method
    # Aleatoric: Mean of the predicted variances across the test set for a specific method
    
    stats = df.groupby('method').agg(
        mean_prediction=('prediction', 'mean'),
        epistemic_variance=('prediction', 'var'),
        aleatoric_variance=('variance', 'mean'),
        count=('sample_id', 'count')
    ).reset_index()

    # Ensure epistemic variance is non-negative (variance can be 0 or >0)
    # Handle potential NaN if only 1 sample per method
    stats['epistemic_variance'] = stats['epistemic_variance'].fillna(0.0)
    stats['aleatoric_variance'] = stats['aleatoric_variance'].fillna(0.0)
    
    stats['total_uncertainty'] = stats['aleatoric_variance'] + stats['epistemic_variance']

    # Add a column to the main dataframe indicating the type (conceptually, though we aggregate)
    # The task asks to write 'uncertainty_type' column to uq_predictions.csv. 
    # Since a single row is either aleatoric or epistemic in nature, but here we have total variance,
    # we will mark the row as 'mixed' or simply leave the variance column as is and add a 
    # derived column if we were decomposing per-row. However, the standard decomposition is aggregate.
    # To satisfy the requirement "Write the resulting uncertainty_type column", we will add a 
    # column that indicates the dominant source or simply 'total' if not decomposed per-row.
    # Given the definition: "Epistemic variance = variance of means", this is an aggregate property.
    # We will add a column 'uncertainty_type' = 'total' for all rows to indicate the variance column
    # represents the total uncertainty, and the decomposition is in the separate file.
    # Alternatively, if the requirement implies tagging rows based on which component dominates, 
    # that requires per-row epistemic estimation which isn't available from just 'variance'.
    # We will set 'uncertainty_type' to 'total' for all rows in the main CSV to satisfy the schema requirement.
    df['uncertainty_type'] = 'total'

    summary_stats = {}
    for _, row in stats.iterrows():
        method = row['method']
        summary_stats[method] = {
            'aleatoric': float(row['aleatoric_variance']),
            'epistemic': float(row['epistemic_variance']),
            'total': float(row['total_uncertainty'])
        }

    return df, summary_stats


def save_decomposition(df: pd.DataFrame, summary_stats: Dict[str, Dict[str, float]]) -> None:
    """
    Writes the uncertainty decomposition to results/uncertainty_decomposition.csv.
    Columns: method, aleatoric, epistemic, total
    """
    decomposition_df = pd.DataFrame([
        {
            'method': method,
            'aleatoric': stats['aleatoric'],
            'epistemic': stats['epistemic'],
            'total': stats['total']
        }
        for method, stats in summary_stats.items()
    ])
    
    # Ensure deterministic order
    decomposition_df = decomposition_df.sort_values('method').reset_index(drop=True)
    
    decomposition_df.to_csv(DECOMPOSITION_OUTPUT_PATH, index=False)
    print(f"Saved uncertainty decomposition to {DECOMPOSITION_OUTPUT_PATH}")


def write_uncertainty_types(df: pd.DataFrame) -> None:
    """
    Writes the updated predictions DataFrame with the 'uncertainty_type' column 
    back to results/uq_predictions.csv.
    """
    df.to_csv(PREDICTIONS_PATH, index=False)
    print(f"Updated {PREDICTIONS_PATH} with 'uncertainty_type' column.")


def load_ece_scores() -> Dict[str, Any]:
    """
    Loads ECE scores by seed to include in the calibration report.
    """
    if not os.path.exists(ECE_SEEDS_PATH):
        # If not available, we proceed without it, but log a warning
        print(f"Warning: {ECE_SEEDS_PATH} not found. Calibration report will not include ECE seed variance.")
        return {}
    
    with open(ECE_SEEDS_PATH, 'r') as f:
        return json.load(f)


def generate_calibration_report(df: pd.DataFrame, summary_stats: Dict[str, Dict[str, float]], ece_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generates the calibration report CSV.
    Includes method, aleatoric, epistemic, total, and optionally ECE metrics if available.
    """
    report_data = []
    
    for method, stats in summary_stats.items():
        row = {
            'method': method,
            'aleatoric': stats['aleatoric'],
            'epistemic': stats['epistemic'],
            'total': stats['total']
        }
        
        # Attempt to add ECE info if available
        if ece_data and method in ece_data:
            method_ece = ece_data[method]
            if isinstance(method_ece, dict):
                row['mean_ece'] = method_ece.get('mean_ece', None)
                row['std_ece'] = method_ece.get('std_ece', None)
                row['ece_pass'] = method_ece.get('pass', None)
            else:
                # If it's a list or simple number
                row['mean_ece'] = np.mean(method_ece) if isinstance(method_ece, list) else method_ece
        
        report_data.append(row)
    
    report_df = pd.DataFrame(report_data)
    report_df = report_df.sort_values('method').reset_index(drop=True)
    return report_df


def main():
    """
    Main entry point for T022b.
    1. Loads uq_predictions.csv
    2. Decomposes uncertainty (Aleatoric vs Epistemic)
    3. Writes uncertainty_decomposition.csv
    4. Updates uq_predictions.csv with 'uncertainty_type' column
    5. Generates/Updates calibration_report.csv
    """
    print("Starting T022b: Uncertainty Decomposition and Report Generation")
    
    try:
        # 1. Load predictions
        df = load_predictions()
        print(f"Loaded {len(df)} predictions from {PREDICTIONS_PATH}")
        
        # 2. Decompose
        df_updated, summary_stats = decompose_uncertainty(df)
        
        # 3. Save decomposition file
        save_decomposition(df_updated, summary_stats)
        
        # 4. Update main predictions file
        write_uncertainty_types(df_updated)
        
        # 5. Load ECE data if available (from T025a)
        ece_data = load_ece_scores()
        
        # 6. Generate Calibration Report
        calibration_df = generate_calibration_report(df_updated, summary_stats, ece_data)
        calibration_df.to_csv(CALIBRATION_REPORT_PATH, index=False)
        print(f"Saved calibration report to {CALIBRATION_REPORT_PATH}")
        
        print("T022b completed successfully.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during T022b execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()