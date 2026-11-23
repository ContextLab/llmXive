import logging
import json
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats
from datetime import datetime

# Local imports based on API surface
from utils.logging import log_result_artifact, log_error_summary
from models.rf import predict as rf_predict, evaluate_model as rf_evaluate
from models.gnn import create_mpnn_model, validate_epoch
import torch
import joblib
import os

logger = logging.getLogger(__name__)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate RMSE, MAE, and R² for given true and predicted values.
    
    Args:
        y_true: Array of true values
        y_pred: Array of predicted values
        
    Returns:
        Dictionary containing 'rmse', 'mae', 'r2'
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    
    if len(y_true) == 0:
        raise ValueError("Input arrays are empty")
        
    # RMSE
    mse = np.mean((y_true - y_pred) ** 2)
    rmse = np.sqrt(mse)
    
    # MAE
    mae = np.mean(np.abs(y_true - y_pred))
    
    # R²
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }

def paired_ttest(errors_a: np.ndarray, errors_b: np.ndarray) -> Dict[str, float]:
    """
    Perform a paired t-test on two sets of errors (e.g., absolute errors).
    
    Args:
        errors_a: Array of errors from model A
        errors_b: Array of errors from model B
        
    Returns:
        Dictionary containing 't_statistic', 'p_value', 'mean_diff', 'std_diff'
    """
    errors_a = np.array(errors_a)
    errors_b = np.array(errors_b)
    
    if len(errors_a) != len(errors_b):
        raise ValueError(f"Length mismatch: errors_a ({len(errors_a)}) != errors_b ({len(errors_b)})")
        
    if len(errors_a) < 2:
        raise ValueError("Need at least 2 samples for t-test")
        
    # Paired t-test
    t_stat, p_val = stats.ttest_rel(errors_a, errors_b)
    
    mean_diff = np.mean(errors_a - errors_b)
    std_diff = np.std(errors_a - errors_b, ddof=1)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_diff": float(mean_diff),
        "std_diff": float(std_diff)
    }

def post_hoc_power_analysis(effect_size: float, n_samples: int, alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate statistical power for a paired t-test given effect size and sample size.
    
    Args:
        effect_size: Cohen's d
        n_samples: Number of paired samples
        alpha: Significance level
        
    Returns:
        Dictionary containing 'power', 'effect_size', 'sample_size', 'alpha'
    """
    if n_samples < 2:
        return {
            "power": 0.0,
            "effect_size": effect_size,
            "sample_size": n_samples,
            "alpha": alpha,
            "note": "Insufficient samples for power calculation"
        }
        
    # Approximate power calculation for paired t-test
    # Using non-central t-distribution approximation
    df = n_samples - 1
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n_samples)
    
    # Power is the probability of rejecting the null hypothesis
    # P(|T| > t_crit | H1) = P(T > t_crit) + P(T < -t_crit)
    # For large n, we approximate with normal distribution for simplicity
    # Power ≈ Φ(ncp - t_crit) + Φ(-ncp - t_crit)
    # More accurate: use stats.nct.cdf but for simplicity we use normal approx
    
    z_crit = stats.norm.ppf(1 - alpha/2)
    power = stats.norm.cdf(ncp - z_crit) + stats.norm.cdf(-ncp - z_crit)
    
    # Ensure power is between 0 and 1
    power = max(0.0, min(1.0, power))
    
    return {
        "power": float(power),
        "effect_size": float(effect_size),
        "sample_size": int(n_samples),
        "alpha": float(alpha)
    }

def load_model_predictions(test_path: Path, model_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load test data and model predictions for a specific model.
    
    Args:
        test_path: Path to data/processed/test.csv
        model_name: Name of the model ('gnn', 'rf_baseline', 'rf_ablation')
        
    Returns:
        Tuple of (y_true, y_pred)
    """
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}")
        
    df = pd.read_csv(test_path)
    
    # Determine target column name
    target_col = None
    for col in ['target', 'y', 'permeability', 'logP', 'experimental_logP']:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        # Try to find any column that looks like a target
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # Assume the last numeric column is the target if not found
            target_col = numeric_cols[-1]
        else:
            raise ValueError("Could not identify target column in test data")
    
    y_true = df[target_col].values.astype(np.float64)
    
    # Load predictions
    pred_col = f"{model_name}_predictions"
    if pred_col not in df.columns:
        # Try alternative naming
        alt_pred_col = f"{model_name}_pred"
        if alt_pred_col in df.columns:
            pred_col = alt_pred_col
        else:
            raise KeyError(f"Predictions column '{pred_col}' not found in test data. Available columns: {df.columns.tolist()}")
    
    y_pred = df[pred_col].values.astype(np.float64)
    
    return y_true, y_pred

def load_model_metadata(model_name: str, project_root: Path) -> Dict[str, Any]:
    """
    Load training metadata (time, memory) for a model.
    
    Args:
        model_name: Name of the model
        project_root: Root path of the project
        
    Returns:
        Dictionary with training_time and peak_memory_gb
    """
    training_log_path = project_root / "results" / "training_log.json"
    
    default_meta = {
        "training_time": 0.0,
        "peak_memory_gb": 0.0
    }
    
    if not training_log_path.exists():
        logger.warning(f"Training log not found at {training_log_path}, using defaults")
        return default_meta
        
    try:
        with open(training_log_path, 'r') as f:
            log_data = json.load(f)
        
        # Look for model-specific metadata
        if isinstance(log_data, dict) and model_name in log_data:
            model_meta = log_data[model_name]
            return {
                "training_time": float(model_meta.get("training_time", 0.0)),
                "peak_memory_gb": float(model_meta.get("peak_memory_gb", 0.0))
            }
        elif isinstance(log_data, list):
            for entry in log_data:
                if entry.get("model_name") == model_name:
                    return {
                        "training_time": float(entry.get("training_time", 0.0)),
                        "peak_memory_gb": float(entry.get("peak_memory_gb", 0.0))
                    }
        
        logger.warning(f"Metadata for model '{model_name}' not found in training log")
        return default_meta
        
    except Exception as e:
        logger.error(f"Error reading training log: {e}")
        return default_meta

