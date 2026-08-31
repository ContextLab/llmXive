"""
Regression Analysis Module for Sensitivity of Regression Coefficients.

This module implements the theoretical baseline calculations and meta-analysis
for assessing how dataset subset selection impacts regression coefficient stability.
"""

import json
import os
import sys
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


def calculate_theoretical_variance(condition_number: float, residual_variance: float = 1.0) -> float:
    """
    Calculate the theoretical variance of OLS coefficients predicted by the condition number alone.

    Under homoscedastic OLS assumptions, the variance of the coefficient estimates is:
    Var(beta_hat) = sigma^2 * (X'X)^-1

    The condition number (kappa) of the design matrix X is the ratio of the largest
    to smallest singular value. The variance inflation due to multicollinearity
    can be approximated by the square of the condition number relative to an
    orthogonal design.

    Theoretical Variance ~ sigma^2 * kappa^2 / N
    (Simplified approximation for sensitivity baseline)

    Args:
        condition_number: The condition number of the design matrix.
        residual_variance: The estimated variance of the residuals (sigma^2).
                           Defaults to 1.0 for a normalized baseline.

    Returns:
        float: Theoretical variance of the coefficients.
    """
    if condition_number <= 0:
        raise ValueError("Condition number must be positive.")

    # Theoretical variance scales with the square of the condition number
    # This reflects the amplification of error in the presence of multicollinearity
    theoretical_var = residual_variance * (condition_number ** 2)

    return theoretical_var


def load_stability_results(artifacts_dir: str) -> pd.DataFrame:
    """
    Load empirical stability results from the artifacts directory.

    Expected file: artifacts/stability/coefficient_sd.json
    This file contains the empirical standard deviation of coefficients
    across subsets for each dataset and sample size tier.

    Args:
        artifacts_dir: Path to the artifacts directory.

    Returns:
        pd.DataFrame: DataFrame containing empirical variance and metadata.
    """
    file_path = Path(artifacts_dir) / "stability" / "coefficient_sd.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Stability results not found at {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(data)

    # Ensure variance column exists (square of std dev)
    if 'coefficient_std_dev' in df.columns:
        df['empirical_variance'] = df['coefficient_std_dev'] ** 2
    else:
        raise KeyError("Missing 'coefficient_std_dev' column in stability results.")

    return df


def load_dataset_profiles(artifacts_dir: str) -> pd.DataFrame:
    """
    Load dataset profiles containing condition numbers and violation severities.

    Expected file: artifacts/profiles/dataset_profiles.json

    Args:
        artifacts_dir: Path to the artifacts directory.

    Returns:
        pd.DataFrame: DataFrame containing condition numbers and profile metadata.
    """
    file_path = Path(artifacts_dir) / "profiles" / "dataset_profiles.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset profiles not found at {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    if 'condition_number' not in df.columns:
        raise KeyError("Missing 'condition_number' column in dataset profiles.")

    return df


def calculate_theoretical_baseline(artifacts_dir: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate the theoretical variance predicted by condition number alone for each dataset.

    This function:
    1. Loads dataset profiles (containing condition numbers).
    2. Loads empirical stability results (containing observed variance).
    3. Calculates theoretical variance using the homoscedastic OLS formula.
    4. Compares empirical vs theoretical variance.
    5. Saves the results to a JSON file.

    Args:
        artifacts_dir: Path to the artifacts directory.
        output_path: Optional path to save the results. Defaults to
                     artifacts/meta_analysis/theoretical_baseline.json.

    Returns:
        Dict[str, Any]: Dictionary containing the calculated baselines and comparisons.
    """
    profiles_df = load_dataset_profiles(artifacts_dir)
    stability_df = load_stability_results(artifacts_dir)

    # Merge on dataset identifier (assuming 'dataset_id' or similar column exists)
    # Adjust column name based on actual schema if different
    merge_key = 'dataset_id' if 'dataset_id' in profiles_df.columns else 'dataset_name'

    if merge_key not in stability_df.columns:
        # Try to infer from stability_df columns if dataset_id is missing
        # This is a fallback; ideally, the schema should be consistent
        available_keys = [c for c in stability_df.columns if 'dataset' in c.lower()]
        if available_keys:
            merge_key = available_keys[0]
        else:
            raise ValueError("Could not find a common key to merge profiles and stability results.")

    merged_df = pd.merge(profiles_df, stability_df, on=merge_key, how='inner')

    results = []

    for _, row in merged_df.iterrows():
        dataset_id = row[merge_key]
        condition_number = row['condition_number']
        empirical_variance = row['empirical_variance']

        # Calculate theoretical variance
        # Assuming residual variance is approximated by the empirical variance
        # if not provided separately, or set to a baseline of 1.0
        theoretical_variance = calculate_theoretical_variance(condition_number, residual_variance=1.0)

        # Calculate ratio (Empirical / Theoretical)
        # If theoretical is 0 or very small, handle division by zero
        if theoretical_variance < 1e-10:
            ratio = float('inf') if empirical_variance > 0 else 1.0
        else:
            ratio = empirical_variance / theoretical_variance

        results.append({
            'dataset_id': dataset_id,
            'condition_number': condition_number,
            'empirical_variance': empirical_variance,
            'theoretical_variance': theoretical_variance,
            'variance_ratio': ratio,
            'violation_severity': row.get('violation_severity', 'unknown')
        })

    output_data = {
        'description': 'Theoretical baseline variance calculation based on condition number.',
        'formula': 'Var_theoretical = sigma^2 * kappa^2',
        'results': results
    }

    if output_path is None:
        output_path = os.path.join(artifacts_dir, 'meta_analysis', 'theoretical_baseline.json')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    return output_data


def main():
    """Main entry point for the theoretical baseline calculation."""
    # Default paths relative to project root
    base_dir = Path(__file__).resolve().parent.parent.parent
    artifacts_dir = base_dir / 'artifacts'

    print(f"Calculating theoretical baseline using artifacts from: {artifacts_dir}")

    try:
        results = calculate_theoretical_baseline(str(artifacts_dir))
        print(f"Baseline calculation complete. Results saved to: {artifacts_dir}/meta_analysis/theoretical_baseline.json")
        print(f"Processed {len(results['results'])} datasets.")

        # Print a summary
        for res in results['results']:
            print(f"Dataset: {res['dataset_id']}, CondNum: {res['condition_number']:.2f}, "
                  f"EmpVar: {res['empirical_variance']:.4f}, TheoVar: {res['theoretical_variance']:.4f}, "
                  f"Ratio: {res['variance_ratio']:.4f}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required data column - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()