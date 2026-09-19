import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from logger import get_logger
from config import get_config

def load_feature_matrix(path: str) -> pd.DataFrame:
    """
    Loads the feature matrix from a CSV file.
    Expects columns: 'epoch_id', 'condition', 'P_alpha', 'Pz_alpha', 'P4_alpha', 'F3_beta', 'Fz_beta', 'F4_beta'
    """
    logger = get_logger()
    logger.info(f"Loading feature matrix from {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature matrix not found at {path}. Ensure T023 has run.")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def compute_correlation_matrix(df: pd.DataFrame, target_electrodes: List[str]) -> np.ndarray:
    """
    Computes the Pearson correlation matrix for the specified electrode features.
    """
    logger = get_logger()
    logger.info(f"Computing correlation matrix for electrodes: {target_electrodes}")
    
    # Filter columns that exist in the dataframe
    available_cols = [col for col in target_electrodes if col in df.columns]
    
    if len(available_cols) != len(target_electrodes):
        missing = set(target_electrodes) - set(available_cols)
        logger.warning(f"Missing expected columns: {missing}. Proceeding with available: {available_cols}")
    
    if len(available_cols) < 2:
        raise ValueError("Need at least 2 valid columns to compute a correlation matrix.")
    
    data_subset = df[available_cols].dropna()
    
    if data_subset.empty:
        raise ValueError("No valid data remaining after dropping NaNs for correlation calculation.")
    
    # Compute Pearson correlation matrix
    corr_matrix = data_subset.corr(method='pearson')
    
    logger.info(f"Correlation matrix shape: {corr_matrix.shape}")
    return corr_matrix.values, available_cols

def compute_variance_inflation_factors(df: pd.DataFrame, target_electrodes: List[str]) -> Dict[str, float]:
    """
    Computes Variance Inflation Factors (VIF) for the target electrodes to assess collinearity.
    VIF > 5 or 10 indicates high collinearity.
    """
    logger = get_logger()
    logger.info("Computing Variance Inflation Factors (VIF)")
    
    available_cols = [col for col in target_electrodes if col in df.columns]
    if not available_cols:
        return {}
        
    data_subset = df[available_cols].dropna()
    if data_subset.empty:
        return {}
    
    vif_results = {}
    # Simple VIF calculation: VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing X_i on all other X's
    # Using numpy for linear algebra
    X = data_subset.values
    n_features = X.shape[1]
    
    for i in range(n_features):
        y = X[:, i]
        X_other = np.delete(X, i, axis=1)
        
        # Add intercept
        X_other = np.column_stack((np.ones(X_other.shape[0]), X_other))
        
        try:
            # OLS: (X'X)^-1 X'y
            coeffs = np.linalg.lstsq(X_other, y, rcond=None)[0]
            y_pred = X_other @ coeffs
            
            # R-squared
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                r_squared = 0
            else:
                r_squared = 1 - (ss_res / ss_tot)
            
            if r_squared >= 1.0:
                vif = float('inf')
            else:
                vif = 1.0 / (1.0 - r_squared)
            
            vif_results[available_cols[i]] = vif
        except np.linalg.LinAlgError:
            vif_results[available_cols[i]] = float('inf')
    
    return vif_results

def compute_feature_stats(df: pd.DataFrame, target_electrodes: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Computes basic statistics (mean, std, min, max) for each target feature.
    """
    logger = get_logger()
    stats = {}
    available_cols = [col for col in target_electrodes if col in df.columns]
    
    for col in available_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            stats[col] = {
                "mean": float(col_data.mean()),
                "std": float(col_data.std()),
                "min": float(col_data.min()),
                "max": float(col_data.max()),
                "count": int(len(col_data))
            }
    return stats

def run_correlation_analysis(
    input_path: str, 
    output_path: str, 
    target_electrodes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main analysis function for T024a.
    1. Loads features.
    2. Computes Pearson correlation matrix.
    3. Computes VIFs.
    4. Saves results to feature_metadata.json.
    """
    logger = get_logger()
    logger.info("Starting Correlation Analysis (T024a)")
    
    if target_electrodes is None:
        # Standard target electrodes from FR-006 / T023 schema
        target_electrodes = ['P3_alpha', 'Pz_alpha', 'P4_alpha', 'F3_beta', 'Fz_beta', 'F4_beta']
    
    # Load Data
    df = load_feature_matrix(input_path)
    
    # Compute Correlation
    try:
        corr_vals, corr_cols = compute_correlation_matrix(df, target_electrodes)
        # Convert to list of lists for JSON serialization
        corr_matrix_list = corr_vals.tolist()
        
        # Create a labeled matrix structure for the JSON
        correlation_matrix = {
            "columns": corr_cols,
            "data": corr_matrix_list
        }
    except ValueError as e:
        logger.error(f"Failed to compute correlation matrix: {e}")
        correlation_matrix = None
    
    # Compute VIFs
    try:
        vif_scores = compute_variance_inflation_factors(df, target_electrodes)
    except Exception as e:
        logger.error(f"Failed to compute VIFs: {e}")
        vif_scores = {}
    
    # Compute Stats
    feature_stats = compute_feature_stats(df, target_electrodes)
    
    # Interpretation
    interpretation = "Collinearity assessment based on Pearson correlations and VIF."
    if correlation_matrix:
        # Simple heuristic for interpretation
        max_corr = 0
        for row in corr_vals:
            for val in row:
                if abs(val) > max_corr:
                    max_corr = abs(val)
        
        if max_corr > 0.9:
            interpretation += " High correlations detected (>0.9), suggesting potential multicollinearity."
        elif max_corr > 0.7:
            interpretation += " Moderate to high correlations detected (>0.7). Monitor for multicollinearity."
        else:
            interpretation += " Correlations are within acceptable ranges (<0.7)."
    
    if vif_scores:
        max_vif = max(vif_scores.values()) if vif_scores else 0
        if max_vif > 10:
            interpretation += f" Critical VIF detected ({max_vif:.2f}). Severe multicollinearity likely."
        elif max_vif > 5:
            interpretation += f" Elevated VIF detected ({max_vif:.2f}). Moderate multicollinearity possible."
    
    collinearity_score = max_vif if vif_scores else 0.0

    # Prepare Output
    output_data = {
        "correlation_matrix": correlation_matrix,
        "collinearity_report": {
            "collinearity_score": float(collinearity_score),
            "interpretation": interpretation,
            "vif_scores": vif_scores
        },
        "feature_statistics": feature_stats,
        "analysis_timestamp": "T024a_execution"
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Correlation analysis complete. Saved to {output_path}")
    return output_data

def main():
    """
    Entry point for running the correlation analysis.
    """
    config = get_config()
    # Default paths relative to project root
    base_path = Path(config.get('DATA_PATH', 'data'))
    processed_path = base_path / 'processed'
    
    input_file = processed_path / 'features_matrix.csv'
    output_file = processed_path / 'feature_metadata.json'
    
    if not input_file.exists():
        logging.error(f"Input file {input_file} not found. Run T023 first.")
        return 1
    
    try:
        run_correlation_analysis(str(input_file), str(output_file))
        return 0
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
