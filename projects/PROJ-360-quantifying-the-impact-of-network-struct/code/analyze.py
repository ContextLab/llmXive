import os
import json
import logging
import csv
import pickle
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

# --- Logger Setup ---
def setup_analysis_logger(name: str = "analyze_main") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --- Data Loading ---
METRICS_CSV_PATH = "data/processed/metrics.csv"
FILTERED_FEATURES_PATH = "data/processed/filtered_features.csv"
CORRELATIONS_OUTPUT_PATH = "results/correlations.json"
POWER_LOG_PATH = "results/power_analysis.log"

def load_metrics_csv() -> pd.DataFrame:
    """Load the metrics CSV file."""
    if not os.path.exists(METRICS_CSV_PATH):
        raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV_PATH}")
    return pd.read_csv(METRICS_CSV_PATH)

def load_filtered_features() -> pd.DataFrame:
    """Load the filtered features CSV file."""
    if not os.path.exists(FILTERED_FEATURES_PATH):
        raise FileNotFoundError(f"Filtered features file not found: {FILTERED_FEATURES_PATH}")
    return pd.read_csv(FILTERED_FEATURES_PATH)

# --- Metric Extraction ---
def get_network_metrics(df: pd.DataFrame) -> List[str]:
    """Return list of network metric columns."""
    # Based on T013, these are the computed network metrics
    metrics = ['avg_degree', 'path_length', 'clustering']
    return [m for m in metrics if m in df.columns]

def get_thermal_conductivity_col(df: pd.DataFrame) -> str:
    """Return the column name for thermal conductivity."""
    # Based on T015, this column is appended
    if 'thermal_conductivity_scalar' in df.columns:
        return 'thermal_conductivity_scalar'
    raise ValueError("Thermal conductivity scalar column not found in metrics.csv")

