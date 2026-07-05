import os
import json
import logging
import csv
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
import warnings

# Suppress specific warnings for cleaner logs if necessary
warnings.filterwarnings('ignore', category=RuntimeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

def setup_analysis_logger(name: str = "analysis") -> logging.Logger:
    """Setup a logger for the analysis module."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def load_metrics_csv(path: str) -> pd.DataFrame:
    """Load the metrics CSV, handling potential header comments."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}")
    
    # Read lines to handle header comments
    lines = p.read_text().splitlines()
    clean_lines = [line for line in lines if not line.startswith('#')]
    
    # Write back to a temp or just parse if pandas supports skiprows with comment char
    # pandas read_csv handles comments directly
    df = pd.read_csv(path, comment='#')
    return df

def get_network_metrics(df: pd.DataFrame) -> List[str]:
    """Identify network metric columns in the dataframe."""
    # Based on T013, these are the standard network metrics
    possible_metrics = ['avg_degree', 'avg_shortest_path', 'clustering_coefficient']
    found = [col for col in possible_metrics if col in df.columns]
    return found

def get_thermal_conductivity_col(df: pd.DataFrame) -> str:
    """Identify the thermal conductivity column."""
    candidates = ['thermal_conductivity', 'k_avg', 'thermal_conductivity_scalar']
    for c in candidates:
        if c in df.columns:
            return c
    # Fallback: look for any column containing 'thermal' and 'conductivity'
    for c in df.columns:
        if 'thermal' in c.lower() and 'conductivity' in c.lower():
            return c
    raise ValueError("Could not identify thermal conductivity column in dataframe")

def calculate_vif(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> pd.DataFrame:
    """Calculate Variance Inflation Factor for features."""
    if len(feature_cols) == 0:
        return pd.DataFrame(columns=['feature', 'vif'])
    
    X = df[feature_cols].copy()
    # Handle constant features or NaNs
    X = X.dropna()
    if X.empty:
        return pd.DataFrame(columns=['feature', 'vif'])
    
    # Add constant for OLS
    X_with_const = sm.add_constant(X)
    vif_data = []
    
    # Note: VIF is calculated for each feature in the design matrix (excluding constant usually, but statsmodels includes it)
    # We only care about the user-provided features
    for col in feature_cols:
        if col not in X.columns:
            continue
        # Recalculate VIF for this specific column using the current dataframe subset
        # To be precise, VIF for column j is 1 / (1 - R_j^2) where R_j^2 is from regressing X_j on all other X
        try:
            # Using the formula directly or statsmodels
            # Simple implementation:
            y = X[col]
            X_other = X.drop(columns=[col])
            if X_other.empty:
                vif = 0.0 # No other features
            else:
                X_other_const = sm.add_constant(X_other)
                model = OLS(y, X_other_const).fit()
                r2 = model.rsquared
                if r2 == 1.0:
                    vif = np.inf
                else:
                    vif = 1.0 / (1.0 - r2)
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})
    
    return pd.DataFrame(vif_data)

def log_vif_results(vif_df: pd.DataFrame, log_path: str) -> None:
    """Log VIF results to a file."""
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    with open(p, 'a') as f:
        f.write(f"\n--- VIF Analysis at {pd.Timestamp.now()} ---\n")
        for _, row in vif_df.iterrows():
            f.write(f"Feature: {row['feature']}, VIF: {row['vif']:.4f}\n")

def compute_correlations(df: pd.DataFrame, metrics: List[str], target_col: str) -> Dict[str, Any]:
    """
    Compute Pearson and Spearman correlations between each network metric and thermal conductivity.
    Returns a dictionary of results.
    """
    results = {}
    
    for metric in metrics:
        if metric not in df.columns or target_col not in df.columns:
            continue
        
        x = df[metric].dropna()
        y = df[target_col].dropna()
        
        # Align indices after dropna
        common_idx = x.index.intersection(y.index)
        if len(common_idx) < 3:
            results[metric] = {
                'pearson_r': None,
                'pearson_p': None,
                'spearman_r': None,
                'spearman_p': None,
                'n': len(common_idx)
            }
            continue
        
        x = x.loc[common_idx]
        y = y.loc[common_idx]
        
        # Pearson
        p_pearson_r, p_pearson_p = stats.pearsonr(x, y)
        # Spearman
        p_spearman_r, p_spearman_p = stats.spearmanr(x, y)
        
        results[metric] = {
            'pearson_r': float(p_pearson_r),
            'pearson_p': float(p_pearson_p),
            'spearman_r': float(p_spearman_r),
            'spearman_p': float(p_spearman_p),
            'n': len(common_idx)
        }
    
    return results

