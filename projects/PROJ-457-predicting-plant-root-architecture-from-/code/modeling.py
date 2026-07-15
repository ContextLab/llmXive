import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.multitest import multipletests
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from config import get_config, setup_logging

# Ensure logging is configured
logger = logging.getLogger(__name__)

def create_species_stratified_split(data: pd.DataFrame, n_splits: int = 5) -> Tuple[List, List]:
    """
    Create species-level stratified cross-validation splits using GroupKFold.
    """
    if 'species' not in data.columns:
        raise ValueError("Data must contain a 'species' column for stratified splitting.")
    
    groups = data['species']
    gkf = GroupKFold(n_splits=n_splits)
    
    train_indices_list = []
    test_indices_list = []
    
    for train_idx, test_idx in gkf.split(data, groups=groups):
        train_indices_list.append(train_idx)
        test_indices_list.append(test_idx)
        
    return train_indices_list, test_indices_list

def fit_lmm(data: pd.DataFrame, formula: str, groups: pd.Series) -> Any:
    """
    Fit a Linear Mixed-Effects Model using statsmodels.
    """
    # Ensure formula is valid and data is clean
    # Simple check for missing values in relevant columns
    if data.isnull().any().any():
        logger.warning("Data contains missing values. Dropping rows for LMM fit.")
        data = data.dropna(subset=formula.split('+') + [formula.split('~')[0].strip()])
    
    if data.empty:
        raise ValueError("No valid data remaining for LMM fitting after dropping NaNs.")

    model = MixedLM.from_formula(formula, groups=groups, data=data, re_formula="1")
    result = model.fit(reml=True)
    return result

def fit_random_forest(X: np.ndarray, y: np.ndarray, max_depth: int = 5, n_estimators: int = 100) -> RandomForestRegressor:
    """
    Fit a Random Forest baseline model.
    """
    rf = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators, random_state=42)
    rf.fit(X, y)
    return rf

def train_models(data: pd.DataFrame, target_col: str, feature_cols: List[str], group_col: str = 'species') -> Dict[str, Any]:
    """
    Train LMM and Random Forest models with cross-validation.
    Returns a dictionary containing models, metrics, and CV results.
    """
    logger.info("Starting model training...")
    
    # Prepare data
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    X = data[feature_cols].values
    y = data[target_col].values
    groups = data[group_col]
    
    # Handle missing values in features for RF
    # Note: In a real pipeline, imputation should happen before this step, 
    # but we add a safeguard here for robustness if called directly.
    if np.isnan(X).any():
        logger.warning("NaNs found in features. Using simple mean imputation for RF training.")
        from sklearn.impute import SimpleImputer
        imputer = SimpleImputer(strategy='mean')
        X = imputer.fit_transform(X)
    
    # --- LMM Training ---
    logger.info("Fitting Linear Mixed-Effects Model...")
    # Construct formula dynamically: target ~ features
    # Assuming features are numeric and additive
    formula = f"{target_col} ~ {' + '.join(feature_cols)}"
    
    try:
        lmm_result = fit_lmm(data, formula, groups)
        lmm_metrics = {
            "log_likelihood": lmm_result.llf,
            "aic": lmm_result.aic,
            "bic": lmm_result.bic,
            "coefficients": lmm_result.params.to_dict()
        }
    except Exception as e:
        logger.error(f"LMM fitting failed: {e}")
        lmm_result = None
        lmm_metrics = {"error": str(e)}

    # --- Random Forest Training with CV ---
    logger.info("Fitting Random Forest with GroupKFold...")
    gkf = GroupKFold(n_splits=5)
    cv_scores = cross_val_score(fit_random_forest(X, y, n_estimators=50), X, y, cv=gkf, groups=groups, scoring='r2')
    
    # Fit final RF on full data
    rf_model = fit_random_forest(X, y, n_estimators=100)
    
    # Evaluate on full data (for reference, though CV is primary)
    y_pred = rf_model.predict(X)
    rf_metrics = {
        "cv_mean_r2": float(np.mean(cv_scores)),
        "cv_std_r2": float(np.std(cv_scores)),
        "full_data_r2": float(r2_score(y, y_pred)),
        "full_data_rmse": float(np.sqrt(mean_squared_error(y, y_pred)))
    }

    return {
        "lmm": lmm_result,
        "lmm_metrics": lmm_metrics,
        "rf_model": rf_model,
        "rf_metrics": rf_metrics,
        "cv_scores": cv_scores
    }

