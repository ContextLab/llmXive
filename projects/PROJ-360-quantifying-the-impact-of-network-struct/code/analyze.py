import os
import json
import logging
import csv
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import scipy.stats as stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd

# Configuration paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "metrics.csv"
CORRELATIONS_PATH = PROJECT_ROOT / "results" / "correlations.json"
POWER_LOG_PATH = PROJECT_ROOT / "results" / "power_analysis.log"

def setup_analysis_logger() -> logging.Logger:
    logger = logging.getLogger("analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_metrics_csv(logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    if logger:
        logger.info(f"Loading metrics from {METRICS_PATH}")
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Metrics file not found: {METRICS_PATH}")
    # Handle potential header comments in CSV
    df = pd.read_csv(METRICS_PATH, comment='#')
    return df

def get_network_metrics(df: pd.DataFrame) -> List[str]:
    # Defined in FR-003 and T013: average_degree, avg_shortest_path, clustering_coeff
    cols = [c for c in df.columns if c in ['average_degree', 'avg_shortest_path', 'clustering_coeff']]
    return cols

def get_thermal_conductivity_col(df: pd.DataFrame) -> str:
    # Defined in T015
    if 'thermal_conductivity' in df.columns:
        return 'thermal_conductivity'
    raise KeyError("Column 'thermal_conductivity' not found in metrics.csv")

def compute_correlations(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, Any]:
    logger.info("Computing Pearson and Spearman correlations")
    metrics = get_network_metrics(df)
    target_col = get_thermal_conductivity_col(df)
    
    results = []
    for metric in metrics:
        # Drop NaNs for correlation calculation
        valid_data = df[[metric, target_col]].dropna()
        if len(valid_data) < 3:
            logger.warning(f"Insufficient data for correlation between {metric} and {target_col}")
            continue
        
        x = valid_data[metric].values
        y = valid_data[target_col].values

        # Pearson
        pearson_r, pearson_p = stats.pearsonr(x, y)
        # Spearman
        spearman_r, spearman_p = stats.spearmanr(x, y)

        results.append({
            "metric": metric,
            "target": target_col,
            "pearson": {"r": float(pearson_r), "p_value": float(pearson_p)},
            "spearman": {"r": float(spearman_r), "p_value": float(spearman_p)}
        })
    
    return {"correlations": results}

def apply_bonferroni_correction(correlation_results: Dict[str, Any], alpha: float = 0.05, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Implements Bonferroni correction for the 3 correlation tests.
    Controls family-wise error rate at alpha <= 0.05.
    """
    if logger:
        logger.info(f"Applying Bonferroni correction with alpha={alpha}")
    
    correlations = correlation_results.get("correlations", [])
    n_tests = len(correlations) * 2 # Pearson and Spearman for each metric
    
    if n_tests == 0:
        logger.warning("No correlations found to correct.")
        return correlation_results

    bonferroni_alpha = alpha / n_tests
    if logger:
        logger.info(f"Number of tests: {n_tests}, Corrected alpha threshold: {bonferroni_alpha:.6f}")

    corrected_results = []
    for item in correlations:
        metric = item["metric"]
        
        # Process Pearson
        p_pearson = item["pearson"]["p_value"]
        is_sig_pearson = p_pearson < bonferroni_alpha
        corrected_item_pearson = {
            "test": "pearson",
            "metric": metric,
            "r": item["pearson"]["r"],
            "p_value": p_pearson,
            "bonferroni_p_value": p_pearson * n_tests, # Adjusted p-value
            "significant_at_alpha": is_sig_pearson,
            "threshold": bonferroni_alpha
        }
        
        # Process Spearman
        p_spearman = item["spearman"]["p_value"]
        is_sig_spearman = p_spearman < bonferroni_alpha
        corrected_item_spearman = {
            "test": "spearman",
            "metric": metric,
            "r": item["spearman"]["r"],
            "p_value": p_spearman,
            "bonferroni_p_value": p_spearman * n_tests, # Adjusted p-value
            "significant_at_alpha": is_sig_spearman,
            "threshold": bonferroni_alpha
        }

        corrected_results.append({
            "metric": metric,
            "pearson": corrected_item_pearson,
            "spearman": corrected_item_spearman
        })

    final_output = {
        "original_correlations": correlation_results,
        "correction_method": "Bonferroni",
        "family_wise_alpha": alpha,
        "num_tests": n_tests,
        "corrected_alpha_threshold": bonferroni_alpha,
        "corrected_results": corrected_results
    }

    if logger:
        logger.info(f"Bonferroni correction complete. Results saved to {CORRELATIONS_PATH}")
    
    return final_output

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for given features."""
    if len(features) == 0:
        return {}
    X = df[features].dropna()
    if X.shape[0] < len(features) + 1:
        raise ValueError("Not enough samples to calculate VIF")
    
    vif_data = {}
    for i, feature in enumerate(features):
        # VIF requires an intercept column in the model matrix for statsmodels
        # We add a constant column manually
        X_const = sm.add_constant(X)
        try:
            model = sm.OLS(X[feature], X_const).fit()
            vif = model.rsquared_adj # This is wrong, need to calculate VIF properly
            # Correct VIF calculation: 1 / (1 - R^2) where R^2 is from regressing feature i on all others
            # Simpler approach using variance_inflation_factor from statsmodels
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = vif
        except Exception as e:
            logging.error(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = np.nan
    return vif_data

def log_vif_results(vif_data: Dict[str, float], logger: logging.Logger):
    logger.info("VIF Results:")
    for feat, val in vif_data.items():
        logger.info(f"  {feat}: {val:.4f}")

def run_kfold_cross_validation(X: pd.DataFrame, y: pd.Series, n_splits: int = 5, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import mean_squared_error
    
    model = LinearRegression()
    r2_scores = cross_val_score(model, X, y, cv=n_splits, scoring='r2')
    # Calculate RMSE via custom CV loop or approx
    # For simplicity in this context, we'll run the loop manually to get RMSE per fold
    rmse_scores = []
    for train_idx, test_idx in None: # Placeholder, need proper KFold
        pass
    
    # Manual CV for RMSE
    from sklearn.model_selection import KFold
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    for train_index, test_index in kf.split(X):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        rmse_scores.append(rmse)

    return {
        "r2_scores": r2_scores.tolist(),
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "rmse_scores": rmse_scores,
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores))
    }

def main():
    logger = setup_analysis_logger()
    logger.info("Starting Analysis Pipeline")
    
    try:
        df = load_metrics_csv(logger)
        logger.info(f"Loaded {len(df)} records")
        
        # Step 1: Compute Correlations
        corr_results = compute_correlations(df, logger)
        
        # Step 2: Apply Bonferroni Correction (T017)
        final_results = apply_bonferroni_correction(corr_results, alpha=0.05, logger=logger)
        
        # Save results
        CORRELATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CORRELATIONS_PATH, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Analysis complete. Results saved to {CORRELATIONS_PATH}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()