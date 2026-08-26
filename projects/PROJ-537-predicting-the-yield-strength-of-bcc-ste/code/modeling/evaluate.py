import os
import sys
import json
import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# Import from project config
try:
    from config import CONFIG, ERR_INSUFFICIENT_DATA
except ImportError:
    # Fallback for execution context where path might differ
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import CONFIG, ERR_INSUFFICIENT_DATA

from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def load_models(models_dir: Path) -> dict:
    """Load trained models from the models directory."""
    models = {}
    model_files = {
        'baseline': 'baseline_model.pkl',
        'dft_enhanced': 'dft_enhanced_model.pkl'
    }
    
    for name, filename in model_files.items():
        path = models_dir / filename
        if path.exists():
            with open(path, 'rb') as f:
                models[name] = pickle.load(f)
            logger.info(f"Loaded model: {name}")
        else:
            logger.warning(f"Model file not found: {path}")
    
    return models

def load_cv_results(results_dir: Path) -> pd.DataFrame:
    """Load cross-validation results."""
    results_path = results_dir / 'cv_results.parquet'
    if results_path.exists():
        return pd.read_parquet(results_path)
    # Fallback to CSV if parquet not available
    results_path = results_dir / 'cv_results.csv'
    if results_path.exists():
        return pd.read_csv(results_path)
    raise FileNotFoundError(f"CV results not found in {results_dir}")

def calculate_metrics(cv_results: pd.DataFrame) -> dict:
    """Calculate aggregate metrics from CV results."""
    metrics = {}
    for model_name in cv_results['model'].unique():
        model_data = cv_results[cv_results['model'] == model_name]
        metrics[model_name] = {
            'r2_mean': model_data['r2'].mean(),
            'r2_std': model_data['r2'].std(),
            'mae_mean': model_data['mae'].mean(),
            'mae_std': model_data['mae'].std()
        }
    return metrics

def perform_paired_ttest(cv_results: pd.DataFrame) -> dict:
    """Perform paired t-test between baseline and DFT-enhanced models."""
    baseline_data = cv_results[cv_results['model'] == 'baseline'].sort_values('fold')
    dft_data = cv_results[cv_results['model'] == 'dft_enhanced'].sort_values('fold')
    
    if len(baseline_data) != len(dft_data):
        logger.warning("Fold counts mismatch, aligning by fold index")
        common_folds = min(len(baseline_data), len(dft_data))
        baseline_data = baseline_data.iloc[:common_folds]
        dft_data = dft_data.iloc[:common_folds]
    
    baseline_errors = baseline_data['mae'].values
    dft_errors = dft_data['mae'].values
    
    t_stat, p_value = stats.ttest_rel(baseline_errors, dft_errors)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'baseline_mae_mean': float(np.mean(baseline_errors)),
        'dft_mae_mean': float(np.mean(dft_errors))
    }

def calculate_statistical_power(cv_results: pd.DataFrame) -> dict:
    """Calculate statistical power based on effect size."""
    baseline_data = cv_results[cv_results['model'] == 'baseline'].sort_values('fold')
    dft_data = cv_results[cv_results['model'] == 'dft_enhanced'].sort_values('fold')
    
    common_folds = min(len(baseline_data), len(dft_data))
    baseline_errors = baseline_data['mae'].iloc[:common_folds].values
    dft_errors = dft_data['mae'].iloc[:common_folds].values
    
    # Calculate effect size (Cohen's d for paired samples)
    mean_diff = np.mean(baseline_errors - dft_errors)
    std_diff = np.std(baseline_errors - dft_errors, ddof=1)
    
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff
    
    n = len(baseline_errors)
    
    # Approximate power calculation using normal distribution
    # For a two-tailed test at alpha=0.05
    alpha = 0.05
    z_alpha = 1.96
    
    # Power = P(Z > z_alpha - |d| * sqrt(n))
    # Simplified approximation
    non_central = abs(cohens_d) * np.sqrt(n)
    power = 1.0 - stats.norm.cdf(z_alpha - non_central) + stats.norm.cdf(-z_alpha - non_central)
    
    return {
        'effect_size_cohens_d': float(cohens_d),
        'sample_size': n,
        'statistical_power': float(power),
        'is_power_sufficient': bool(power >= 0.8)
    }