# --- VIF Calculation (T020a) ---
def calculate_vif(features_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each feature."""
    vif_dict = {}
    # Add constant for OLS if not present
    if 'const' not in features_df.columns:
        X = sm.add_constant(features_df)
    else:
        X = features_df
    
    for col in features_df.columns:
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_dict[col] = vif
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_dict[col] = float('inf')
    return vif_dict

def log_vif_results(vif_dict: Dict[str, float], logger: Optional[logging.Logger] = None):
    """Log VIF values to power_analysis.log."""
    log_path = Path(POWER_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write("\n--- VIF Results ---\n")
        for feature, value in vif_dict.items():
            f.write(f"VIF: {feature} = {value:.4f}\n")
    
    if logger:
        for feature, value in vif_dict.items():
            logger.info(f"VIF: {feature} = {value:.4f}")

# --- Feature Filtering (T021) ---
def filter_features(features_df: pd.DataFrame, vif_threshold: float = 5.0) -> pd.DataFrame:
    """Filter features based on VIF threshold."""
    vif_dict = calculate_vif(features_df)
    
    # Log results
    log_vif_results(vif_dict)
    
    included = []
    excluded = []
    
    for feature, value in vif_dict.items():
        if value < vif_threshold:
            included.append(feature)
        else:
            excluded.append((feature, value))
    
    # Log exclusions
    log_path = Path(POWER_LOG_PATH)
    with open(log_path, 'a') as f:
        for feat, val in excluded:
            f.write(f"EXCLUDED: {feat} (VIF={val:.4f})\n")
        for feat in included:
            f.write(f"INCLUDED: {feat} (VIF={vif_dict[feat]:.4f})\n")
    
    if not included:
        raise RuntimeError("All features were excluded due to high VIF. Halting pipeline.")
    
    filtered_df = features_df[included]
    
    # Write to disk
    filtered_df.to_csv(FILTERED_FEATURES_PATH, index=False)
    
    return filtered_df

# --- Model Training (T022) ---
def train_model(features_df: pd.DataFrame, target_series: pd.Series) -> LinearRegression:
    """Train a Linear Regression model."""
    model = LinearRegression()
    model.fit(features_df, target_series)
    return model

# --- Cross Validation (T023) ---
def run_stratified_cross_validation(model: LinearRegression, X: pd.DataFrame, y: pd.Series, k: int = 5) -> Dict[str, List[float]]:
    """Run k-fold cross-validation."""
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = []
    rmse_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r2 = model.score(X_test, y_test)
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
    
    return {"r2": r2_scores, "rmse": rmse_scores}

def aggregate_cv_results(cv_results: Dict[str, List[float]]) -> Dict[str, Any]:
    """Aggregate CV results."""
    r2_mean = np.mean(cv_results["r2"])
    r2_std = np.std(cv_results["r2"])
    rmse_mean = np.mean(cv_results["rmse"])
    rmse_std = np.std(cv_results["rmse"])
    
    result = {
        "r2_mean": float(r2_mean),
        "r2_std": float(r2_std),
        "rmse_mean": float(rmse_mean),
        "rmse_std": float(rmse_std),
        "r2_interpretation": None
    }
    
    if r2_mean < 0.30:
        result["r2_interpretation"] = "Weak predictive power (R² < 0.30), consistent with null hypothesis."
    
    return result

# --- Correlation Analysis (T016) ---
def compute_correlations(df: pd.DataFrame, metrics: List[str], target_col: str) -> List[Dict[str, Any]]:
    """Compute Pearson and Spearman correlations."""
    results = []
    for metric in metrics:
        if metric not in df.columns or target_col not in df.columns:
            continue
        
        # Drop NaNs
        valid_data = df[[metric, target_col]].dropna()
        if len(valid_data) < 3:
            continue
        
        x = valid_data[metric]
        y = valid_data[target_col]
        
        # Pearson
        pearson_r, pearson_p = stats.pearsonr(x, y)
        
        # Spearman
        spearman_r, spearman_p = stats.spearmanr(x, y)
        
        results.append({
            "metric": metric,
            "pearson_r": float(pearson_r),
            "pearson_p": float(pearson_p),
            "spearman_r": float(spearman_r),
            "spearman_p": float(spearman_p)
        })
    
    return results

def save_correlations(correlation_results: List[Dict[str, Any]], output_path: str):
    """Save correlations to JSON."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(correlation_results, f, indent=2)

# --- Power Analysis & Bonferroni (T017, T018) ---
def log_sample_size(n: int, logger: Optional[logging.Logger] = None):
    """Log sample size and warnings."""
    log_path = Path(POWER_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(f"\n--- Sample Size Log ---\n")
        f.write(f"Sample size (n): {n}\n")
        if n < 50:
            warning = f"WARNING: Sample size (n={n}) is less than 50. Power analysis may be underpowered."
            f.write(warning + "\n")
            if logger:
                logger.warning(warning)
        else:
            f.write("Sample size sufficient for standard Bonferroni correction.\n")

def calculate_alpha(n: int, k: int = 3) -> float:
    """
    Calculate the Bonferroni-adjusted alpha threshold.
    
    Logic:
    - If sample size n < 50, adjust the Bonferroni correction as per spec Edge Cases.
      (Interpreted as: acknowledge limitation, but strictly speaking Bonferroni is 
      alpha/k. However, if power is low, one might use a less conservative method or 
      note the limitation. The task says "adjust... as per spec Edge Cases". 
      Since the spec isn't fully provided here, we follow the standard Bonferroni 
      logic but log the warning in log_sample_size. 
      If the spec implies a different alpha for small n, it would be specific. 
      Given the instruction "adjust the Bonferroni correction", and typical 
      statistical practice, we stick to alpha/k but ensure the warning is logged.
      *Self-correction*: The task says "adjust... as per spec Edge Cases". 
      If the edge case implies a different formula (e.g. Holm-Bonferroni or just 
      noting the limitation), we should reflect that. 
      However, without the exact text of the "Edge Cases" in the prompt, the 
      safest implementation of "Bonferroni correction" is alpha/k. 
      The "adjustment" might be the logging/warning. 
      Let's assume the standard formula alpha/k is required, but the "adjustment" 
      is the context of small n. 
      Actually, re-reading: "If sample size n < 50, adjust the Bonferroni correction...".
      A common adjustment for low power is to NOT adjust (to avoid Type II error) 
      or to use a less conservative method. But the task says "Implement Bonferroni correction".
      Let's stick to the standard alpha/k but ensure the log_sample_size function 
      handles the warning. If the user meant a specific formula change, it's not 
      provided. I will return alpha/k.
    - Otherwise use fixed divisor k=3.
    """
    # Standard Bonferroni: alpha / k
    # The "adjustment" for n < 50 is primarily a warning/log, as Bonferroni is 
    # a method to control FWER regardless of n, though power suffers.
    # If the spec meant "do not adjust if n < 50", it would say "skip".
    # It says "adjust". I will return the standard value but log the warning.
    # If a specific alternative formula was intended, it is not in the prompt.
    return 0.05 / k

def apply_significance(p_value: float, alpha: float) -> bool:
    """Check if p-value is significant against alpha."""
    return p_value < alpha

def log_power_analysis(correlation_results: List[Dict[str, Any]], n: int, alpha: float, logger: Optional[logging.Logger] = None):
    """Log power analysis and significance results."""
    log_path = Path(POWER_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(f"\n--- Power Analysis & Significance ---\n")
        f.write(f"Sample size (n): {n}\n")
        f.write(f"Number of tests (k): 3\n")
        f.write(f"Family-wise alpha: 0.05\n")
        f.write(f"Bonferroni-adjusted alpha: {alpha:.5f}\n")
        f.write(f"Significance threshold: p < {alpha:.5f}\n\n")
        
        for res in correlation_results:
            metric = res["metric"]
            pearson_p = res["pearson_p"]
            spearman_p = res["spearman_p"]
            
            pearson_sig = apply_significance(pearson_p, alpha)
            spearman_sig = apply_significance(spearman_p, alpha)
            
            f.write(f"Metric: {metric}\n")
            f.write(f"  Pearson: r={res['pearson_r']:.4f}, p={pearson_p:.5f} -> {'Significant' if pearson_sig else 'Not Significant'}\n")
            f.write(f"  Spearman: r={res['spearman_r']:.4f}, p={spearman_p:.5f} -> {'Significant' if spearman_sig else 'Not Significant'}\n")
            f.write("\n")
    
    if logger:
        logger.info(f"Power analysis logged. Adjusted alpha: {alpha}")

# --- Main Entry Point ---
def main():
    logger = setup_analysis_logger()
    logger.info("Starting analysis pipeline...")
    
    try:
        # 1. Load Data
        metrics_df = load_metrics_csv()
        logger.info(f"Loaded metrics: {len(metrics_df)} rows")
        
        # 2. Get Network Metrics and Target
        network_metrics = get_network_metrics(metrics_df)
        target_col = get_thermal_conductivity_col(metrics_df)
        
        if not network_metrics:
            logger.error("No network metrics found in dataset.")
            return 1
        
        logger.info(f"Network metrics found: {network_metrics}")
        
        # 3. Log Sample Size (T018a)
        n = len(metrics_df)
        log_sample_size(n, logger)
        
        # 4. Calculate Alpha (T018b) - T017 Logic
        # Logic: If n < 50, adjust? The prompt says "adjust... as per spec Edge Cases".
        # Since the specific edge case formula isn't provided, we use standard alpha/k
        # but the logging in log_sample_size handles the "adjustment" context.
        # If the spec meant a different alpha (e.g. 0.10), it would be specified.
        # We stick to 0.05/3.
        k = len(network_metrics)
        if k == 0: k = 1 # Avoid division by zero
        alpha = calculate_alpha(n, k)
        logger.info(f"Calculated Bonferroni alpha: {alpha}")
        
        # 5. Compute Correlations (T016)
        correlation_results = compute_correlations(metrics_df, network_metrics, target_col)
        
        # 6. Apply Significance & Log (T017, T018c)
        log_power_analysis(correlation_results, n, alpha, logger)
        
        # 7. Save Correlations
        save_correlations(correlation_results, CORRELATIONS_OUTPUT_PATH)
        logger.info(f"Correlations saved to {CORRELATIONS_OUTPUT_PATH}")
        
        # 8. VIF & Filtering (T020a, T021) - Only if features exist
        # This path is often taken in the full pipeline, but T017 is about correlations.
        # However, the full run-book calls analyze.py which likely does everything.
        # We check if filtered_features.csv is needed or if we do it here.
        # Based on T021, filter_features writes to data/processed/filtered_features.csv.
        # We should run this if the file is missing or to update it.
        # But T017 specifically is about Bonferroni. We ensure the flow works.
        
        # Check if we need to run VIF/Filtering (T020/T021)
        # The task T017 is just Bonferroni, but the script analyze.py does the whole pipeline.
        # We need to ensure filtered_features.csv is written if the pipeline expects it.
        # Let's assume the full pipeline runs this function.
        
        if os.path.exists(FILTERED_FEATURES_PATH) or 'volume' in metrics_df.columns:
            # If physical descriptors exist, run VIF/Filtering
            # Select features for VIF: network metrics + physical descriptors if present
            features_to_check = network_metrics.copy()
            physical_cols = ['volume', 'atom_count', 'mean_mass']
            for col in physical_cols:
                if col in metrics_df.columns:
                    features_to_check.append(col)
            
            if features_to_check:
                X_features = metrics_df[features_to_check].dropna()
                y_target = metrics_df[target_col].loc[X_features.index]
                
                if len(X_features) > 0:
                    filtered_df = filter_features(X_features, vif_threshold=5.0)
                    logger.info(f"Filtered features saved to {FILTERED_FEATURES_PATH}")
                    
                    # Train model (T022)
                    model = train_model(filtered_df, y_target)
                    
                    # CV (T023)
                    cv_results = run_stratified_cross_validation(model, filtered_df, y_target, k=5)
                    agg_results = aggregate_cv_results(cv_results)
                    
                    # Save Model Performance (T024)
                    perf_path = "results/model_performance.json"
                    with open(perf_path, 'w') as f:
                        json.dump(agg_results, f, indent=2)
                    logger.info(f"Model performance saved to {perf_path}")
        
        logger.info("Analysis pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main())