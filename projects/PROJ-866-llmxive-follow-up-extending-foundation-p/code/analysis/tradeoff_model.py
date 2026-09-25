import json
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Constants
VIF_THRESHOLD = 5.0
DEFAULT_OUTPUT_PATH = "data/results/vif_report.json"
RAW_DATA_PATH = "data/processed/full_context_logs.json"
COMPRESSED_DATA_PATH = "data/processed/compressed_context_logs.json"


def load_processed_logs(full_path: str, compressed_path: str) -> pd.DataFrame:
    """
    Load and merge full context and compressed context logs into a single DataFrame.
    """
    full_logs = []
    compressed_logs = []

    # Load full context logs
    if os.path.exists(full_path):
        with open(full_path, 'r') as f:
            full_logs = json.load(f)
    else:
        warnings.warn(f"Full context logs not found at {full_path}")

    # Load compressed context logs
    if os.path.exists(compressed_path):
        with open(compressed_path, 'r') as f:
            compressed_logs = json.load(f)
    else:
        warnings.warn(f"Compressed context logs not found at {compressed_path}")

    if not full_logs and not compressed_logs:
        raise FileNotFoundError("No logs found for analysis.")

    # Flatten and merge logs
    data = []
    for log in full_logs:
        data.append({
            'workflow_id': log.get('workflow_id'),
            'depth': log.get('compression_depth', 0),
            'context_reduction_pct': 0.0,  # Full context has 0% reduction
            'token_count': log.get('token_count', 0),
            'policy_violation_error_rate': 0.0 if log.get('is_valid', True) else 1.0,
            'complexity': log.get('metadata', {}).get('complexity', 0)
        })

    for log in compressed_logs:
        reduction = log.get('context_reduction_pct')
        if isinstance(reduction, str) and reduction == "[deferred]":
            continue  # Skip edge cases for VIF analysis
        data.append({
            'workflow_id': log.get('workflow_id'),
            'depth': log.get('compression_depth', 0),
            'context_reduction_pct': float(reduction),
            'token_count': log.get('token_count', 0),
            'policy_violation_error_rate': 1.0 if log.get('policy_violations') else 0.0,
            'complexity': log.get('metadata', {}).get('complexity', 0)
        })

    df = pd.DataFrame(data)
    return df


def filter_invalid_workflows_from_logs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out workflows that are marked as invalid in the logs.
    """
    # In this context, we assume 'policy_violation_error_rate' of 1.0 for invalid workflows
    # but we need to check the original logs for 'is_valid' flag if available.
    # For VIF analysis, we focus on valid workflows to avoid skewing the model.
    return df[df['policy_violation_error_rate'] < 1.0]


def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for specified features.
    """
    if df.empty:
        return {}

    # Add constant for intercept
    X = df[features].copy()
    X = sm.add_constant(X)

    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = float(vif)
        except Exception as e:
            warnings.warn(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('nan')

    return vif_data


def run_vif_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run VIF analysis on the dataframe for depth and complexity covariates.
    """
    features = ['depth', 'complexity']
    vif_results = calculate_vif(df, features)

    report = {
        "metric": "VIF",
        "threshold": VIF_THRESHOLD,
        "covariates": vif_results,
        "warnings": []
    }

    # Check for multicollinearity
    for covariate, value in vif_results.items():
        if not np.isnan(value) and value > VIF_THRESHOLD:
            msg = f"Multicollinearity detected for {covariate}: VIF = {value:.2f} (threshold = {VIF_THRESHOLD})"
            report["warnings"].append(msg)
            warnings.warn(msg)

    return report


def save_vif_report(report: Dict[str, Any], output_path: str = DEFAULT_OUTPUT_PATH) -> None:
    """
    Save the VIF report to a JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"VIF report saved to {output_path}")


def main() -> None:
    """
    Main function to run VIF analysis and save the report.
    """
    full_path = os.getenv('FULL_LOGS_PATH', RAW_DATA_PATH)
    compressed_path = os.getenv('COMPRESSED_LOGS_PATH', COMPRESSED_DATA_PATH)
    output_path = os.getenv('VIF_REPORT_PATH', DEFAULT_OUTPUT_PATH)

    try:
        df = load_processed_logs(full_path, compressed_path)
        if df.empty:
            warnings.warn("No data available for VIF analysis.")
            return

        df_valid = filter_invalid_workflows_from_logs(df)
        if df_valid.empty:
            warnings.warn("No valid workflows found for VIF analysis.")
            return

        report = run_vif_analysis(df_valid)
        save_vif_report(report, output_path)

    except Exception as e:
        print(f"Error during VIF analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()