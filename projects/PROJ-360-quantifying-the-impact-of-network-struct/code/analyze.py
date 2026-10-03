import os
import json
import logging
import csv
import pickle
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd
import numpy as np

from config import Config, initialize_environment
from utils import setup_logging

# --- Logger Setup ---
def setup_analysis_logger(name: str = "analysis_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

analysis_logger = setup_analysis_logger()

# --- Data Loading ---
def load_metrics_csv(filepath: str) -> pd.DataFrame:
    """Load the metrics CSV file into a pandas DataFrame."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    df = pd.read_csv(filepath)
    analysis_logger.info(f"Loaded metrics CSV with {len(df)} rows and {len(df.columns)} columns.")
    return df

# --- VIF Calculation ---
def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    Returns a DataFrame with feature names and their VIF values.
    """
    if len(features) == 0:
        return pd.DataFrame(columns=["feature", "vif"])

    # Drop rows with NaN in any of the features
    vif_data = df[features].dropna()
    if len(vif_data) == 0:
        raise ValueError("No valid data rows remaining after dropping NaNs for VIF calculation.")

    X = vif_data[features]
    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    vif_results = []
    for i, feature in enumerate(features):
        # VIF for feature i is 1 / (1 - R^2_i) where R^2_i is from regressing feature i on all other features
        # statsmodels vif function handles this
        try:
            vif_val = variance_inflation_factor(X_with_const.values, i)
            vif_results.append({"feature": feature, "vif": vif_val})
        except Exception as e:
            analysis_logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_results.append({"feature": feature, "vif": np.nan})

    return pd.DataFrame(vif_results)

import statsmodels.api as sm

def log_vif_results(vif_df: pd.DataFrame, threshold: float = 5.0) -> List[str]:
    """Log VIF results and return list of features to keep (VIF < threshold)."""
    analysis_logger.info("--- VIF Analysis Results ---")
    kept_features = []
    for _, row in vif_df.iterrows():
        feature = row['feature']
        vif_val = row['vif']
        status = "KEEP" if vif_val < threshold else "DROP"
        analysis_logger.info(f"Feature: {feature}, VIF: {vif_val:.4f} -> {status}")
        if vif_val < threshold:
            kept_features.append(feature)
    
    analysis_logger.info(f"Features to keep (VIF < {threshold}): {kept_features}")
    return kept_features

def verify_vif_scope(features_to_check: List[str], available_features: List[str]) -> bool:
    """Verify that all requested features are present in the available set."""
    missing = set(features_to_check) - set(available_features)
    if missing:
        analysis_logger.warning(f"Missing features for VIF check: {missing}")
        return False
    return True

def filter_features(df: pd.DataFrame, keep_features: List[str], target_col: str) -> pd.DataFrame:
    """Filter the dataframe to keep only specified features and the target column."""
    cols_to_keep = keep_features + [target_col]
    # Ensure all columns exist
      # Ensure all columns exist
    missing_cols = [c for c in cols_to_keep if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found in dataframe: {missing_cols}")
    
    filtered_df = df[cols_to_keep].dropna()
    analysis_logger.info(f"Filtered features dataframe shape: {filtered_df.shape}")
    return filtered_df

# --- Correlation Analysis (for completeness, though T020c focuses on VIF) ---
def compute_correlations(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Dict[str, Any]:
    """Compute Pearson and Spearman correlations."""
    results = {}
    for feat in feature_cols:
        if feat in df.columns and target_col in df.columns:
            clean_data = df[[feat, target_col]].dropna()
            if len(clean_data) > 1:
                pearson = clean_data[feat].corr(clean_data[target_col], method='pearson')
                spearman = clean_data[feat].corr(clean_data[target_col], method='spearman')
                results[feat] = {
                    "pearson": pearson,
                    "spearman": spearman
                }
    return results

def calculate_bonferroni_pvalues(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    m = len(p_values)
    if m == 0:
        return []
    corrected = [min(p * m, 1.0) for p in p_values]
    return corrected

def save_correlations(correlations: Dict[str, Any], output_path: str):
    """Save correlation results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(correlations, f, indent=2)
    analysis_logger.info(f"Saved correlations to {output_path}")

def update_state_artifact_hash(state_path: str, artifact_path: str):
    """Update a state artifact with the hash of a specific file."""
    import hashlib
    if not os.path.exists(artifact_path):
        analysis_logger.warning(f"Cannot update state, artifact not found: {artifact_path}")
        return

    with open(artifact_path, 'rb') as f:
        content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()

    state = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = json.load(f)

    state['last_artifact_hash'] = file_hash
    state['last_updated'] = str(pd.Timestamp.now())

    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    analysis_logger.info(f"Updated state artifact hash for {artifact_path}")

def log_sample_size_warning(df: pd.DataFrame, min_size: int = 50):
    """Log a warning if the sample size is below the threshold."""
    n = len(df)
    if n < min_size:
        analysis_logger.warning(f"Sample size ({n}) is below the recommended threshold ({min_size}).")
    else:
        analysis_logger.info(f"Sample size ({n}) is sufficient (>= {min_size}).")

def main():
    """
    Main execution for VIF analysis and feature filtering (Task T020c).
    1. Load metrics.csv
    2. Calculate VIF for network metrics and physical descriptors
    3. Log VIF values
    4. Filter features based on VIF threshold
    5. Save filtered_features.csv
    6. Update checksums
    """
    initialize_environment()
    config = Config()
    
    # Paths
    metrics_path = "data/processed/metrics.csv"
    filtered_output_path = "data/processed/filtered_features.csv"
    checksums_path = "data/processed/checksums.json"
    
    # Define candidate features (Network Metrics + Physical Descriptors)
    # Based on T013 and T014a outputs
    candidate_features = [
        "average_degree",
        "average_path_length", 
        "clustering_coefficient",
        "unit_cell_volume",
        "total_atom_count",
        "mean_atomic_mass"
    ]
    target_feature = "thermal_conductivity_scalar"

    # 1. Load Data
    try:
        df = load_metrics_csv(metrics_path)
    except FileNotFoundError as e:
        analysis_logger.error(str(e))
        return

    # 2. Verify Scope
    if not verify_vif_scope(candidate_features, list(df.columns)):
        analysis_logger.error("Missing features for VIF calculation. Cannot proceed.")
        return

    # 3. Calculate VIF
    vif_df = calculate_vif(df, candidate_features)
    
    # 4. Log VIF Results and Determine Features to Keep
    kept_features = log_vif_results(vif_df, threshold=5.0)
    
    # 5. Filter Features
    if not kept_features:
        analysis_logger.error("No features passed the VIF threshold. Cannot create filtered dataset.")
        return
        
    filtered_df = filter_features(df, kept_features, target_feature)
    
    # 6. Save Filtered Features
    filtered_df.to_csv(filtered_output_path, index=False)
    analysis_logger.info(f"Saved filtered features to {filtered_output_path}")
    
    # 7. Update Checksums
    # We need to compute the hash for the new file and update the checksums.json
    import hashlib
    import json
    
    if os.path.exists(checksums_path):
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    else:
        checksums = {"source_cifs": {}, "derived_graphs": {}, "derivation": ""}
    
    with open(filtered_output_path, 'rb') as f:
        content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
    
    checksums["filtered_features"] = file_hash
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    analysis_logger.info(f"Updated checksums.json with hash for filtered_features.csv: {file_hash}")

if __name__ == "__main__":
    main()