import os
import json
import logging
import csv
import pickle
import random
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config, initialize_environment

def setup_analysis_logger():
    logger = logging.getLogger("analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_metrics_csv() -> pd.DataFrame:
    """Load metrics from data/processed/metrics.csv or transformed version if available."""
    path = Path("data/processed/metrics.csv")
    transformed_path = Path("data/processed/metrics_transformed.csv")
    
    if transformed_path.exists():
        logging.getLogger("analysis").info("Using transformed metrics file.")
        return pd.read_csv(transformed_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    
    return pd.read_csv(path)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """Calculate Variance Inflation Factor for each feature."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Add constant for intercept
    X = df[features].copy()
    X = X.dropna() # VIF requires no NaNs
    if len(X) < len(features) + 1:
        raise ValueError("Not enough data points to calculate VIF.")
    
    vif_data = []
    for i, col in enumerate(features):
        if col in X.columns:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({"feature": col, "vif": vif})
    
    return pd.Series([d["vif"] for d in vif_data], index=[d["feature"] for d in vif_data])

def log_vif_results(vif_series: pd.Series, logger: logging.Logger):
    """Log VIF values."""
    logger.info("VIF Results:")
    for feature, vif in vif_series.items():
        logger.info(f"  {feature}: {vif:.2f}")

def verify_vif_scope(df: pd.DataFrame, logger: logging.Logger):
    """Verify that physical descriptors are included in the feature set for VIF calculation."""
    required_physical = ["unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
    missing = [col for col in required_physical if col not in df.columns]
    if missing:
        logger.warning(f"Missing physical descriptors for VIF scope: {missing}")
    else:
        logger.info("Physical descriptors present for VIF scope verification.")

def filter_features(df: pd.DataFrame, vif_threshold: float = 5.0, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """Filter features based on VIF threshold and save to filtered_features.csv."""
    if logger is None:
        logger = setup_analysis_logger()
    
    feature_cols = [
        "average_degree", "average_path_length", "clustering_coefficient",
        "unit_cell_volume", "total_atom_count", "mean_atomic_mass"
    ]
    
    # Ensure columns exist
    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        raise ValueError("No feature columns found for VIF calculation.")
    
    # Calculate VIF
    vif_series = calculate_vif(df, available_features)
    log_vif_results(vif_series, logger)
    
    # Filter
    low_vif_features = vif_series[vif_series < vif_threshold].index.tolist()
    
    # Keep target and material_id
    cols_to_keep = ["material_id", "thermal_conductivity_scalar"] + low_vif_features
    cols_to_keep = [c for c in cols_to_keep if c in df.columns]
    
    filtered_df = df[cols_to_keep].dropna()
    
    output_path = Path("data/processed/filtered_features.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    
    logger.info(f"Filtered features saved to {output_path} with columns: {list(filtered_df.columns)}")
    return filtered_df

def compute_correlations(df: pd.DataFrame, logger: logging.Logger):
    """Compute Pearson and Spearman correlations."""
    network_metrics = ["average_degree", "average_path_length", "clustering_coefficient"]
    target = "thermal_conductivity_scalar"
    
    results = []
    
    for metric in network_metrics:
        if metric not in df.columns or target not in df.columns:
            continue
        
        # Drop NaNs
        valid_data = df[[metric, target]].dropna()
        if len(valid_data) < 3:
            continue
        
        x = valid_data[metric]
        y = valid_data[target]
        
        pearson_corr, pearson_p = stats.pearsonr(x, y)
        spearman_corr, spearman_p = stats.spearmanr(x, y)
        
        results.append({
            "metric": metric,
            "pearson_r": pearson_corr,
            "pearson_p": pearson_p,
            "spearman_rho": spearman_corr,
            "spearman_p": spearman_p
        })
    
    return results

def calculate_bonferroni_pvalues(results: List[Dict], nominal_alpha: float = 0.05) -> List[Dict]:
    """Apply Bonferroni correction to p-values."""
    n_tests = len(results) * 2 # Pearson and Spearman for each metric
    if n_tests == 0:
        return results
    
    adjusted_alpha = nominal_alpha / n_tests
    
    for res in results:
        res["bonferroni_pearson_p"] = min(res["pearson_p"] * n_tests, 1.0)
        res["bonferroni_spearman_p"] = min(res["spearman_p"] * n_tests, 1.0)
        res["bonferroni_alpha"] = adjusted_alpha
    
    return results

def save_correlations(results: List[Dict], logger: logging.Logger):
    """Save correlation results to results/correlations.json."""
    output_path = Path("results/correlations.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved correlations to {output_path}")

def update_state_artifact_hash():
    """Update state file with artifact hash (placeholder for now)."""
    pass

def log_sample_size_warning(df: pd.DataFrame, logger: logging.Logger):
    """Log warning if sample size < 50."""
    n = len(df)
    if n < 50:
        logger.warning(f"Sample size is small: {n} (< 50). Results may not be robust.")
    else:
        logger.info(f"Sample size: {n} (>= 50).")

def log_final_count(df: pd.DataFrame, logger: logging.Logger):
    """Log final count of materials."""
    logger.info(f"Final material count: {len(df)}")

def perform_normality_test(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Perform Shapiro-Wilk test and apply log-transform if non-normal."""
    target_col = "thermal_conductivity_scalar"
    metric_cols = ["average_degree", "average_path_length", "clustering_coefficient"]
    
    if target_col not in df.columns:
        logger.warning(f"Target column {target_col} not found. Skipping normality test.")
        return df
    
    # Check normality
    non_normal_cols = []
    
    # Test target
    valid_target = df[target_col].dropna()
    if len(valid_target) >= 3:
        stat, p = stats.shapiro(valid_target)
        if p < 0.05:
            non_normal_cols.append(target_col)
            logger.info(f"Target {target_col} is non-normal (p={p:.4f}). Applying log-transform.")
    
    # Test metrics
    for col in metric_cols:
        if col in df.columns:
            valid_col = df[col].dropna()
            if len(valid_col) >= 3:
                stat, p = stats.shapiro(valid_col)
                if p < 0.05:
                    non_normal_cols.append(col)
                    logger.info(f"Metric {col} is non-normal (p={p:.4f}). Applying log-transform.")
    
    if non_normal_cols:
        df_transformed = df.copy()
        for col in non_normal_cols:
            # Avoid log(0) or log(negative) by adding small epsilon if needed
            if df_transformed[col].min() <= 0:
                epsilon = 1e-6
                df_transformed[col] = np.log(df_transformed[col] + epsilon)
            else:
                df_transformed[col] = np.log(df_transformed[col])
        
        output_path = Path("data/processed/metrics_transformed.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_transformed.to_csv(output_path, index=False)
        logger.info(f"Saved transformed metrics to {output_path}")
        return df_transformed
    
    logger.info("All tested columns appear normal. No transformation needed.")
    return df

def main():
    logger = setup_analysis_logger()
    initialize_environment()
    
    try:
        # 1. Load Metrics
        df = load_metrics_csv()
        log_final_count(df, logger)
        log_sample_size_warning(df, logger)
        
        # 2. Perform Normality Test (T031)
        df = perform_normality_test(df, logger)
        
        # 3. Calculate VIF and Filter Features (T020a, T020b)
        verify_vif_scope(df, logger)
        filter_features(df, logger=logger)
        
        # 4. Compute Correlations (T016a)
        corr_results = compute_correlations(df, logger)
        
        # 5. Bonferroni Correction (T017)
        corr_results = calculate_bonferroni_pvalues(corr_results)
        
        # 6. Save Correlations (T016b)
        save_correlations(corr_results, logger)
        
        logger.info("Analysis pipeline completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
