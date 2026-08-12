import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.utils.logging import log_info, log_warning, log_error, log_critical

logger = logging.getLogger(__name__)

def verify_regression_inputs(
    error_rates_path: Path,
    features_path: Path
) -> Tuple[bool, Optional[str]]:
    """
    Pre-computation check for T050.
    Verifies that input files exist, IDs match, and no NaN/Inf values exist
    in critical columns before running the regression.

    Args:
        error_rates_path: Path to data/results/error_rates.csv
        features_path: Path to data/results/filtered_features.json

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
        If is_valid is False, error_message contains the reason for failure.
        If is_valid is True, error_message is None.
    """
    errors = []

    # 1. Check file existence
    if not error_rates_path.exists():
        errors.append(f"Error file not found: {error_rates_path}")
    if not features_path.exists():
        errors.append(f"Features file not found: {features_path}")

    if errors:
        log_critical(" ".join(errors))
        return False, "; ".join(errors)

    # 2. Load data
    try:
        error_df = pd.read_csv(error_rates_path)
    except Exception as e:
        msg = f"Failed to load error_rates.csv: {e}"
        log_critical(msg)
        return False, msg

    try:
        with open(features_path, 'r') as f:
            features_data = json.load(f)
    except Exception as e:
        msg = f"Failed to load filtered_features.json: {e}"
        log_critical(msg)
        return False, msg

    # 3. Validate structure of features
    if not isinstance(features_data, list):
        msg = "filtered_features.json must be a list of objects."
        log_critical(msg)
        return False, msg

    if len(features_data) == 0:
        msg = "filtered_features.json is empty."
        log_critical(msg)
        return False, msg

    # Convert features to DataFrame for comparison
    features_df = pd.DataFrame(features_data)

    # Ensure required columns exist in both
    # Assuming error_rates.csv has 'dataset_id' and 'error_rate'
    # Assuming features_json has 'dataset_id' and 'hurst' (or similar)
    # We need to align on 'dataset_id'

    id_col = 'dataset_id'

    if id_col not in error_df.columns:
        msg = f"Column '{id_col}' missing in error_rates.csv. Found: {list(error_df.columns)}"
        log_critical(msg)
        return False, msg

    if id_col not in features_df.columns:
        msg = f"Column '{id_col}' missing in filtered_features.json. Found: {list(features_df.columns)}"
        log_critical(msg)
        return False, msg

    # 4. Check for NaN/Inf in error_rates
    if error_df['error_rate'].isna().any():
        nan_indices = error_df[error_df['error_rate'].isna()][id_col].tolist()
        msg = f"NaN values found in 'error_rate' for dataset IDs: {nan_indices}"
        log_critical(msg)
        return False, msg

    if np.isinf(error_df['error_rate']).any():
        inf_indices = error_df[np.isinf(error_df['error_rate'])][id_col].tolist()
        msg = f"Inf values found in 'error_rate' for dataset IDs: {inf_indices}"
        log_critical(msg)
        return False, msg

    # 5. Check for NaN/Inf in Hurst (or primary predictor)
    # Determine the Hurst column name - usually 'hurst' based on T010a/T010b
    hurst_col = 'hurst'
    if hurst_col not in features_df.columns:
        # Try to find a column containing 'hurst'
        candidates = [c for c in features_df.columns if 'hurst' in c.lower()]
        if candidates:
            hurst_col = candidates[0]
        else:
            msg = f"Column '{hurst_col}' (or similar) missing in features. Found: {list(features_df.columns)}"
            log_critical(msg)
            return False, msg

    if features_df[hurst_col].isna().any():
        nan_indices = features_df[features_df[hurst_col].isna()][id_col].tolist()
        msg = f"NaN values found in '{hurst_col}' for dataset IDs: {nan_indices}"
        log_critical(msg)
        return False, msg

    if np.isinf(features_df[hurst_col]).any():
        inf_indices = features_df[np.isinf(features_df[hurst_col])][id_col].tolist()
        msg = f"Inf values found in '{hurst_col}' for dataset IDs: {inf_indices}"
        log_critical(msg)
        return False, msg

    # 6. Verify ID alignment (Inner Join check)
    error_ids = set(error_df[id_col].astype(str))
    feature_ids = set(features_df[id_col].astype(str))

    missing_in_features = error_ids - feature_ids
    missing_in_errors = feature_ids - error_ids

    if missing_in_features or missing_in_features:
        msg_parts = []
        if missing_in_features:
            msg_parts.append(f"IDs in errors but not features: {sorted(list(missing_in_features))[:10]}...")
        if missing_in_errors:
            msg_parts.append(f"IDs in features but not errors: {sorted(list(missing_in_errors))[:10]}...")
        
        full_msg = f"Dataset ID mismatch detected. {', '.join(msg_parts)}"
        log_critical(full_msg)
        return False, full_msg

    log_info("Regression input verification passed: IDs match, no NaN/Inf in critical columns.")
    return True, None