def evaluate_model(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate model performance and compare LMM vs RF.
    """
    # This function is a placeholder for more complex evaluation logic
    # that might be expanded in future tasks.
    return {
        "lmm_cv_r2": "N/A (LMM CV not implemented in basic flow)",
        "rf_cv_r2": results["rf_metrics"]["cv_mean_r2"]
    }

def calculate_r2_delta(lmm_r2: float, rf_r2: float) -> float:
    """
    Calculate the difference in R² between LMM and RF.
    """
    return lmm_r2 - rf_r2

def evaluate_success_criterion(r2_delta: float, threshold: float = 0.05) -> Tuple[str, float]:
    """
    Evaluate if the R² difference meets the success criterion (<= 5%).
    """
    status = "PASS" if abs(r2_delta) <= threshold else "FAIL"
    return status, r2_delta

def perform_f_tests_and_pvalues(lmm_result: MixedLM) -> Dict[str, float]:
    """
    Perform F-tests for overall model significance and extract coefficient p-values.
    Note: statsmodels MixedLM does not provide direct F-test for the whole model 
    in the same way as OLS. We rely on the t-tests for individual coefficients 
    and the likelihood ratio test (LRT) for model comparison if needed.
    For this task, we extract p-values from the summary.
    """
    # Extract p-values from the result summary
    # The 'pvalues' attribute is available in the result object
    pvalues = lmm_result.pvalues
    
    # Calculate an approximate F-statistic or use the t-stats squared for single df
    # Since MixedLM doesn't have a direct 'f_test' for the whole model like OLS,
    # we will focus on the coefficient p-values and the likelihood ratio if comparing models.
    # Here we just return the p-values as the primary metric for significance.
    
    return pvalues.to_dict()

def apply_multiple_comparison_correction(p_values: Dict[str, float], method: str = 'fdr_bh') -> Dict[str, Any]:
    """
    Apply multiple-comparison correction (Bonferroni or FDR) to hypothesis testing results.
    
    Args:
        p_values: Dictionary of coefficient names to raw p-values.
        method: Correction method ('fdr_bh' for Benjamini-Hochberg, 'bonferroni', etc.)
    
    Returns:
        Dictionary containing corrected p-values, rejection booleans, and original values.
    """
    if not p_values:
        logger.warning("No p-values provided for multiple comparison correction.")
        return {}

    # Extract values and keys
    labels = list(p_values.keys())
    raw_pvals = np.array(list(p_values.values()))
    
    # Filter out non-numeric or NaN p-values if any
    valid_mask = np.isfinite(raw_pvals)
    if not np.all(valid_mask):
        logger.warning(f"Found {np.sum(~valid_mask)} non-finite p-values. Excluding them from correction.")
        valid_labels = [l for l, m in zip(labels, valid_mask) if m]
        valid_pvals = raw_pvals[valid_mask]
    else:
        valid_labels = labels
        valid_pvals = raw_pvals

    if len(valid_pvals) == 0:
        return {}

    # Apply correction
    # multipletests returns: (reject, pvals_corrected, pvals_corrected_raw, alphacSidak, alphacBonf)
    reject, pvals_corrected, _, _ = multipletests(valid_pvals, alpha=0.05, method=method)
    
    # Map results back to labels
    corrected_results = {}
    for i, label in enumerate(valid_labels):
        corrected_results[label] = {
            "raw_pvalue": float(valid_pvals[i]),
            "corrected_pvalue": float(pvals_corrected[i]),
            "rejected": bool(reject[i])
        }
    
    logger.info(f"Applied {method} correction to {len(valid_labels)} hypotheses. "
                f"{np.sum(reject)} hypotheses rejected at alpha=0.05.")
                
    return corrected_results

def generate_final_metrics_report(results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate the final metrics report JSON including R², RMSE, p-values, 
    and multiple-comparison corrected results.
    """
    report = {
        "lmm_metrics": results.get("lmm_metrics", {}),
        "rf_metrics": results.get("rf_metrics", {}),
        "comparison": {
            "r2_delta": results.get("r2_delta", None),
            "success_criterion_met": results.get("success_criterion_met", None),
            "sc002_status": results.get("sc002_status", None)
        },
        "hypothesis_testing": {
            "method": "fdr_bh", # Default method used
            "results": results.get("corrected_pvalues", {})
        }
    }
    
    # Save to JSON
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final metrics report saved to {output_path}")

def main():
    """
    Main execution function for the modeling pipeline.
    """
    config = get_config()
    setup_logging(config)
    
    # Load preprocessed data (assumed to be generated by previous tasks)
    # Adjust path based on actual project structure
    data_path = Path(config.get('DATA_PATH', 'data/processed/merged_data.csv'))
    if not data_path.exists():
        logger.error(f"Data file not found at {data_path}. Please run data ingestion and preprocessing first.")
        sys.exit(1)
    
    data = pd.read_csv(data_path)
    
    # Define target and features
    target_col = 'root_length' # Example target
    feature_cols = ['phosphorus', 'nitrogen'] # Example features
    
    # Train models
    results = train_models(data, target_col, feature_cols)
    
    # Calculate R² delta and success criterion
    # Note: LMM R² is not directly provided by statsmodels in the same way as RF.
    # We might need to calculate pseudo-R² for LMM or use the RF R² for comparison.
    # For this implementation, we will use the RF R² for both if LMM R² is not available,
    # or calculate a pseudo-R² for LMM.
    # Let's assume we calculate a simple pseudo-R² for LMM: 1 - (resid_ss / total_ss)
    if results["lmm"]:
        lmm_resid_ss = np.sum(results["lmm"].resid**2)
        total_ss = np.sum((data[target_col] - data[target_col].mean())**2)
        lmm_r2 = 1 - (lmm_resid_ss / total_ss) if total_ss > 0 else 0.0
    else:
        lmm_r2 = 0.0
        
    rf_r2 = results["rf_metrics"]["full_data_r2"]
    r2_delta = calculate_r2_delta(lmm_r2, rf_r2)
    sc_status, _ = evaluate_success_criterion(r2_delta)
    
    results["r2_delta"] = r2_delta
    results["success_criterion_met"] = abs(r2_delta) <= 0.05
    results["sc002_status"] = sc_status
    
    # Perform F-tests and get p-values
    if results["lmm"]:
        raw_pvalues = perform_f_tests_and_pvalues(results["lmm"])
        corrected_pvalues = apply_multiple_comparison_correction(raw_pvalues, method='fdr_bh')
        results["corrected_pvalues"] = corrected_pvalues
    else:
        results["corrected_pvalues"] = {}
    
    # Generate report
    report_path = Path('artifacts/reports/metrics.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_final_metrics_report(results, report_path)
    
    logger.info("Modeling pipeline completed successfully.")

if __name__ == "__main__":
    main()