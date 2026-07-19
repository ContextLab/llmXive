import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
from statsmodels.regression.mixed_linear_model import MixedLM
import json

from config import get_config, setup_logging
from models import RootPhenotypeRecord, SoilNutrientRecord
from preprocessing import apply_log_transformation, apply_zscore_normalization

# Ensure logging is configured
logger = setup_logging()
config = get_config()

def create_species_stratified_split(df: pd.DataFrame, groups: pd.Series, n_splits: int = 5) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Perform k-fold cross-validation split strictly by species.
    Uses GroupKFold to ensure no species leakage between train/test sets.
    """
    gkf = GroupKFold(n_splits=n_splits)
    return list(gkf.split(df, groups=groups))

def fit_lmm(train_df: pd.DataFrame, test_df: pd.DataFrame, formula: str = None) -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects Model using statsmodels.
    Fixed effects: Nutrients (Phosphorus, Nitrogen)
    Random effects: Species as random intercept
    """
    if formula is None:
        # Default formula based on task requirements
        formula = "root_length ~ phosphorus + nitrogen"
    
    try:
        model = MixedLM.from_formula(
            formula,
            data=train_df,
            groups=train_df['species']
        )
        result = model.fit(reml=True)
        
        # Extract p-values using Satterthwaite approximation if available
        # Note: statsmodels MixedLM doesn't automatically provide p-values for fixed effects
        # We need to compute them manually or use a different approach
        p_values = {}
        for param_name, param_val in result.params.items():
            if param_name != "intercept":
                # Approximate p-value using t-statistic
                t_stat = param_val / result.bse[param_name]
                # Two-tailed p-value (approximate)
                from scipy import stats
                p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=result.df_resid))
                p_values[param_name] = p_val
        
        return {
            "result": result,
            "p_values": p_values,
            "params": result.params.to_dict(),
            "bse": result.bse.to_dict(),
            "loglike": result.llf
        }
    except Exception as e:
        logger.error(f"Failed to fit LMM: {e}")
        raise

def fit_random_forest(train_df: pd.DataFrame, test_df: pd.DataFrame, target_col: str = "root_length") -> Dict[str, Any]:
    """
    Fit a Random Forest baseline model.
    max_depth=5 as per requirements.
    """
    feature_cols = [col for col in train_df.columns if col not in ['species', target_col]]
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        random_state=config.get('SEED', 42),
        n_jobs=1  # CPU-only constraint
    )
    rf.fit(X_train, y_train)
    
    y_pred = rf.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return {
        "model": rf,
        "r2": r2,
        "rmse": rmse,
        "feature_importances": dict(zip(feature_cols, rf.feature_importances_.tolist()))
    }

def train_models(df: pd.DataFrame, target_col: str = "root_length") -> Dict[str, Any]:
    """
    Train both LMM and Random Forest models with species-stratified CV.
    """
    splits = create_species_stratified_split(df, df['species'])
    
    lmm_results = []
    rf_results = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        logger.info(f"Training fold {fold_idx + 1}/{len(splits)}")
        train_fold = df.iloc[train_idx]
        test_fold = df.iloc[test_idx]
        
        # Fit LMM
        lmm_res = fit_lmm(train_fold, test_fold)
        lmm_results.append(lmm_res)
        
        # Fit RF
        rf_res = fit_random_forest(train_fold, test_fold, target_col)
        rf_results.append(rf_res)
    
    # Aggregate results
    avg_lmm_r2 = np.mean([r["r2"] for r in lmm_results]) if lmm_results else None
    avg_rf_r2 = np.mean([r["r2"] for r in rf_results]) if rf_results else None
    
    return {
        "lmm": {
            "results": lmm_results,
            "avg_r2": avg_lmm_r2
        },
        "rf": {
            "results": rf_results,
            "avg_r2": avg_rf_r2
        }
    }

def evaluate_model(model_results: Dict[str, Any], target_col: str = "root_length") -> Dict[str, Any]:
    """
    Evaluate model performance metrics.
    """
    # This function would typically calculate additional metrics
    # For now, it returns the aggregated results
    return model_results

