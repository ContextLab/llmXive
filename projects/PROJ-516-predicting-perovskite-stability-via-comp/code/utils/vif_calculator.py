"""
Variance Inflation Factor (VIF) Calculator for Perovskite Descriptors.

Computes VIF for all descriptor features to identify multicollinearity.
Reads from data/processed/descriptors_filtered.csv and writes the report
to data/processed/vif_report.csv.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

INPUT_PATH = Path("data/processed/descriptors_filtered.csv")
OUTPUT_PATH = Path("data/processed/vif_report.csv")
VIF_THRESHOLD = 5.0

def calculate_vif(df: pd.DataFrame, feature_names: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.

    VIF_i = 1 / (1 - R^2_i) where R^2_i is the coefficient of determination
    when feature i is regressed against all other features.

    Args:
        df: DataFrame containing the features.
        feature_names: List of column names to compute VIF for.

    Returns:
        pd.Series: VIF values indexed by feature name.
    """
    logger.info(f"Calculating VIF for {len(feature_names)} features...")

    # Select only numeric columns for VIF calculation
    X = df[feature_names].copy()

    # Remove constant columns (VIF is undefined for constants)
    constant_cols = [col for col in X.columns if X[col].std() == 0]
    if constant_cols:
        logger.warning(f"Removing constant columns: {constant_cols}")
        X = X.drop(columns=constant_cols)

    vif_results = {}

    for i, col in enumerate(X.columns):
        # Regress col against all other columns
        y = X[col]
        X_other = X.drop(columns=[col])

        # Fit linear regression
        # Add intercept
        X_other_with_intercept = X_other.copy()
        X_other_with_intercept['intercept'] = 1.0

        try:
            # Use least squares: beta = (X^T X)^-1 X^T y
            # We need R^2 from this regression
            model = stats.linregress(X_other_with_intercept.values, y.values)
            # Note: linregress only works for single predictor.
            # For multiple predictors, we use numpy.linalg.lstsq
            pass
        except Exception:
            pass

        # Use numpy for multiple regression
        try:
            # Add intercept column
            X_design = np.column_stack([np.ones(len(X_other)), X_other.values])
            coeffs, residuals, rank, s = np.linalg.lstsq(X_design, y.values, rcond=None)

            if len(y) > X_design.shape[1]:
                # Calculate R^2
                y_pred = X_design @ coeffs
                ss_res = np.sum((y.values - y_pred) ** 2)
                ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)

                if ss_tot == 0:
                    r_squared = 0.0
                else:
                    r_squared = 1.0 - (ss_res / ss_tot)

                # VIF = 1 / (1 - R^2)
                if r_squared >= 1.0:
                    vif_value = float('inf')
                else:
                    vif_value = 1.0 / (1.0 - r_squared)
            else:
                vif_value = float('inf')

        except np.linalg.LinAlgError:
            logger.warning(f"Singularity detected for {col}, VIF undefined (inf)")
            vif_value = float('inf')
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_value = float('nan')

        vif_results[col] = vif_value

    return pd.Series(vif_results)

def run_vif_diagnostic(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
    threshold: float = VIF_THRESHOLD
) -> pd.DataFrame:
    """
    Run the full VIF diagnostic pipeline.

    1. Load the filtered descriptor dataset.
    2. Identify numeric descriptor columns.
    3. Calculate VIF for each.
    4. Flag features with VIF > threshold.
    5. Write the report to disk.

    Args:
        input_path: Path to the input CSV.
        output_path: Path to the output CSV report.
        threshold: VIF threshold for flagging (default 5.0).

    Returns:
        DataFrame containing the VIF report.
    """
    logger.info(f"Loading data from {input_path}...")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    # Identify descriptor columns (exclude target and metadata)
    exclude_cols = {'formula', 'T_d', 'total_uncertainty', 'perovskite_family',
                    'instrument_model', 'manufacturer', 'source', 'precision_source'}
    descriptor_cols = [col for col in df.columns if col not in exclude_cols and np.issubdtype(df[col].dtype, np.number)]

    if not descriptor_cols:
        raise ValueError("No numeric descriptor columns found in the dataset.")

    logger.info(f"Computing VIF for {len(descriptor_cols)} descriptors: {descriptor_cols}")

    vif_series = calculate_vif(df, descriptor_cols)

    # Create report DataFrame
    report_df = pd.DataFrame({
        'descriptor': vif_series.index,
        'vif_value': vif_series.values,
        'flagged': vif_series.values > threshold
    })

    # Sort by VIF descending
    report_df = report_df.sort_values(by='vif_value', ascending=False).reset_index(drop=True)

    # Write to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)
    logger.info(f"VIF report written to {output_path}")

    # Log summary
    flagged_count = report_df['flagged'].sum()
    logger.info(f"Found {flagged_count} features with VIF > {threshold}.")

    return report_df

def main():
    """Entry point for the VIF calculator script."""
    try:
        run_vif_diagnostic()
        logger.info("VIF calculation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
