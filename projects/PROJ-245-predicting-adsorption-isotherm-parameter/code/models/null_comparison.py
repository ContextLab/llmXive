import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold

# Import from existing project modules
from models.evaluate import bootstrap_confidence_intervals, load_test_data, load_models, prepare_features_and_target
from utils.runtime_logger import start_timer, end_timer, get_elapsed_seconds, persist_runtime_log

logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        Path("data/validation"),
        Path("data/results")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs

def predict_mean_null_model(X_train: pd.DataFrame, y_train: pd.Series, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[np.ndarray, float]:
    """
    Implement a null model that predicts the mean of the training target for all test samples.
    
    Args:
        X_train: Training features (not used, but required for signature consistency)
        y_train: Training targets
        X_test: Test features (not used)
        y_test: Test targets
        
    Returns:
        Tuple of (predictions, mean_train_target)
    """
    mean_target = y_train.mean()
    predictions = np.full(len(y_test), mean_target)
    return predictions, mean_target

def calculate_null_model_metrics(y_test: pd.Series, predictions: np.ndarray) -> Dict[str, float]:
    """
    Calculate metrics for the null model.
    
    Args:
        y_test: Actual test values
        predictions: Null model predictions
        
    Returns:
        Dictionary with RMSE, R2, MAE
    """
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    mae = np.mean(np.abs(y_test - predictions))
    
    return {
        "rmse": float(rmse),
        "r2": float(r2),
        "mae": float(mae)
    }

def compare_models_with_bootstrap(
    y_test: pd.Series,
    y_pred_trained: np.ndarray,
    y_pred_null: np.ndarray,
    n_bootstrap: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Compare trained model vs null model using paired t-test and bootstrap confidence intervals.
    
    Args:
        y_test: Actual test values
        y_pred_trained: Trained model predictions
        y_pred_null: Null model predictions
        n_bootstrap: Number of bootstrap resamples
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with comparison results including p-values and CIs
    """
    # Calculate per-sample errors
    errors_trained = y_test.values - y_pred_trained
    errors_null = y_test.values - y_pred_null
    
    # RMSE for each model
    rmse_trained = np.sqrt(np.mean(errors_trained**2))
    rmse_null = np.sqrt(np.mean(errors_null**2))
    
    # RMSE reduction percentage
    rmse_reduction_pct = ((rmse_null - rmse_trained) / rmse_null) * 100
    
    # Paired t-test on squared errors (for RMSE comparison)
    squared_errors_trained = errors_trained**2
    squared_errors_null = errors_null**2
    
    t_stat, p_value = stats.ttest_rel(squared_errors_null, squared_errors_trained)
    
    # Wilcoxon signed-rank test as non-parametric alternative
    wilcoxon_stat, wilcoxon_p = stats.wilcoxon(squared_errors_null, squared_errors_trained)
    
    # Bootstrap confidence intervals for R2
    # Calculate R2 for each model
    r2_trained = r2_score(y_test, y_pred_trained)
    r2_null = r2_score(y_test, y_pred_null)
    
    # Bootstrap for R2 of trained model
    np.random.seed(seed)
    n_samples = len(y_test)
    r2_bootstrap_trained = []
    r2_bootstrap_null = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        y_test_boot = y_test.values[indices]
        y_pred_trained_boot = y_pred_trained[indices]
        y_pred_null_boot = y_pred_null[indices]
        
        # Calculate R2 for bootstrap sample
        r2_boot_trained = r2_score(y_test_boot, y_pred_trained_boot)
        r2_boot_null = r2_score(y_test_boot, y_pred_null_boot)
        
        r2_bootstrap_trained.append(r2_boot_trained)
        r2_bootstrap_null.append(r2_boot_null)
    
    # Calculate 95% CI for trained model R2
    ci_lower_trained = float(np.percentile(r2_bootstrap_trained, 2.5))
    ci_upper_trained = float(np.percentile(r2_bootstrap_trained, 97.5))
    ci_trained = {"lower": ci_lower_trained, "upper": ci_upper_trained}
    
    # Calculate 95% CI for null model R2
    ci_lower_null = float(np.percentile(r2_bootstrap_null, 2.5))
    ci_upper_null = float(np.percentile(r2_bootstrap_null, 97.5))
    ci_null = {"lower": ci_lower_null, "upper": ci_upper_null}
    
    # Determine significance
    is_significant = p_value < 0.05
    improvement_significant = rmse_reduction_pct > 20 and p_value < 0.05
    
    return {
        "rmse_trained": float(rmse_trained),
        "rmse_null": float(rmse_null),
        "rmse_reduction_pct": float(rmse_reduction_pct),
        "r2_trained": float(r2_trained),
        "r2_null": float(r2_null),
        "r2_ci_trained": ci_trained,
        "r2_ci_null": ci_null,
        "paired_t_test": {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "is_significant": bool(is_significant)
        },
        "wilcoxon_test": {
            "statistic": float(wilcoxon_stat),
            "p_value": float(wilcoxon_p),
            "is_significant": bool(wilcoxon_p < 0.05)
        },
        "meets_improvement_threshold": bool(improvement_significant),
        "threshold_pct": 20.0,
        "bootstrap_resamples": n_bootstrap,
        "seed": seed
    }

def run_cross_fold_comparison(
    X: pd.DataFrame,
    y: pd.Series,
    model,
    n_splits: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run paired comparison across cross-validation folds.
    
    Args:
        X: Feature matrix
        y: Target vector
        model: Trained model object with .predict() method
        n_splits: Number of CV folds
        seed: Random seed
        
    Returns:
        Comparison results aggregated across folds
    """
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    
    trained_rmse_list = []
    null_rmse_list = []
    trained_r2_list = []
    null_r2_list = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train_fold = X.iloc[train_idx]
        y_train_fold = y.iloc[train_idx]
        X_test_fold = X.iloc[test_idx]
        y_test_fold = y.iloc[test_idx]
        
        # Train model on fold
        model_fold = model.clone() if hasattr(model, 'clone') else model
        if hasattr(model_fold, 'fit'):
            model_fold.fit(X_train_fold, y_train_fold)
        
        # Predictions
        y_pred_trained = model_fold.predict(X_test_fold)
        y_pred_null, _ = predict_mean_null_model(X_train_fold, y_train_fold, X_test_fold, y_test_fold)
        
        # Calculate metrics
        rmse_trained = np.sqrt(mean_squared_error(y_test_fold, y_pred_trained))
        rmse_null = np.sqrt(mean_squared_error(y_test_fold, y_pred_null))
        r2_trained = r2_score(y_test_fold, y_pred_trained)
        r2_null = r2_score(y_test_fold, y_pred_null)
        
        trained_rmse_list.append(rmse_trained)
        null_rmse_list.append(rmse_null)
        trained_r2_list.append(r2_trained)
        null_r2_list.append(r2_null)
    
    # Aggregate results
    avg_rmse_trained = np.mean(trained_rmse_list)
    avg_rmse_null = np.mean(null_rmse_list)
    avg_r2_trained = np.mean(trained_r2_list)
    avg_r2_null = np.mean(null_r2_list)
    
    rmse_reduction_pct = ((avg_rmse_null - avg_rmse_trained) / avg_rmse_null) * 100
    
    # Paired t-test across folds
    t_stat, p_value = stats.ttest_rel(null_rmse_list, trained_rmse_list)
    
    # Bootstrap CI for R2 across folds
    bootstrap_r2_trained = []
    bootstrap_r2_null = []
    np.random.seed(seed)
    
    for _ in range(1000):
        indices = np.random.choice(len(trained_r2_list), size=len(trained_r2_list), replace=True)
        bootstrap_r2_trained.append(np.mean([trained_r2_list[i] for i in indices]))
        bootstrap_r2_null.append(np.mean([null_r2_list[i] for i in indices]))
    
    ci_lower_trained = float(np.percentile(bootstrap_r2_trained, 2.5))
    ci_upper_trained = float(np.percentile(bootstrap_r2_trained, 97.5))
    ci_lower_null = float(np.percentile(bootstrap_r2_null, 2.5))
    ci_upper_null = float(np.percentile(bootstrap_r2_null, 97.5))
    
    return {
        "method": "cross_fold_paired",
        "n_folds": n_splits,
        "avg_rmse_trained": float(avg_rmse_trained),
        "avg_rmse_null": float(avg_rmse_null),
        "rmse_reduction_pct": float(rmse_reduction_pct),
        "avg_r2_trained": float(avg_r2_trained),
        "avg_r2_null": float(avg_r2_null),
        "r2_ci_trained": {"lower": ci_lower_trained, "upper": ci_upper_trained},
        "r2_ci_null": {"lower": ci_lower_null, "upper": ci_upper_null},
        "paired_t_test": {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "is_significant": bool(p_value < 0.05)
        },
        "meets_improvement_threshold": bool(rmse_reduction_pct > 20 and p_value < 0.05),
        "threshold_pct": 20.0
    }

def main():
    """
    Main function to run null model comparison and save results.
    """
    start_timer("null_comparison")
    
    # Ensure directories
    ensure_dirs()
    
    logger.info("Starting null model comparison analysis...")
    
    try:
        # Load test data
        X_test, y_test = load_test_data()
        
        if X_test is None or y_test is None or len(X_test) == 0:
            logger.error("No test data available for null model comparison")
            result = {
                "status": "failed",
                "reason": "No test data available",
                "timestamp": str(pd.Timestamp.now())
            }
            output_path = Path("data/validation/null_model_comparison.json")
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            return result
        
        logger.info(f"Loaded test data with {len(X_test)} samples")
        
        # Load trained models
        models = load_models()
        
        if not models:
            logger.error("No trained models available for comparison")
            result = {
                "status": "failed",
                "reason": "No trained models available",
                "timestamp": str(pd.Timestamp.now())
            }
            output_path = Path("data/validation/null_model_comparison.json")
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            return result
        
        # Get the best model (usually the last one or the one with best metrics)
        best_model_name = list(models.keys())[0]
        best_model = models[best_model_name]
        logger.info(f"Using model: {best_model_name}")
        
        # Prepare features and target
        X, y = prepare_features_and_target(X_test, y_test)
        
        # Run cross-fold comparison
        logger.info("Running cross-fold paired comparison...")
        cross_fold_results = run_cross_fold_comparison(X, y, best_model)
        
        # Also run single-split comparison for completeness
        logger.info("Running single-split comparison with bootstrap...")
        y_pred_trained = best_model.predict(X)
        y_pred_null, _ = predict_mean_null_model(X, y, X, y)
        
        single_split_results = compare_models_with_bootstrap(
            y_test,
            y_pred_trained,
            y_pred_null,
            n_bootstrap=1000,
            seed=42
        )
        
        # Combine results
        final_result = {
            "status": "success",
            "timestamp": str(pd.Timestamp.now()),
            "cross_fold_comparison": cross_fold_results,
            "single_split_comparison": single_split_results,
            "summary": {
                "best_method": "cross_fold_paired" if cross_fold_results.get("is_significant") else "single_split",
                "rmse_improvement_pct": cross_fold_results.get("rmse_reduction_pct", 0),
                "p_value": cross_fold_results.get("paired_t_test", {}).get("p_value", 1.0),
                "is_significant": cross_fold_results.get("paired_t_test", {}).get("is_significant", False),
                "meets_20pct_threshold": cross_fold_results.get("meets_improvement_threshold", False),
                "r2_trained": cross_fold_results.get("avg_r2_trained", 0),
                "r2_null": cross_fold_results.get("avg_r2_null", 0),
                "r2_ci_95": cross_fold_results.get("r2_ci_trained", {})
            }
        }
        
        # Save results
        output_path = Path("data/validation/null_model_comparison.json")
        with open(output_path, 'w') as f:
            json.dump(final_result, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        logger.info(f"RMSE improvement: {cross_fold_results.get('rmse_reduction_pct', 0):.2f}%")
        logger.info(f"P-value: {cross_fold_results.get('paired_t_test', {}).get('p_value', 1.0):.4f}")
        logger.info(f"Significant: {cross_fold_results.get('paired_t_test', {}).get('is_significant', False)}")
        
        end_timer("null_comparison")
        persist_runtime_log()
        
        return final_result
        
    except Exception as e:
        logger.error(f"Error during null model comparison: {str(e)}", exc_info=True)
        result = {
            "status": "failed",
            "reason": str(e),
            "timestamp": str(pd.Timestamp.now())
        }
        output_path = Path("data/validation/null_model_comparison.json")
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