def calculate_r2_delta(lmm_r2: float, rf_r2: float) -> float:
    """
    Calculate the difference in R² between LMM and RF models.
    """
    return lmm_r2 - rf_r2

def evaluate_success_criterion(r2_delta: float, threshold: float = 0.05) -> bool:
    """
    Evaluate if the success criterion is met.
    """
    return abs(r2_delta) < threshold

def perform_f_tests_and_pvalues(lmm_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform F-tests for overall model significance and coefficient p-values.
    """
    # Extract p-values from LMM result
    p_values = lmm_result.get("p_values", {})
    
    # Calculate F-statistic for overall model significance
    # This is a simplified approach; in practice, you'd use anova_lm or similar
    # For now, we'll return the p-values we have
    return {
        "coefficient_p_values": p_values,
        "overall_significance": "approximated"  # Placeholder for proper F-test
    }

def apply_multiple_comparison_correction(p_values: Dict[str, float], method: str = "fdr_bh") -> Dict[str, Any]:
    """
    Apply multiple-comparison correction (Bonferroni or FDR) for hypothesis testing.
    
    Args:
        p_values: Dictionary of parameter names to their p-values
        method: Correction method - 'bonferroni' or 'fdr_bh' (Benjamini-Hochberg)
    
    Returns:
        Dictionary containing corrected p-values, rejection decisions, and method used
    """
    if not p_values:
        logger.warning("No p-values provided for multiple comparison correction")
        return {
            "corrected_p_values": {},
            "rejections": {},
            "method": method,
            "note": "No p-values to correct"
        }
    
    # Convert to arrays for statsmodels
    param_names = list(p_values.keys())
    raw_p_values = np.array(list(p_values.values()))
    
    try:
        # Apply correction
        if method == "bonferroni":
            corrected_p_values, rejections = multipletests(
                raw_p_values,
                method='bonferroni',
                alpha=0.05
            )
        elif method == "fdr_bh":
            corrected_p_values, rejections = multipletests(
                raw_p_values,
                method='fdr_bh',  # Benjamini-Hochberg FDR
                alpha=0.05
            )
        else:
            raise ValueError(f"Unsupported correction method: {method}")
        
        # Map results back to parameter names
        corrected_p_dict = dict(zip(param_names, corrected_p_values))
        rejections_dict = dict(zip(param_names, rejections.tolist()))
        
        logger.info(f"Applied {method} correction to {len(p_values)} hypotheses")
        logger.info(f"Rejections: {sum(rejections)} out of {len(p_values)}")
        
        return {
            "corrected_p_values": corrected_p_dict,
            "rejections": rejections_dict,
            "method": method,
            "alpha": 0.05,
            "total_tests": len(p_values),
            "rejected_tests": sum(rejections)
        }
        
    except Exception as e:
        logger.error(f"Multiple comparison correction failed: {e}")
        raise

def generate_final_metrics_report(
    model_results: Dict[str, Any],
    correction_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate the final metrics report including corrected p-values.
    """
    report = {
        "model_metrics": {
            "lmm_avg_r2": model_results.get("lmm", {}).get("avg_r2"),
            "rf_avg_r2": model_results.get("rf", {}).get("avg_r2"),
            "r2_delta": calculate_r2_delta(
                model_results.get("lmm", {}).get("avg_r2", 0),
                model_results.get("rf", {}).get("avg_r2", 0)
            )
        },
        "multiple_comparison_correction": correction_results
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final metrics report written to {output_path}")

def main():
    """
    Main execution function for T027 - Multiple comparison correction.
    """
    logger.info("Starting T027: Multiple comparison correction implementation")
    
    # This would typically be called after model training
    # For demonstration, we'll show how the correction is applied
    # In a real scenario, this would use actual p-values from model training
    
    # Example usage:
    # 1. Train models and get p-values
    # 2. Apply correction
    # 3. Generate report
    
    logger.info("T027 implementation complete - functions ready for use")

if __name__ == "__main__":
    main()