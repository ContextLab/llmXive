import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut
from scipy.stats import pearsonr, spearmanr
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_descriptors(path: str) -> pd.DataFrame:
    """Load descriptors from CSV."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Descriptors file not found: {path}")
    return pd.read_csv(p)

def calculate_correlation_matrix(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Calculate Pearson and Spearman correlation matrices."""
    pearson_corr = df[feature_cols].corr(method='pearson')
    spearman_corr = df[feature_cols].corr(method='spearman')
    return pearson_corr, spearman_corr

def calculate_p_values(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate p-values for Pearson and Spearman correlations."""
    n = len(feature_cols)
    pearson_p = pd.DataFrame(np.zeros((n, n)), index=feature_cols, columns=feature_cols)
    spearman_p = pd.DataFrame(np.zeros((n, n)), index=feature_cols, columns=feature_cols)

    for i, col1 in enumerate(feature_cols):
        for j, col2 in enumerate(feature_cols):
            if i == j:
                pearson_p.iloc[i, j] = 0.0
                spearman_p.iloc[i, j] = 0.0
            elif i < j:
                p_pearson, _ = pearsonr(df[col1], df[col2])
                p_spearman, _ = spearmanr(df[col1], df[col2])
                pearson_p.iloc[i, j] = p_pearson
                pearson_p.iloc[j, i] = p_pearson
                spearman_p.iloc[i, j] = p_spearman
                spearman_p.iloc[j, i] = p_spearman
    return pearson_p, spearman_p

def benjamini_hochberg_fdr(p_values: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction to p-values."""
    flat_p = p_values.values.flatten()
    n = len(flat_p)
    indices = np.argsort(flat_p)
    sorted_p = flat_p[indices]
    
    # BH procedure
    ranks = np.arange(1, n + 1)
    adjusted_p = sorted_p * n / ranks
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    adjusted_p_matrix = np.zeros((n, n))
    for i, idx in enumerate(indices):
        row, col = divmod(idx, p_values.shape[1])
        adjusted_p_matrix[row, col] = adjusted_p[i]
    
    return pd.DataFrame(adjusted_p_matrix, index=p_values.index, columns=p_values.columns)

def save_correlation_matrix(matrix: pd.DataFrame, path: str):
    """Save correlation matrix to CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(path)
    logger.info(f"Saved correlation matrix to {path}")

def calculate_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.Series:
    """Calculate Variance Inflation Factor for features."""
    X = df[feature_cols].values
    vif_data = pd.Series(
        [variance_inflation_factor(X, i) for i in range(len(feature_cols))],
        index=feature_cols
    )
    return vif_data

def save_vif_diagnostic_log(vif_data: pd.Series, threshold: float = 5.0, path: str = "data/processed/vif_diagnostic_log.json"):
    """Save VIF diagnostic log with flags for high VIF."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    log = {
        "vif_values": vif_data.to_dict(),
        "threshold": threshold,
        "high_vif_features": [feat for feat, val in vif_data.items() if val > threshold],
        "flagged": len([feat for feat, val in vif_data.items() if val > threshold]) > 0
    }
    with open(path, 'w') as f:
        json.dump(log, f, indent=2)
    logger.info(f"Saved VIF diagnostic log to {path}")

