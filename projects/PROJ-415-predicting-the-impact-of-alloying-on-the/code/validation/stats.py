import os
import json
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

from config import DATA_DIR, MODELS_DIR, REPORTS_DIR
from utils.logging import get_logger, log_error_traceback, log_info, log_warning

logger = get_logger(__name__)

# Constants for statistical validation
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_CONFIDENCE_LEVEL = 0.95
SIGNIFICANCE_THRESHOLD = 0.05
MIN_SAMPLES_FOR_BOOTSTRAP = 10

def load_linear_model_coefficients() -> Dict[str, float]:
    """Load Linear Regression coefficients and p-value from saved artifact."""
    coef_path = MODELS_DIR / "linear_coef.json"
    if not coef_path.exists():
        raise FileNotFoundError(f"Linear coefficients file not found: {coef_path}")
    
    with open(coef_path, 'r') as f:
        return json.load(f)

def load_curated_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load curated data and prepare features/target for validation.
    Returns X (features) and y (target).
    """
    curated_path = DATA_DIR / "curated" / "filtered.csv"
    if not curated_path.exists():
        raise FileNotFoundError(f"Curated data not found: {curated_path}")
    
    import pandas as pd
    df = pd.read_csv(curated_path)
    
    # Ensure we have the necessary columns
    if 'size_mismatch' not in df.columns or 'activation_energy' not in df.columns:
        raise ValueError("Curated data missing required columns: size_mismatch, activation_energy")
    
    X = df[['size_mismatch']].values
    y = df['activation_energy'].values
    
    return X, y

def compute_bootstrap_ci(coef: float, X: np.ndarray, y: np.ndarray, 
                         n_resamples: int = BOOTSTRAP_RESAMPLES, 
                         confidence_level: float = BOOTSTRAP_CONFIDENCE_LEVEL) -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval for a coefficient.
    
    Args:
        coef: Original coefficient estimate
        X: Feature matrix
        y: Target vector
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level (e.g., 0.95 for 95% CI)
        
    Returns:
        Tuple of (ci_lower, ci_upper)
    """
    rng = np.random.default_rng(42)  # Fixed seed for reproducibility
    n_samples = len(y)
    bootstrap_coefs = []
    
    for _ in range(n_resamples):
        # Resample with replacement
        indices = rng.choice(n_samples, size=n_samples, replace=True)
        X_resample = X[indices]
        y_resample = y[indices]
        
        # Fit model on resample
        model = LinearRegression()
        model.fit(X_resample, y_resample)
        bootstrap_coefs.append(model.coef_[0])
    
    bootstrap_coefs = np.array(bootstrap_coefs)
    alpha = 1 - confidence_level
    ci_lower = np.percentile(bootstrap_coefs, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_coefs, 100 * (1 - alpha / 2))
    
    return ci_lower, ci_upper

def verify_p_value_significance(p_value: float, threshold: float = SIGNIFICANCE_THRESHOLD) -> bool:
    """Verify if p-value is below significance threshold."""
    return p_value < threshold

def calculate_effect_size(coef: float, X: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate effect size (Cohen's d-like metric for regression).
    Uses the coefficient normalized by the standard deviation of the target.
    """
    std_y = np.std(y)
    if std_y == 0:
        return 0.0
    return abs(coef) / std_y

def calculate_statistical_power(effect_size: float, n_samples: int, 
                                alpha: float = SIGNIFICANCE_THRESHOLD) -> float:
    """
    Calculate statistical power for a given effect size and sample size.
    Uses a simplified approximation for linear regression power.
    """
    # Simplified power calculation using normal approximation
    # Power = P(Z > z_alpha - effect_size * sqrt(n))
    from scipy import stats
    
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    non_central = effect_size * np.sqrt(n_samples)
    power = 1 - stats.norm.cdf(z_alpha - non_central) + stats.norm.cdf(-z_alpha - non_central)
    
    return float(power)

def run_power_analysis(coef: float, X: np.ndarray, y: np.ndarray, 
                       alpha: float = SIGNIFICANCE_THRESHOLD) -> Dict[str, float]:
    """
    Run power analysis for the linear regression coefficient.
    
    Returns:
        Dictionary with 'power' and 'effect_size'
    """
    effect_size = calculate_effect_size(coef, X, y)
    power = calculate_statistical_power(effect_size, len(y), alpha)
    
    return {
        'power': power,
        'effect_size': effect_size
    }

def run_validation_stats() -> Dict[str, Any]:
    """
    Run all statistical validation checks.
    
    Returns:
        Dictionary containing validation results
    """
    try:
        # Load data and coefficients
        coef_data = load_linear_model_coefficients()
        coef = coef_data['coef']
        p_value = coef_data['p_value']
        
        X, y = load_curated_data()
        
        # CRITICAL: Add min_samples check before proceeding
        n_samples = len(y)
        if n_samples < MIN_SAMPLES_FOR_BOOTSTRAP:
            raise SystemExit(
                f"Statistical Error: Insufficient samples for bootstrap CI (N = {n_samples} < {MIN_SAMPLES_FOR_BOOTSTRAP})"
            )
        
        logger.info(f"Proceeding with statistical validation. Sample size: {n_samples}")
        
        # Compute bootstrap confidence interval
        ci_lower, ci_upper = compute_bootstrap_ci(coef, X, y)
        
        # Verify p-value significance
        is_significant = verify_p_value_significance(p_value)
        
        # Verify CI does not cross zero
        ci_non_zero = (ci_lower > 0) or (ci_upper < 0)
        
        # Calculate effect size and power
        power_analysis = run_power_analysis(coef, X, y)
        
        results = {
            'p_value': p_value,
            'is_significant': is_significant,
            'ci_95_lower': ci_lower,
            'ci_95_upper': ci_upper,
            'ci_non_zero_crossing': ci_non_zero,
            'sample_size': n_samples,
            'power_analysis': power_analysis,
            'validation_passed': is_significant and ci_non_zero
        }
        
        logger.info(f"Validation results: {results}")
        return results
        
    except Exception as e:
        log_error_traceback(logger, e)
        raise

def save_validation_results(results: Dict[str, Any]) -> Path:
    """Save validation results to reports directory."""
    report_path = REPORTS_DIR / "validation_report.json"
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation report saved to: {report_path}")
    return report_path

def main():
    """Main entry point for statistical validation."""
    logger.info("Starting statistical validation (T062)")
    
    try:
        results = run_validation_stats()
        report_path = save_validation_results(results)
        
        if not results['validation_passed']:
            logger.warning("Statistical validation did not pass all checks.")
            if not results['is_significant']:
                logger.warning("P-value significance not met.")
            if not results['ci_non_zero_crossing']:
                logger.warning("Confidence interval crosses zero.")
        
        logger.info("Statistical validation completed successfully.")
        return results
        
    except SystemExit as e:
        logger.error(f"Validation failed with system exit: {e}")
        raise
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        raise

if __name__ == "__main__":
    main()