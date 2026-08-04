import os
import json
import logging
import csv
import pickle
import random
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from scipy.stats import pearsonr, spearmanr

# Ensure statsmodels is available
try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError:
    # Fallback if not installed, though requirements.txt should have it
    variance_inflation_factor = None

logger = logging.getLogger("analyze")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def setup_analysis_logger():
    """Configure logging for analysis tasks."""
    return logger

def update_state_artifact_hash(file_path: str) -> None:
    """
    Computes SHA-256 checksum of the output file and updates the project state YAML.
    """
    import hashlib
    import yaml
    
    state_file_path = Path("state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml")
    
    if not file_path or not os.path.exists(file_path):
        logger.error(f"Cannot compute hash for non-existent file: {file_path}")
        return

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    
    logger.info(f"Computed checksum for {file_path}: {checksum}")

    state_data = {}
    if state_file_path.exists():
        with open(state_file_path, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Error reading state file: {e}")
                return
    
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    state_data["artifact_hashes"][str(file_path)] = checksum
    
    temp_path = state_file_path.with_suffix('.tmp')
    try:
        with open(temp_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        os.replace(temp_path, state_file_path)
        logger.info(f"State file updated at {state_file_path}")
    except Exception as e:
        logger.error(f"Failed to update state file: {e}")
        if temp_path.exists():
            temp_path.unlink()

def load_metrics_csv(path: str = "data/processed/metrics.csv") -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found: {path}")
    return pd.read_csv(path)

def calculate_vif(features_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for network metrics ONLY.
    Excludes physical descriptors (volume, atom count, mass).
    """
    if variance_inflation_factor is None:
        raise ImportError("statsmodels is required for VIF calculation.")
    
    # Filter columns to only network metrics as per spec
    network_metrics = ['avg_degree', 'path_length', 'clustering']
    available_metrics = [col for col in network_metrics if col in features_df.columns]
    
    if not available_metrics:
        logger.warning("No network metrics found for VIF calculation.")
        return {}
    
    X = features_df[available_metrics].dropna()
    
    if X.empty:
        logger.warning("No valid rows for VIF calculation after dropping NaNs.")
        return {col: float('inf') for col in available_metrics}
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    vif_dict = {}
    for i, col in enumerate(available_metrics):
        try:
            # VIF for a feature is 1 / (1 - R^2) where R^2 is from regressing that feature on others
            # statsmodels VIF function handles this
            vif_val = variance_inflation_factor(X_const.values, i+1) # +1 because of constant
            vif_dict[col] = float(vif_val)
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_dict[col] = float('inf')
    
    return vif_dict

def log_vif_results(vif_dict: Dict[str, float], log_path: str = "results/power_analysis.log") -> None:
    """Logs VIF values to the power analysis log."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"\n--- VIF Calculation Results ---\n")
        for feature, value in vif_dict.items():
            f.write(f"VIF: {feature} = {value:.4f}\n")
    logger.info(f"VIF results logged to {log_path}")

def verify_vif_scope(vif_dict: Dict[str, float]) -> bool:
    """Verifies that VIF calculation was performed only on network metrics."""
    allowed = {'avg_degree', 'path_length', 'clustering'}
    actual = set(vif_dict.keys())
    if not actual.issubset(allowed):
        logger.error(f"VIF calculation included non-network metrics: {actual - allowed}")
        return False
    return True

def filter_features(features_df: pd.DataFrame, vif_threshold: float = 5.0) -> pd.DataFrame:
    """
    Filters features based on VIF threshold.
    Writes filtered features to data/processed/filtered_features.csv.
    Updates state file.
    """
    vif_dict = calculate_vif(features_df)
    log_vif_results(vif_dict)
    
    if not verify_vif_scope(vif_dict):
        logger.error("VIF scope verification failed. Aborting filter.")
        return pd.DataFrame()
    
    included_features = []
    excluded_features = []
    
    for feature, vif_val in vif_dict.items():
        if vif_val < vif_threshold:
            included_features.append(feature)
            logger.info(f"INCLUDED: {feature} (VIF={vif_val:.4f})")
        else:
            excluded_features.append(feature)
            logger.info(f"EXCLUDED: {feature} (VIF={vif_val:.4f})")
    
    if not included_features:
        logger.critical("No valid features for regression. All excluded.")
        # Generate report as per spec
        report_path = "results/no_features_report.txt"
        with open(report_path, 'w') as f:
            f.write("No valid features for regression\n")
        return pd.DataFrame()
    
    # Filter the dataframe
    # We need to include the target variable if it's in the dataframe, but VIF is only on features
    # The function signature implies we are filtering the feature columns.
    # Assuming features_df contains both features and target, we select only the included features.
    # However, for regression, we usually separate X and y.
    # Here, we return a dataframe with only the included feature columns.
    # The target 'thermal_conductivity_scalar' should be preserved if we want to train later,
    # but the spec says "filter_features" returns the filtered features.
    # Let's assume the caller will handle target separation.
    # But to be safe and useful for T022, let's include the target if it exists.
    
    target_col = 'thermal_conductivity_scalar'
    final_cols = included_features
    if target_col in features_df.columns:
        final_cols.append(target_col)
    
    filtered_df = features_df[final_cols].copy()
    
    output_path = "data/processed/filtered_features.csv"
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered features saved to {output_path}")
    
    # Update state
    update_state_artifact_hash(output_path)
    
    return filtered_df

def compute_correlations(metrics_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Computes Pearson and Spearman correlations between network metrics and thermal conductivity.
    """
    results = []
    target = 'thermal_conductivity_scalar'
    metrics = ['avg_degree', 'path_length', 'clustering']
    
    if target not in metrics_df.columns:
        logger.error(f"Target column '{target}' not found in metrics dataframe.")
        return results
    
    for metric in metrics:
        if metric not in metrics_df.columns:
            logger.warning(f"Metric '{metric}' not found, skipping.")
            continue
        
        x = metrics_df[metric].dropna()
        y = metrics_df[target].dropna()
        
        # Align indices
        common_idx = x.index.intersection(y.index)
        x = x.loc[common_idx]
        y = y.loc[common_idx]
        
        if len(x) < 2:
            logger.warning(f"Not enough data points for correlation on {metric}.")
            continue
        
        pearson_r, pearson_p = pearsonr(x, y)
        spearman_r, spearman_p = spearmanr(x, y)
        
        results.append({
            "metric_name": metric,
            "pearson_coeff": float(pearson_r),
            "pearson_p_value": float(pearson_p),
            "spearman_coeff": float(spearman_r),
            "spearman_p_value": float(spearman_p)
        })
    
    return results

def calculate_bonferroni_pvalues(results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Applies Bonferroni correction for multiple comparisons.
    Fixed alpha = 0.05 / 3 (number of tests).
    """
    n_tests = 3
    corrected_alpha = alpha / n_tests
    logger.info(f"Bonferroni correction: alpha = {alpha} / {n_tests} = {corrected_alpha}")
    
    for res in results:
        res['bonferroni_adjusted_p'] = min(res['pearson_p_value'] * n_tests, 1.0)
        res['is_significant'] = res['bonferroni_adjusted_p'] < corrected_alpha
    
    return results

def save_correlations(results: List[Dict[str, Any]], output_path: str = "results/correlations.json") -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    update_state_artifact_hash(output_path)
    logger.info(f"Correlations saved to {output_path}")

def main():
    """
    Main entry point for correlation analysis and VIF filtering (T016-T021 logic).
    This function orchestrates the flow if run directly.
    """
    # 1. Load metrics
    try:
        metrics_df = load_metrics_csv()
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    # 2. Compute correlations (T016)
    corr_results = compute_correlations(metrics_df)
    
    # 3. Bonferroni (T017)
    corr_results = calculate_bonferroni_pvalues(corr_results)
    
    # 4. Save correlations (T016)
    save_correlations(corr_results)
    
    # 5. VIF and Filter (T020-T021)
    # We need to pass the feature columns
    features_df = metrics_df[['avg_degree', 'path_length', 'clustering', 'thermal_conductivity_scalar']]
    filtered_df = filter_features(features_df)
    
    if filtered_df.empty:
        logger.warning("No features passed VIF filter. Model training skipped.")
        return 0
    
    # 6. Train Model (T022) - simplified inline for main execution if needed
    # (T022 is usually a separate step in the pipeline, but we can call it here if integrated)
    # For now, we stop at T021 as per task boundaries, assuming T022 is called separately.
    
    return 0

if __name__ == "__main__":
    exit(main())
