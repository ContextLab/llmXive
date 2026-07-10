import os
import sys
import json
import logging
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Any, Optional

from config import CONFIG
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def load_models(models_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Load trained models from disk."""
    if models_dir is None:
        models_dir = CONFIG.MODELS_DIR
    
    models = {}
    if not models_dir.exists():
        logger.warning(f"Models directory {models_dir} does not exist")
        return models
    
    for file_path in models_dir.glob("*.pkl"):
        model_name = file_path.stem
        with open(file_path, 'rb') as f:
            models[model_name] = pickle.load(f)
        logger.info(f"Loaded model: {model_name}")
    
    return models

def load_cv_results(results_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load cross-validation results from disk."""
    if results_path is None:
        results_path = CONFIG.CV_RESULTS_PATH
    
    if not results_path.exists():
        raise FileNotFoundError(f"CV results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def calculate_metrics(cv_results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Calculate mean R² and MAE for each model from CV results."""
    metrics = {}
    for model_name, data in cv_results.items():
        r2_scores = data.get('r2_scores', [])
        mae_scores = data.get('mae_scores', [])
        
        if r2_scores and mae_scores:
            metrics[model_name] = {
                'mean_r2': float(np.mean(r2_scores)),
                'std_r2': float(np.std(r2_scores)),
                'mean_mae': float(np.mean(mae_scores)),
                'std_mae': float(np.std(mae_scores))
            }
            logger.info(f"Model {model_name}: R²={metrics[model_name]['mean_r2']:.4f}, MAE={metrics[model_name]['mean_mae']:.4f}")
        else:
            logger.warning(f"Missing scores for model {model_name}")
    
    return metrics

def perform_paired_ttest(cv_results: Dict[str, Any], model_a: str, model_b: str) -> Dict[str, float]:
    """Perform paired t-test between two models' fold-wise errors."""
    if model_a not in cv_results or model_b not in cv_results:
        raise ValueError(f"Models {model_a} or {model_b} not found in CV results")
    
    mae_a = np.array(cv_results[model_a].get('mae_scores', []))
    mae_b = np.array(cv_results[model_b].get('mae_scores', []))
    
    if len(mae_a) == 0 or len(mae_b) == 0:
        raise ValueError("One or both models have no MAE scores for t-test")
    
    if len(mae_a) != len(mae_b):
        raise ValueError("Models have different number of folds for t-test")
    
    t_stat, p_value = stats.ttest_rel(mae_a, mae_b)
    
    logger.info(f"Paired t-test: {model_a} vs {model_b}, t={t_stat:.4f}, p={p_value:.6f}")
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'n_folds': int(len(mae_a)),
        'mean_mae_a': float(np.mean(mae_a)),
        'mean_mae_b': float(np.mean(mae_b)),
        'diff_mean_mae': float(np.mean(mae_a) - np.mean(mae_b))
    }

def calculate_statistical_power(cv_results: Dict[str, Any], model_a: str, model_b: str, alpha: float = 0.05) -> Dict[str, float]:
    """
    Calculate statistical power (1 - beta) based on the t-test effect size.
    
    Uses the effect size (Cohen's d) from the paired differences and the
    number of folds to estimate power for the observed effect.
    
    Args:
        cv_results: Dictionary containing CV results for both models
        model_a: Name of the first model (baseline)
        model_b: Name of the second model (enhanced)
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with power, effect size, and related statistics
    """
    if model_a not in cv_results or model_b not in cv_results:
        raise ValueError(f"Models {model_a} or {model_b} not found in CV results")
    
    mae_a = np.array(cv_results[model_a].get('mae_scores', []))
    mae_b = np.array(cv_results[model_b].get('mae_scores', []))
    
    if len(mae_a) == 0 or len(mae_b) == 0:
        raise ValueError("One or both models have no MAE scores for power analysis")
    
    if len(mae_a) != len(mae_b):
        raise ValueError("Models have different number of folds for power analysis")
    
    # Calculate paired differences
    differences = mae_a - mae_b
    n = len(differences)
    
    # Calculate effect size (Cohen's d for paired samples)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    
    if std_diff == 0:
        logger.warning("Standard deviation of differences is zero, power cannot be calculated")
        return {
            'power': 0.0,
            'effect_size': 0.0,
            'n_folds': n,
            'mean_difference': float(mean_diff),
            'std_difference': 0.0,
            'is_adequate_power': False,
            'message': "Zero variance in differences"
        }
    
    # Cohen's d for paired samples
    effect_size = mean_diff / std_diff
    
    # Calculate power using t-test power formula
    # Degrees of freedom
    df = n - 1
    
    # Non-centrality parameter
    ncp = abs(effect_size) * np.sqrt(n)
    
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power = P(|T| > t_crit | non-central t-distribution)
    # Using the non-central t-distribution
    power_low = stats.nct.cdf(t_crit, df, ncp)
    power_high = stats.nct.sf(-t_crit, df, ncp)
    power = power_low + power_high
    
    # Ensure power is between 0 and 1
    power = max(0.0, min(1.0, power))
    
    is_adequate = power >= 0.8
    
    result = {
        'power': float(power),
        'effect_size': float(effect_size),
        'n_folds': n,
        'mean_difference': float(mean_diff),
        'std_difference': float(std_diff),
        'is_adequate_power': is_adequate,
        'alpha': alpha,
        'message': "Power is adequate" if is_adequate else f"Power ({power:.2f}) is below threshold (0.8)"
    }
    
    logger.info(f"Statistical Power Analysis: Power={power:.4f}, Effect Size={effect_size:.4f}, Adequate={is_adequate}")
    
    return result

def calculate_shear_yield_correlation(data_path: Optional[Path] = None) -> Dict[str, float]:
    """Calculate Pearson correlation between Shear Modulus and Yield Strength."""
    if data_path is None:
        data_path = CONFIG.MERGED_DATASET_PATH
    
    if not data_path.exists():
        raise FileNotFoundError(f"Merged dataset not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    required_cols = ['shear_modulus_GPa', 'yield_strength_MPa']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Drop rows with NaN in required columns
    valid_data = df.dropna(subset=required_cols)
    
    if len(valid_data) < 2:
        raise ValueError("Insufficient data points for correlation calculation")
    
    shear = valid_data['shear_modulus_GPa'].values
    yield_strength = valid_data['yield_strength_MPa'].values
    
    corr, p_value = stats.pearsonr(shear, yield_strength)
    
    logger.info(f"Pearson correlation (Shear vs Yield): r={corr:.4f}, p={p_value:.6f}")
    
    return {
        'pearson_correlation': float(corr),
        'p_value': float(p_value),
        'n_samples': int(len(valid_data)),
        'description': 'Pearson correlation between Shear Modulus (GPa) and Yield Strength (MPa)'
    }

def run_evaluation(models_dir: Optional[Path] = None, results_path: Optional[Path] = None) -> Dict[str, Any]:
    """Run full evaluation pipeline including metrics, t-test, power, and correlation."""
    if models_dir is None:
        models_dir = CONFIG.MODELS_DIR
    if results_path is None:
        results_path = CONFIG.CV_RESULTS_PATH
    
    logger.info("Starting evaluation pipeline")
    
    # Load CV results
    cv_results = load_cv_results(results_path)
    
    # Calculate metrics
    metrics = calculate_metrics(cv_results)
    
    # Identify models for comparison (assuming baseline and dft-enhanced)
    model_names = list(cv_results.keys())
    if len(model_names) < 2:
        logger.warning("Less than 2 models found, skipping t-test and power analysis")
        ttest_result = None
        power_result = None
    else:
        # Compare first two models (baseline vs enhanced)
        model_a, model_b = model_names[0], model_names[1]
        
        # Perform paired t-test
        ttest_result = perform_paired_ttest(cv_results, model_a, model_b)
        
        # Calculate statistical power
        power_result = calculate_statistical_power(cv_results, model_a, model_b)
    
    # Calculate shear-yield correlation
    try:
        correlation_result = calculate_shear_yield_correlation()
    except Exception as e:
        logger.warning(f"Could not calculate correlation: {e}")
        correlation_result = None
    
    evaluation_result = {
        'metrics': metrics,
        'paired_t_test': ttest_result,
        'statistical_power': power_result,
        'shear_yield_correlation': correlation_result,
        'timestamp': str(pd.Timestamp.now())
    }
    
    logger.info("Evaluation pipeline completed")
    return evaluation_result

def save_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """Save evaluation results to JSON file."""
    if output_path is None:
        output_path = CONFIG.OUTPUT_RESULTS_PATH
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for evaluation script."""
    try:
        # Run evaluation
        results = run_evaluation()
        
        # Save results
        save_results(results)
        
        # Print summary
        print("\n=== Evaluation Summary ===")
        print(f"Models evaluated: {list(results['metrics'].keys())}")
        
        if results['statistical_power']:
            power = results['statistical_power']['power']
            adequate = results['statistical_power']['is_adequate_power']
            print(f"Statistical Power: {power:.4f} ({'Adequate' if adequate else 'Inadequate'})")
            if not adequate:
                print(f"  -> WARNING: Power ({power:.2f}) is below threshold (0.8)")
        
        if results['shear_yield_correlation']:
            corr = results['shear_yield_correlation']['pearson_correlation']
            print(f"Shear-Yield Correlation: {corr:.4f}")
        
        print(f"\nDetailed results saved to: {CONFIG.OUTPUT_RESULTS_PATH}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == '__main__':
    main()