def run_regression(
    error_rates_path: Path,
    features_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Runs the linear regression analysis for T037a.
    First calls verify_regression_inputs. If verification fails, raises ValueError.
    """
    # Pre-computation check (T050)
    is_valid, error_msg = verify_regression_inputs(error_rates_path, features_path)
    if not is_valid:
        log_critical(f"Regression aborted due to input verification failure: {error_msg}")
        raise ValueError(f"Input verification failed: {error_msg}")

    # Load data
    error_df = pd.read_csv(error_rates_path)
    with open(features_path, 'r') as f:
        features_data = json.load(f)
    features_df = pd.DataFrame(features_data)

    # Merge on dataset_id
    merged = pd.merge(error_df, features_df, on='dataset_id')

    # Identify columns
    y_col = 'error_rate'
    x_col = 'hurst' # As per spec, regressing error rate vs Hurst

    # Prepare X and y
    X = merged[[x_col]]
    y = merged[y_col]

    # Add constant for intercept
    X = sm.add_constant(X)

    # Fit model
    model = sm.OLS(y, X).fit()

    # Calculate VIF
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col != 'const':
            vif_data[col] = variance_inflation_factor(X.values, i)

    # Calculate N_eff approximation (1 / (1 + 2*sum(ACF))) - simplified for this task
    # Since we don't have full ACF here, we might estimate or skip if not available in merged
    # The spec says calculate N_eff, but T037c handles the calculation.
    # We will assume N_eff is calculated elsewhere or use a placeholder if not in features.
    # However, T037c calculates it. Let's assume it's in the features if needed, or we skip.
    # For this task, we output the regression stats.
    
    result = {
        "slope": float(model.params[x_col]),
        "intercept": float(model.params['const']),
        "p_value": float(model.pvalues[x_col]),
        "r_squared": float(model.rsquared),
        "slope_per_01_unit": float(model.params[x_col] * 0.1),
        "vif": vif_data.get(x_col, None),
        "n_eff": None # Placeholder, should be populated from T037c if available in features
    }

    # If n_eff is in the features, we can pull it
    if 'n_eff' in merged.columns:
        result['n_eff'] = float(merged['n_eff'].mean())

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    log_info(f"Regression model saved to {output_path}")
    return result

def main():
    """
    Entry point for running the regression verification and execution.
    """
    project_root = Path(__file__).resolve().parents[2]
    error_rates_path = project_root / "data" / "results" / "error_rates.csv"
    features_path = project_root / "data" / "results" / "filtered_features.json"
    output_path = project_root / "data" / "results" / "regression_model.json"

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Run verification first
        is_valid, error_msg = verify_regression_inputs(error_rates_path, features_path)
        if not is_valid:
            sys.exit(1)

        # Run regression
        run_regression(error_rates_path, features_path, output_path)
        sys.exit(0)
    except Exception as e:
        log_critical(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()