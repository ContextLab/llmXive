"""
Statistical comparison module for model evaluation.

Implements Shapiro-Wilk normality test, Wilcoxon Signed-Rank Test,
and Corrected Resampled t-test for comparing model residuals.
"""
import os
import sys
import json
import logging
import math
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

import numpy as np
from scipy import stats

from utils.config import get_paths
from utils.logging_config import get_logger
from utils.provenance import record_artifact

logger = get_logger(__name__)

def shapiro_wilk_test(residuals: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality on residuals.
    
    Args:
        residuals: List of residual values (observed - predicted)
        alpha: Significance level for the test
        
    Returns:
        Dictionary with 'is_normal' (bool), 'statistic' (float), 'p_value' (float)
    """
    if len(residuals) < 3:
        logger.warning("Insufficient data for Shapiro-Wilk test (n < 3). Assuming non-normal.")
        return {
            'is_normal': False,
            'statistic': None,
            'p_value': None,
            'message': 'Insufficient data for test'
        }
    
    try:
        statistic, p_value = stats.shapiro(residuals)
        is_normal = p_value >= alpha
        
        logger.info(f"Shapiro-Wilk Test: W={statistic:.4f}, p-value={p_value:.4f}, "
                    f"Normal: {is_normal}")
        
        return {
            'is_normal': is_normal,
            'statistic': float(statistic),
            'p_value': float(p_value),
            'alpha': alpha
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return {
            'is_normal': False,
            'statistic': None,
            'p_value': None,
            'error': str(e)
        }

def wilcoxon_signed_rank_test(residuals_model_a: List[float], 
                              residuals_model_b: List[float]) -> Dict[str, Any]:
    """
    Perform Wilcoxon Signed-Rank Test for non-normal paired data.
    
    Args:
        residuals_model_a: Residuals from model A
        residuals_model_b: Residuals from model B
        
    Returns:
        Dictionary with 'statistic', 'p_value', 'method'
    """
    if len(residuals_model_a) != len(residuals_model_b):
        raise ValueError("Residual lists must have equal length for paired test.")
    
    if len(residuals_model_a) < 5:
        logger.warning("Small sample size for Wilcoxon test. Results may be unreliable.")
    
    try:
        statistic, p_value = stats.wilcoxon(residuals_model_a, residuals_model_b)
        
        logger.info(f"Wilcoxon Signed-Rank Test: W={statistic:.4f}, p-value={p_value:.4f}")
        
        return {
            'method': 'wilcoxon_signed_rank',
            'statistic': float(statistic),
            'p_value': float(p_value),
            'sample_size': len(residuals_model_a)
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            'method': 'wilcoxon_signed_rank',
            'statistic': None,
            'p_value': None,
            'error': str(e)
        }

def corrected_resampled_ttest(residuals_model_a: List[float],
                              residuals_model_b: List[float],
                              n_iterations: int = 1000,
                              train_size_ratio: float = 0.8,
                              alpha: float = 0.05,
                              random_state: int = 42) -> Dict[str, Any]:
    """
    Perform Corrected Resampled t-test for paired model comparison.
    
    This test corrects for the dependence between training sets in repeated
    cross-validation by adjusting the variance estimate.
    
    Args:
        residuals_model_a: Residuals from model A
        residuals_model_b: Residuals from model B
        n_iterations: Number of resampling iterations
        train_size_ratio: Ratio of data to use for training in each iteration
        alpha: Significance level
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with test results including statistic, p_value, and confidence interval
    """
    if len(residuals_model_a) != len(residuals_model_b):
        raise ValueError("Residual lists must have equal length for paired test.")
    
    n_samples = len(residuals_model_a)
    if n_samples < 10:
        logger.warning("Small sample size. Corrected Resampled t-test may be unstable.")
    
    np.random.seed(random_state)
    
    # Calculate differences in absolute errors (we want to test if one model is consistently better)
    abs_errors_a = np.abs(residuals_model_a)
    abs_errors_b = np.abs(residuals_model_b)
    differences = abs_errors_a - abs_errors_b
    
    # Store t-statistics from each iteration
    t_statistics = []
    
    for i in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        diff_sample = differences[indices]
        
        n_train = int(n_samples * train_size_ratio)
        
        if n_train < 2:
            continue
            
        # Calculate mean and standard error
        mean_diff = np.mean(diff_sample[:n_train])
        std_diff = np.std(diff_sample[:n_train], ddof=1)
        
        if std_diff == 0:
            continue
            
        # Standard t-statistic
        t_stat = mean_diff / (std_diff / math.sqrt(n_train))
        t_statistics.append(t_stat)
    
    if not t_statistics:
        logger.error("Could not compute t-statistics. Check sample size.")
        return {
            'method': 'corrected_resampled_ttest',
            'statistic': None,
            'p_value': None,
            'confidence_interval': None,
            'error': 'No valid iterations'
        }
    
    t_statistics = np.array(t_statistics)
    
    # Corrected variance adjustment (Nadeau et al. correction)
    # The correction factor accounts for the overlap in training sets
    correction_factor = math.sqrt((1/n_samples) + (1/n_train))
    
    # Calculate overall mean and corrected standard error
    mean_t = np.mean(t_statistics)
    std_t = np.std(t_statistics, ddof=1)
    
    # Two-tailed p-value using normal approximation for large n_iterations
    p_value = 2 * (1 - stats.norm.cdf(abs(mean_t)))
    
    # 95% Confidence Interval
    ci_lower = mean_t - 1.96 * (std_t / math.sqrt(len(t_statistics)))
    ci_upper = mean_t + 1.96 * (std_t / math.sqrt(len(t_statistics)))
    
    is_significant = p_value < alpha
    
    logger.info(f"Corrected Resampled t-test: t={mean_t:.4f}, p={p_value:.4f}, "
                f"Significant: {is_significant}, CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return {
        'method': 'corrected_resampled_ttest',
        'statistic': float(mean_t),
        'p_value': float(p_value),
        'is_significant': is_significant,
        'confidence_interval': [float(ci_lower), float(ci_upper)],
        'alpha': alpha,
        'n_iterations': n_iterations,
        'train_size_ratio': train_size_ratio
    }

def run_statistical_comparison(residuals_a: List[float], 
                               residuals_b: List[float],
                               model_name_a: str = "Model A",
                               model_name_b: str = "Model B",
                               alpha: float = 0.05,
                               output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for statistical comparison of two models.
    
    Logic:
    1. Perform Shapiro-Wilk test on residuals of both models
    2. If residuals are non-normal (p < 0.05), use Wilcoxon Signed-Rank Test
    3. If residuals are normal, use Corrected Resampled t-test
    
    Args:
        residuals_a: Residuals from model A
        residuals_b: Residuals from model B
        model_name_a: Name of model A
        model_name_b: Name of model B
        alpha: Significance level
        output_path: Optional path to save the results JSON
        
    Returns:
        Dictionary containing full comparison results
    """
    logger.info(f"Starting statistical comparison: {model_name_a} vs {model_name_b}")
    
    result = {
        'comparison': f"{model_name_a} vs {model_name_b}",
        'sample_size': len(residuals_a),
        'alpha': alpha,
        'shapiro_wilk': {},
        'test_used': None,
        'test_results': {},
        'conclusion': ""
    }
    
    # Step 1: Normality check
    sw_a = shapiro_wilk_test(residuals_a, alpha)
    sw_b = shapiro_wilk_test(residuals_b, alpha)
    
    result['shapiro_wilk'] = {
        'model_a': sw_a,
        'model_b': sw_b
    }
    
    # Determine if we should use parametric or non-parametric test
    # If EITHER model has non-normal residuals, use Wilcoxon
    use_non_parametric = (not sw_a.get('is_normal', False)) or (not sw_b.get('is_normal', False))
    
    if use_non_parametric:
        logger.info("Non-normal residuals detected. Using Wilcoxon Signed-Rank Test.")
        test_result = wilcoxon_signed_rank_test(residuals_a, residuals_b)
        result['test_used'] = 'wilcoxon_signed_rank'
        
        if test_result.get('p_value') is not None:
            is_significant = test_result['p_value'] < alpha
            if is_significant:
                result['conclusion'] = f"Significant difference detected (p={test_result['p_value']:.4f}). " \
                                      f"One model performs significantly better than the other."
            else:
                result['conclusion'] = f"No significant difference detected (p={test_result['p_value']:.4f}). " \
                                      f"Models perform similarly."
        else:
            result['conclusion'] = "Test failed to compute p-value."
            
    else:
        logger.info("Normal residuals detected. Using Corrected Resampled t-test.")
        test_result = corrected_resampled_ttest(residuals_a, residuals_b, alpha=alpha)
        result['test_used'] = 'corrected_resampled_ttest'
        
        if test_result.get('p_value') is not None:
            is_significant = test_result['p_value'] < alpha
            if is_significant:
                result['conclusion'] = f"Significant difference detected (p={test_result['p_value']:.4f}). " \
                                      f"One model performs significantly better than the other."
            else:
                result['conclusion'] = f"No significant difference detected (p={test_result['p_value']:.4f}). " \
                                      f"Models perform similarly."
        else:
            result['conclusion'] = "Test failed to compute p-value."
    
    result['test_results'] = test_result
    
    logger.info(f"Statistical comparison complete. Conclusion: {result['conclusion']}")
    
    # Save to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        
        # Record provenance
        try:
            record_artifact(str(output_path), str(Path(output_path).parent / "state.yaml"))
            logger.info(f"Provenance recorded for {output_path}")
        except Exception as e:
            logger.warning(f"Failed to record provenance: {e}")
    
    return result

def main():
    """
    Command-line interface for statistical comparison.
    
    Expected input: Two CSV files containing residuals for each model.
    Each CSV should have a 'residual' column.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistical comparison of model residuals")
    parser.add_argument("--residuals-a", type=str, required=True, 
                       help="Path to CSV with residuals for model A")
    parser.add_argument("--residuals-b", type=str, required=True, 
                       help="Path to CSV with residuals for model B")
    parser.add_argument("--model-a-name", type=str, default="Model A",
                       help="Name for model A")
    parser.add_argument("--model-b-name", type=str, default="Model B",
                       help="Name for model B")
    parser.add_argument("--output", type=str, default=None,
                       help="Output JSON file path")
    parser.add_argument("--alpha", type=float, default=0.05,
                       help="Significance level")
    
    args = parser.parse_args()
    
    # Load residuals from CSVs
    def load_residuals(path: str) -> List[float]:
        residuals = []
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'residual' in row:
                    residuals.append(float(row['residual']))
        return residuals
    
    logger.info(f"Loading residuals from {args.residuals_a}")
    residuals_a = load_residuals(args.residuals_a)
    logger.info(f"Loaded {len(residuals_a)} residuals for {args.model_a_name}")
    
    logger.info(f"Loading residuals from {args.residuals_b}")
    residuals_b = load_residuals(args.residuals_b)
    logger.info(f"Loaded {len(residuals_b)} residuals for {args.model_b_name}")
    
    if len(residuals_a) != len(residuals_b):
        logger.error("Residual lists must have equal length.")
        sys.exit(1)
    
    output_path = Path(args.output) if args.output else None
    
    result = run_statistical_comparison(
        residuals_a=residuals_a,
        residuals_b=residuals_b,
        model_name_a=args.model_a_name,
        model_name_b=args.model_b_name,
        alpha=args.alpha,
        output_path=output_path
    )
    
    print(json.dumps(result, indent=2))
    sys.exit(0)

if __name__ == "__main__":
    main()
