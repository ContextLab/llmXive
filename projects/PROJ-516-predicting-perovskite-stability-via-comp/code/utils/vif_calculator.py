"""
Variance Inflation Factor (VIF) Calculator for Perovskite Stability Descriptors.

Computes VIF for all numeric descriptor columns in the dataset to detect
multicollinearity. Writes a report to data/processed/vif_report.csv.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = Path("data/processed/descriptors_v1.csv")
OUTPUT_PATH = Path("data/processed/vif_report.csv")
VIF_THRESHOLD = 5.0  # Threshold for flagging high multicollinearity

def calculate_vif(data: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for each feature in the dataframe.

    Args:
        data: DataFrame containing the features.
        feature_cols: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    # Ensure we have a numeric subset
    X = data[feature_cols].copy()
    
    # Handle constant columns (VIF is undefined for constant columns)
    # Replace constant columns with NaN temporarily for calculation, then handle
    for col in X.columns:
        if X[col].std() == 0:
            logger.warning(f"Column {col} is constant. VIF is undefined. Setting to NaN.")
            X[col] = np.nan

    # Drop rows with any NaN (from constant columns or missing data)
    # Note: In a real production pipeline, we might want to handle this more gracefully
    # by imputing or excluding specific rows, but for VIF calculation, we need complete cases.
    X_complete = X.dropna()

    if len(X_complete) < X.shape[0]:
        logger.warning(f"Dropped {X.shape[0] - len(X_complete)} rows due to NaN values during VIF calculation.")

    if len(X_complete) < 2:
        raise ValueError("Not enough data points to calculate VIF (need at least 2).")

    vif_results = {}
    for i, col in enumerate(X_complete.columns):
        try:
            # Calculate VIF: VIF = 1 / (1 - R^2) where R^2 is from regressing col against all other cols
            # We use a simple linear regression approach to compute R^2 manually to avoid statsmodels dependency issues
            # if statsmodels is not available, though the task implies it might be.
            # However, to be robust and avoid external dependencies beyond standard sklearn/pandas/numpy:
            # R^2 for feature i regressed on others:
            y = X_complete.iloc[:, i].values
            X_other = X_complete.drop(X_complete.columns[i], axis=1).values
            
            # Add intercept
            X_other_with_intercept = np.column_stack([np.ones(X_other.shape[0]), X_other])
            
            # Solve least squares: beta = (X'X)^-1 X'y
            try:
                beta = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)[0]
                y_pred = X_other_with_intercept @ beta
                
                ss_res = np.sum((y - y_pred) ** 2)
                ss_tot = np.sum((y - np.mean(y)) ** 2)
                
                if ss_tot == 0:
                    r_squared = 0.0
                else:
                    r_squared = 1 - (ss_res / ss_tot)
                
                # Avoid division by zero if R^2 is exactly 1 (perfect collinearity)
                if r_squared >= 1.0:
                    vif = float('inf')
                else:
                    vif = 1.0 / (1.0 - r_squared)
                
                vif_results[col] = vif
            except np.linalg.LinAlgError:
                # Singular matrix, likely perfect collinearity
                vif_results[col] = float('inf')
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results[col] = np.nan

    return vif_results

def run_vif_diagnostic(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
    threshold: float = VIF_THRESHOLD
) -> pd.DataFrame:
    """
    Run VIF diagnostic on the dataset and write the report.

    Args:
        input_path: Path to the input CSV file.
        output_path: Path to write the VIF report CSV.
        threshold: VIF threshold above which a feature is flagged.

    Returns:
        DataFrame containing the VIF report.
    """
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)
    
    # Identify numeric descriptor columns (exclude non-numeric and target columns)
    # We need to be careful to select only the feature columns used for regression
    # Based on T014e, the descriptors are:
    # atomic_fraction_A, atomic_fraction_B, atomic_fraction_X,
    # weighted_ionic_radius, weighted_electronegativity, weighted_formation_enthalpy,
    # first_ionization_energy, variance_ionic_radius, variance_electronegativity
    # Plus potentially 'T_d' (target) and 'total_uncertainty' (weight) and categorical fields.
    
    exclude_cols = ['formula', 'T_d', 'total_uncertainty', 'perovskite_family', 
                    'instrument_model', 'manufacturer', 'precision_source']
                    
    feature_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not feature_cols:
        raise ValueError("No numeric feature columns found for VIF calculation.")
    
    logger.info(f"Calculating VIF for {len(feature_cols)} features: {feature_cols}")

    vif_results = calculate_vif(df, feature_cols)

    # Create report DataFrame
    report_data = []
    for col, vif_val in vif_results.items():
        # Handle infinity for flagging
        is_flagged = False
        if np.isinf(vif_val) or (not np.isnan(vif_val) and vif_val > threshold):
            is_flagged = True
        
        report_data.append({
            'descriptor': col,
            'vif_value': vif_val,
            'flagged': is_flagged
        })

    report_df = pd.DataFrame(report_data)
    
    # Sort by VIF value descending (handling inf and nan)
    # Replace inf with a large number for sorting, then restore
    sort_vals = report_df['vif_value'].replace([np.inf, -np.inf], np.nan).fillna(-1)
    report_df = report_df.iloc[sort_vals.argsort()[::-1]].reset_index(drop=True)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing VIF report to {output_path}")
    report_df.to_csv(output_path, index=False)
    
    # Log summary
    flagged_count = report_df['flagged'].sum()
    logger.info(f"VIF calculation complete. {flagged_count} features flagged (VIF > {threshold}).")
    
    return report_df

def main():
    """Main entry point for the VIF calculator script."""
    try:
        run_vif_diagnostic()
        logger.info("VIF diagnostic completed successfully.")
    except Exception as e:
        logger.error(f"VIF diagnostic failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
