import os
import json
import logging
import csv
import pickle
import random
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import Config, get_config
from utils import setup_logging, pin_seed

logger = logging.getLogger("analyze")

def load_metrics_csv(csv_path: str) -> pd.DataFrame:
    """Load metrics from CSV into a DataFrame."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metrics CSV not found at {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for specified features.
    """
    X = df[feature_cols].dropna()
    if len(X) < len(feature_cols) + 1:
        logger.warning("Insufficient data points for VIF calculation.")
        return {col: float('inf') for col in feature_cols}

    vif_data = {}
    for i, col in enumerate(feature_cols):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = float(vif)
        except Exception as e:
            logger.error(f"VIF calculation failed for {col}: {e}")
            vif_data[col] = float('inf')
    return vif_data

def log_vif_results(vif_dict: Dict[str, float], log_path: str = "results/power_analysis.log"):
    """Log VIF results to a file."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        f.write("Variance Inflation Factor (VIF) Analysis\n")
        f.write("-" * 40 + "\n")
        for col, val in vif_dict.items():
            f.write(f"{col}: {val:.4f}\n")
        f.write("-" * 40 + "\n")
    logger.info(f"VIF results logged to {log_path}")

def verify_vif_scope(vif_dict: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """Return list of features with VIF below threshold."""
    return [col for col, val in vif_dict.items() if val < threshold]

def filter_features(df: pd.DataFrame, keep_cols: List[str], target_col: str) -> pd.DataFrame:
    """Filter dataframe to keep only specified features and target."""
    cols_to_keep = [c for c in keep_cols if c in df.columns]
    if target_col in df.columns:
        cols_to_keep.append(target_col)
    return df[cols_to_keep].dropna()

def compute_correlations(df: pd.DataFrame, metric_cols: List[str], target_col: str) -> Dict[str, Any]:
    """Compute Pearson and Spearman correlations with Bonferroni correction."""
    results = []
    n_tests = len(metric_cols)
    alpha = 0.05
    corrected_alpha = alpha / n_tests

    for col in metric_cols:
        if col not in df.columns or target_col not in df.columns:
            continue
        
        x = df[col].dropna()
        y = df[target_col].dropna()
        
        # Align indices for correlation
        common_idx = x.index.intersection(y.index)
        x = x.loc[common_idx]
        y = y.loc[common_idx]

        if len(x) < 3:
            continue

        pearson_r, pearson_p = stats.pearsonr(x, y)
        spearman_r, spearman_p = stats.spearmanr(x, y)

        results.append({
            "feature": col,
            "pearson_r": float(pearson_r),
            "pearson_p": float(pearson_p),
            "spearman_r": float(spearman_r),
            "spearman_p": float(spearman_p),
            "bonferroni_corrected": float(pearson_p * n_tests) if pearson_p is not None else None,
            "significant_at_0.05": (pearson_p * n_tests) < 0.05 if pearson_p is not None else False
        })

    return {
        "correlations": results,
        "bonferroni_alpha": corrected_alpha,
        "sample_size": len(df)
    }

def calculate_bonferroni_pvalues(correlation_results: List[Dict], alpha: float = 0.05) -> List[Dict]:
    """Apply Bonferroni correction to p-values."""
    n = len(correlation_results)
    corrected_alpha = alpha / n
    for res in correlation_results:
        res['bonferroni_corrected_p'] = res['pearson_p'] * n
        res['significant'] = res['bonferroni_corrected_p'] < alpha
    return correlation_results

def save_correlations(correlation_data: Dict[str, Any], output_path: str):
    """Save correlation results to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(correlation_data, f, indent=2)
    logger.info(f"Saved correlations to {output_path}")

def update_state_artifact_hash(state_path: str, artifact_path: str):
    """Update state YAML with artifact checksum."""
    if not os.path.exists(state_path):
        return
    try:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
        
        checksum = hashlib.sha256(open(artifact_path, 'rb').read()).hexdigest()
        if 'artifacts' not in state:
            state['artifacts'] = {}
        state['artifacts'][os.path.basename(artifact_path)] = {
            "path": artifact_path,
            "checksum": checksum
        }
        with open(state_path, 'w') as f:
            yaml.dump(state, f)
    except Exception as e:
        logger.error(f"Failed to update state: {e}")

def main():
    """Main entry point for correlation analysis."""
    config = get_config()
    pin_seed(config.get('RANDOM_SEED', 42))

    metrics_path = "data/processed/metrics.csv"
    correlations_path = "results/correlations.json"
    filtered_features_path = "data/processed/filtered_features.csv"
    state_path = "state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml"

    # Load Data
    df = load_metrics_csv(metrics_path)
    
    # Define Feature Columns
    network_metrics = ["average_degree", "average_path_length", "clustering_coefficient"]
    physical_descriptors = ["unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
    all_features = network_metrics + physical_descriptors
    target_col = "thermal_conductivity_scalar"

    # VIF Analysis
    vif_dict = calculate_vif(df, all_features)
    log_vif_results(vif_dict)
    logger.info(f"VIF Results: {vif_dict}")

    # Filter Features (VIF < 5)
    safe_features = verify_vif_scope(vif_dict, threshold=5.0)
    logger.info(f"Safe features after VIF filtering: {safe_features}")

    # Create Filtered Dataset
    filtered_df = filter_features(df, safe_features, target_col)
    filtered_df.to_csv(filtered_features_path, index=False)
    logger.info(f"Saved filtered features to {filtered_features_path}")

    # Compute Correlations
    corr_data = compute_correlations(filtered_df, safe_features, target_col)
    calculate_bonferroni_pvalues(corr_data['correlations'])
    save_correlations(corr_data, correlations_path)

    # Update State
    update_state_artifact_hash(state_path, correlations_path)
    update_state_artifact_hash(state_path, filtered_features_path)

    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()