def calculate_shear_yield_correlation(merged_data_path: Path) -> dict:
    """
    Calculate Pearson correlation between Shear Modulus and Yield Strength.
    This implements SC-001 and FR-005.
    
    Args:
        merged_data_path: Path to data/intermediate/merged.csv
        
    Returns:
        Dictionary with correlation coefficient, p-value, and sample size.
    """
    if not merged_data_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_data_path}")
    
    logger.info(f"Loading merged dataset from {merged_data_path}")
    df = pd.read_csv(merged_data_path)
    
    # Identify relevant columns (case-insensitive check)
    cols_lower = {col.lower(): col for col in df.columns}
    
    shear_col = None
    yield_col = None
    
    # Look for shear modulus
    for key in ['shear_modulus_gpa', 'shear_modulus', 'g_gpa', 'g']:
        if key in cols_lower:
            shear_col = cols_lower[key]
            break
    
    # Look for yield strength
    for key in ['yield_strength_mpa', 'yield_strength', 'ys_mpa', 'ys']:
        if key in cols_lower:
            yield_col = cols_lower[key]
            break
    
    if not shear_col:
        raise ValueError("Shear modulus column not found in merged dataset")
    if not yield_col:
        raise ValueError("Yield strength column not found in merged dataset")
    
    # Drop rows with NaN in either column
    valid_data = df[[shear_col, yield_col]].dropna()
    
    if len(valid_data) < 3:
        raise ValueError(f"Insufficient valid data points for correlation (found {len(valid_data)})")
    
    shear_values = valid_data[shear_col].values
    yield_values = valid_data[yield_col].values
    
    # Calculate Pearson correlation
    corr_matrix, p_value = stats.pearsonr(shear_values, yield_values)
    
    logger.info(f"Pearson correlation (Shear Modulus vs Yield Strength): {corr_matrix:.4f} (p={p_value:.4e})")
    
    return {
        'pearson_correlation': float(corr_matrix),
        'p_value': float(p_value),
        'sample_size': int(len(valid_data)),
        'shear_column': shear_col,
        'yield_column': yield_col,
        'is_significant': bool(p_value < 0.05)
    }

def run_evaluation(merged_data_path: Path, cv_results_path: Path, models_dir: Path) -> dict:
    """Run full evaluation pipeline."""
    logger.info("Starting evaluation pipeline")
    
    # Load CV results
    cv_results = load_cv_results(cv_results_path)
    
    # Calculate metrics
    metrics = calculate_metrics(cv_results)
    
    # Perform paired t-test
    ttest_results = perform_paired_ttest(cv_results)
    
    # Calculate statistical power
    power_results = calculate_statistical_power(cv_results)
    
    # Calculate shear-yield correlation (SC-001)
    correlation_results = calculate_shear_yield_correlation(merged_data_path)
    
    results = {
        'model_metrics': metrics,
        'statistical_test': ttest_results,
        'power_analysis': power_results,
        'correlation_analysis': correlation_results,
        'sc_001_satisfied': correlation_results['is_significant'],
        'sc_003_satisfied': ttest_results['p_value'] < 0.05,
        'sc_008_satisfied': power_results['is_power_sufficient']
    }
    
    logger.info("Evaluation pipeline completed")
    return results

def save_results(results: dict, output_path: Path):
    """Save results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for evaluation."""
    # Paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    merged_path = project_root / CONFIG.INTERMEDIATE_DIR / 'merged.csv'
    results_dir = project_root / CONFIG.RESULTS_DIR
    models_dir = project_root / CONFIG.MODELS_DIR
    
    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / 'output.json'
    
    try:
        results = run_evaluation(merged_path, results_dir, models_dir)
        save_results(results, output_path)
        print(f"Evaluation complete. Results written to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())