def evaluate_models(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main evaluation function that calculates metrics for all models and generates artifacts.
    
    Args:
        project_root: Project root directory. Defaults to parent of current file.
        
    Returns:
        Dictionary containing all metrics and evaluation results
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        
    test_path = project_root / "data" / "processed" / "test.csv"
    metrics_output_path = project_root / "results" / "metrics.json"
    predictions_errors_path = project_root / "results" / "predictions_errors.json"
    
    logger.info(f"Starting evaluation. Test data: {test_path}")
    
    if not test_path.exists():
        raise FileNotFoundError(f"Test data file not found: {test_path}. Please ensure T017 has completed successfully.")
    
    # Models to evaluate (excluding ablation as per task description)
    models_to_evaluate = ["gnn", "rf_baseline"]
    
    all_metrics = {}
    all_predictions_errors = {}
    comparison_results = {}
    
    # Evaluate each model
    for model_name in models_to_evaluate:
        logger.info(f"Evaluating model: {model_name}")
        try:
            y_true, y_pred = load_model_predictions(test_path, model_name)
            metrics = calculate_metrics(y_true, y_pred)
            
            # Add training metadata
            meta = load_model_metadata(model_name, project_root)
            metrics["training_time"] = meta["training_time"]
            metrics["peak_memory_gb"] = meta["peak_memory_gb"]
            metrics["sample_size"] = len(y_true)
            
            all_metrics[model_name] = metrics
            all_predictions_errors[model_name] = {
                "y_true": y_true.tolist(),
                "y_pred": y_pred.tolist(),
                "errors": (y_true - y_pred).tolist(),
                "abs_errors": np.abs(y_true - y_pred).tolist()
            }
            
            logger.info(f"  RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
            
        except Exception as e:
            logger.error(f"Error evaluating {model_name}: {e}")
            log_error_summary(e)
            all_metrics[model_name] = {"error": str(e)}
    
    # Perform paired t-test if both models succeeded
    if "gnn" in all_metrics and "rf_baseline" in all_metrics:
        if "error" not in all_metrics["gnn"] and "error" not in all_metrics["rf_baseline"]:
            try:
                y_true_gnn, y_pred_gnn = load_model_predictions(test_path, "gnn")
                y_true_rf, y_pred_rf = load_model_predictions(test_path, "rf_baseline")
                
                # Calculate absolute errors
                abs_errors_gnn = np.abs(y_true_gnn - y_pred_gnn)
                abs_errors_rf = np.abs(y_true_rf - y_pred_rf)
                
                t_test_results = paired_ttest(abs_errors_gnn, abs_errors_rf)
                
                # Calculate Cohen's d
                mean_diff = np.mean(abs_errors_gnn - abs_errors_rf)
                std_diff = np.std(abs_errors_gnn - abs_errors_rf, ddof=1)
                cohens_d = mean_diff / std_diff if std_diff != 0 else 0.0
                
                # Calculate confidence interval for mean difference
                n = len(abs_errors_gnn)
                se = std_diff / np.sqrt(n)
                t_crit = stats.t.ppf(0.975, n - 1)
                ci_lower = mean_diff - t_crit * se
                ci_upper = mean_diff + t_crit * se
                
                comparison_results = {
                    "t_test": t_test_results,
                    "cohens_d": float(cohens_d),
                    "confidence_interval": {
                        "lower": float(ci_lower),
                        "upper": float(ci_upper),
                        "level": 0.95
                    },
                    "sample_size": n
                }
                
                # Add to metrics
                all_metrics["comparison"] = comparison_results
                
                # Perform power analysis
                power_results = post_hoc_power_analysis(cohens_d, n)
                all_metrics["power_analysis"] = power_results
                
                logger.info(f"  T-test p-value: {t_test_results['p_value']:.6f}, Cohen's d: {cohens_d:.4f}")
                
            except Exception as e:
                logger.error(f"Error in statistical comparison: {e}")
                log_error_summary(e)
    
    # Compile final results
    final_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "test_file": str(test_path),
        "models": all_metrics,
        "comparison": comparison_results if comparison_results else None
    }
    
    # Save metrics.json
    try:
        with open(metrics_output_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        logger.info(f"Metrics saved to {metrics_output_path}")
        log_result_artifact(str(metrics_output_path), "metrics.json")
    except Exception as e:
        logger.error(f"Failed to save metrics.json: {e}")
    
    # Save predictions_errors.json
    try:
        with open(predictions_errors_path, 'w') as f:
            json.dump(all_predictions_errors, f, indent=2)
        logger.info(f"Predictions and errors saved to {predictions_errors_path}")
        log_result_artifact(str(predictions_errors_path), "predictions_errors.json")
    except Exception as e:
        logger.error(f"Failed to save predictions_errors.json: {e}")
    
    return final_results

def main():
    """Entry point for running evaluation from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = evaluate_models()
        logger.info("Evaluation completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        log_error_summary(e)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