def bootstrap_feature_importance(model_path: str, data_path: str, target_col: str, n_resamples: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """Bootstrap feature importance to calculate 95% CI."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    df = pd.read_csv(data_path)
    feature_cols = [col for col in df.columns if col not in [target_col, 'family']]
    X = df[feature_cols]
    y = df[target_col]
    
    np.random.seed(seed)
    importances = []
    
    for _ in range(n_resamples):
        indices = np.random.choice(len(X), size=len(X), replace=True)
        X_boot = X.iloc[indices]
        y_boot = y.iloc[indices]
        
        # Retrain model on bootstrapped data
        model_boot = GradientBoostingRegressor(
            n_estimators=model.n_estimators,
            max_depth=model.max_depth,
            learning_rate=model.learning_rate,
            random_state=seed
        )
        model_boot.fit(X_boot, y_boot)
        importances.append(model_boot.feature_importances_)
    
    importances = np.array(importances)
    mean_importance = np.mean(importances, axis=0)
    std_importance = np.std(importances, axis=0)
    ci_lower = np.percentile(importances, 2.5, axis=0)
    ci_upper = np.percentile(importances, 97.5, axis=0)
    
    result = {
        "feature_importance_mean": dict(zip(feature_cols, mean_importance.tolist())),
        "feature_importance_std": dict(zip(feature_cols, std_importance.tolist())),
        "feature_importance_ci_95": {
            "lower": dict(zip(feature_cols, ci_lower.tolist())),
            "upper": dict(zip(feature_cols, ci_upper.tolist()))
        }
    }
    return result

def save_stability_metrics(metrics: Dict[str, Any], path: str = "artifacts/metrics/stability_metrics.json"):
    """Save stability metrics to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved stability metrics to {path}")

def run_sensitivity_analysis(
    model_path: str,
    data_path: str,
    family_col: str = 'family',
    target_col: str = 'Tg',
    max_depths: List[int] = [3, 5, 7],
    n_splits: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping max_depth and reporting variance of R² scores.
    
    FR-006: Sensitivity Analysis - sweep max_depth ∈ {3, 5, 7} and report variance of R² scores.
    """
    with open(model_path, 'rb') as f:
        best_model = pickle.load(f)
    
    df = pd.read_csv(data_path)
    feature_cols = [col for col in df.columns if col not in [target_col, family_col]]
    X = df[feature_cols]
    y = df[target_col]
    groups = df[family_col]
    
    logo = LeaveOneGroupOut()
    
    results = {}
    all_r2_scores = []
    
    logger.info(f"Starting sensitivity analysis with max_depths: {max_depths}")
    
    for depth in max_depths:
        logger.info(f"Evaluating max_depth={depth}")
        r2_scores = []
        
        for train_idx, test_idx in logo.split(X, y, groups):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            model = GradientBoostingRegressor(
                n_estimators=best_model.n_estimators,
                max_depth=depth,
                learning_rate=best_model.learning_rate,
                random_state=seed
            )
            model.fit(X_train, y_train)
            r2 = model.score(X_test, y_test)
            r2_scores.append(r2)
            all_r2_scores.append(r2)
        
        mean_r2 = np.mean(r2_scores)
        std_r2 = np.std(r2_scores)
        variance_r2 = np.var(r2_scores)
        
        results[depth] = {
            "mean_r2": mean_r2,
            "std_r2": std_r2,
            "variance_r2": variance_r2,
            "scores": r2_scores
        }
        logger.info(f"max_depth={depth}: Mean R²={mean_r2:.4f}, Variance={variance_r2:.6f}")
    
    overall_variance = np.var(all_r2_scores)
    sensitivity_report = {
        "max_depths_tested": max_depths,
        "results_by_depth": {str(k): v for k, v in results.items()},
        "overall_variance_across_all_depths": overall_variance,
        "interpretation": (
            "Lower variance indicates model stability across hyperparameter changes. "
            "Significant variance suggests sensitivity to max_depth choice."
        )
    }
    
    return sensitivity_report

def save_sensitivity_report(report: Dict[str, Any], path: str = "artifacts/metrics/sensitivity_analysis.json"):
    """Save sensitivity analysis report to JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved sensitivity analysis report to {path}")

def main():
    """Main entry point for analysis pipeline."""
    logger.info("Starting analysis pipeline...")
    
    # Paths
    descriptors_path = "data/processed/descriptors.csv"
    model_path = "artifacts/models/best_model.pkl"
    target_col = "Tg"
    family_col = "family"
    
    # 1. Load descriptors
    logger.info(f"Loading descriptors from {descriptors_path}")
    df = load_descriptors(descriptors_path)
    feature_cols = [col for col in df.columns if col not in [target_col, family_col]]
    
    # 2. Correlation Analysis
    logger.info("Calculating correlation matrices...")
    pearson_corr, spearman_corr = calculate_correlation_matrix(df, feature_cols)
    save_correlation_matrix(pearson_corr, "data/processed/correlation_matrix_pearson.csv")
    save_correlation_matrix(spearman_corr, "data/processed/correlation_matrix_spearman.csv")
    
    # 3. P-values and FDR
    logger.info("Calculating p-values and applying FDR...")
    pearson_p, spearman_p = calculate_p_values(df, feature_cols)
    pearson_fdr = benjamini_hochberg_fdr(pearson_p)
    spearman_fdr = benjamini_hochberg_fdr(spearman_p)
    save_correlation_matrix(pearson_fdr, "data/processed/correlation_matrix_pearson_fdr.csv")
    save_correlation_matrix(spearman_fdr, "data/processed/correlation_matrix_spearman_fdr.csv")
    
    # 4. VIF Calculation
    logger.info("Calculating VIF...")
    vif_data = calculate_vif(df, feature_cols)
    save_vif_diagnostic_log(vif_data)
    
    # 5. Bootstrap Feature Importance
    logger.info("Running bootstrap feature importance...")
    stability_metrics = bootstrap_feature_importance(model_path, descriptors_path, target_col)
    save_stability_metrics(stability_metrics)
    
    # 6. Sensitivity Analysis (T037)
    logger.info("Running sensitivity analysis (T037)...")
    sensitivity_report = run_sensitivity_analysis(
        model_path=model_path,
        data_path=descriptors_path,
        family_col=family_col,
        target_col=target_col,
        max_depths=[3, 5, 7]
    )
    save_sensitivity_report(sensitivity_report)
    
    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()