def apply_bonferroni_correction(correlation_results: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to the p-values from the correlation tests.
    The family-wise error rate is controlled at alpha.
    Number of tests = number of metrics * 2 (Pearson + Spearman) OR just per metric type?
    Task T017 says: "for the 3 correlation tests". This implies 3 tests total.
    Usually, we test each metric against the target. If we do both Pearson and Spearman,
    that's 6 tests. However, the task says "3 correlation tests", likely meaning
    one test per metric (perhaps focusing on Pearson, or treating the pair as one hypothesis).
    Given the phrasing "3 correlation tests", we assume 3 hypotheses (one per metric).
    If we correct per metric type (Pearson vs Spearman), we might do 3 corrections for Pearson and 3 for Spearman.
    Let's assume the standard interpretation: 3 hypotheses (Metric 1, Metric 2, Metric 3).
    We will correct the p-values for each metric. If both Pearson and Spearman are present,
    we apply the correction to both, but the "3 tests" constraint suggests we are testing the
    relationship of the metric to conductivity.
    
    Correction: p_corrected = min(p * m, 1.0) where m is the number of tests.
    Here m = 3.
    """
    m = 3 # Number of metrics (hypotheses)
    corrected_results = {}
    
    for metric, data in correlation_results.items():
        corrected_data = data.copy()
        
        if data['pearson_p'] is not None:
            corrected_data['pearson_p_corrected'] = min(data['pearson_p'] * m, 1.0)
            corrected_data['pearson_significant'] = corrected_data['pearson_p_corrected'] < alpha
        
        if data['spearman_p'] is not None:
            corrected_data['spearman_p_corrected'] = min(data['spearman_p'] * m, 1.0)
            corrected_data['spearman_significant'] = corrected_data['spearman_p_corrected'] < alpha
        
        corrected_results[metric] = corrected_data
        
    return corrected_results

def run_kfold_cross_validation(X: pd.DataFrame, y: pd.Series, n_splits: int = 5) -> Dict[str, Any]:
    """Perform k-fold cross validation for linear regression."""
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import KFold
    
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    r2_scores = []
    rmse_scores = []
    
    model = LinearRegression()
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r2 = model.score(X_test, y_test)
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
    
    return {
        'r2_scores': r2_scores,
        'rmse_scores': rmse_scores,
        'mean_r2': float(np.mean(r2_scores)),
        'std_r2': float(np.std(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores)),
        'std_rmse': float(np.std(rmse_scores))
    }

def main():
    """
    Main entry point for analysis tasks including correlation and Bonferroni correction.
    This function specifically addresses T016 and T017.
    """
    logger = setup_analysis_logger()
    
    # Paths
    metrics_path = Path("data/processed/metrics.csv")
    correlations_path = Path("results/correlations.json")
    
    if not metrics_path.exists():
        logger.error(f"Metrics file not found at {metrics_path}")
        return
    
    logger.info("Loading metrics data...")
    df = load_metrics_csv(str(metrics_path))
    
    # Identify columns
    network_metrics = get_network_metrics(df)
    if not network_metrics:
        logger.warning("No network metrics found in the dataframe.")
        return
    
    target_col = get_thermal_conductivity_col(df)
    logger.info(f"Target column: {target_col}")
    logger.info(f"Network metrics found: {network_metrics}")
    
    # Compute correlations (T016)
    logger.info("Computing correlations...")
    raw_correlations = compute_correlations(df, network_metrics, target_col)
    
    # Apply Bonferroni Correction (T017)
    logger.info("Applying Bonferroni correction (m=3)...")
    corrected_correlations = apply_bonferroni_correction(raw_correlations)
    
    # Save results
    correlations_path.parent.mkdir(parents=True, exist_ok=True)
    with open(correlations_path, 'w') as f:
        json.dump(corrected_correlations, f, indent=2)
    
    logger.info(f"Correlation results saved to {correlations_path}")
    
    # Log summary
    for metric, data in corrected_correlations.items():
        logger.info(f"{metric}: Pearson p-corr={data.get('pearson_p_corrected', 'N/A'):.4f}, Significant={data.get('pearson_significant', False)}")

if __name__ == "__main__":
    main()