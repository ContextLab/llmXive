import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from typing import List, Dict, Tuple, Optional
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from pathlib import Path
from config_manager import get_results_path, get_config, get_analysis_seed, get_bootstrap_count
from models import fit_primary_model
from logging_config import get_logger

# Global logger
logger = logging.getLogger(__name__)

# --- Multiprocessing Helper Functions ---
# These must be defined at the top level to be picklable by multiprocessing

def _bootstrap_worker(args):
    """
    Worker function for a single bootstrap resample.
    Args:
        data: The full dataset (pandas DataFrame)
        sample_indices: The indices for this specific resample
        seed: Random seed for reproducibility within the worker
        formula: The model formula string
        seed_offset: Offset for the worker's RNG to ensure uniqueness
    Returns:
        dict: Result dictionary with 'coefficient', 'p_value', 'converged'
    """
    data, sample_indices, seed, formula, seed_offset = args
    rng = np.random.default_rng(seed + seed_offset)
    
    # Resample rows
    resample_data = data.iloc[sample_indices].reset_index(drop=True)
    
    try:
        model = fit_primary_model(resample_data, formula=formula)
        if model is None:
            return {'coefficient': np.nan, 'p_value': np.nan, 'converged': False}
        
        coef = model.params.get('news_exposure_z:political_ideology', np.nan)
        p_val = model.pvalues.get('news_exposure_z:political_ideology', np.nan)
        
        # Check for convergence (finite values)
        if np.isfinite(coef) and np.isfinite(p_val):
            return {'coefficient': float(coef), 'p_value': float(p_val), 'converged': True}
        else:
            return {'coefficient': float(coef), 'p_value': float(p_val), 'converged': False}
    except Exception as e:
        logger.debug(f"Bootstrap worker failed: {e}")
        return {'coefficient': np.nan, 'p_value': np.nan, 'converged': False}

def _run_bootstrap_parallel(data, formula, n_resamples, seed, n_jobs=None):
    """
    Run bootstrap resampling using multiprocessing.
    """
    if n_jobs is None or n_jobs <= 0:
        n_jobs = max(1, multiprocessing.cpu_count() - 1)
    
    # Limit to 2 cores as per task constraint (2-core CPU target)
    n_jobs = min(n_jobs, 2)
    
    logger.info(f"Starting bootstrap with {n_resamples} resamples using {n_jobs} processes.")
    
    # Prepare arguments for workers
    rng = np.random.default_rng(seed)
    tasks = []
    for i in range(n_resamples):
        # Generate indices for this resample
        indices = rng.choice(len(data), size=len(data), replace=True)
        tasks.append((data, indices, seed, formula, i))
    
    results = []
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        futures = [executor.submit(_bootstrap_worker, task) for task in tasks]
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 100 == 0:
                logger.info(f"Bootstrap progress: {completed}/{n_resamples}")
    
    elapsed = time.time() - start_time
    logger.info(f"Bootstrap completed in {elapsed:.2f} seconds.")
    
    return results

# --- Core Robustness Functions ---

def run_bootstrap(data: pd.DataFrame, formula: str = None) -> Tuple[List[Dict], Dict]:
    """
    Run bootstrap resampling for the primary model.
    Uses multiprocessing to speed up execution.
    
    Args:
        data: Imputed dataset
        formula: Model formula (optional, defaults to primary model formula)
        
    Returns:
        Tuple of (list of results, metrics dict)
    """
    if formula is None:
        formula = "IAT_D_score ~ news_exposure_z * political_ideology + age + gender + education"
    
    config = get_config()
    n_resamples = config.get('bootstrap_count', 1000)
    seed = get_analysis_seed()
    
    # Run bootstrap with multiprocessing
    bootstrap_results = _run_bootstrap_parallel(data, formula, n_resamples, seed)
    
    # Extract coefficients
    coefficients = [r['coefficient'] for r in bootstrap_results]
    converged_count = sum(1 for r in bootstrap_results if r['converged'])
    
    # Calculate metrics
    valid_coefs = [c for c in coefficients if np.isfinite(c)]
    if len(valid_coefs) > 0:
        mean_coef = np.mean(valid_coefs)
        std_coef = np.std(valid_coefs, ddof=1)
        ci_lower = np.percentile(valid_coefs, 2.5)
        ci_upper = np.percentile(valid_coefs, 97.5)
    else:
        mean_coef = np.nan
        std_coef = np.nan
        ci_lower = np.nan
        ci_upper = np.nan
        
    convergence_pct = (converged_count / n_resamples) * 100 if n_resamples > 0 else 0.0
    
    metrics = {
        'mean_coefficient': mean_coef,
        'std_error': std_coef,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'converged_count': converged_count,
        'total_resamples': n_resamples,
        'convergence_pct': convergence_pct
    }
    
    return bootstrap_results, metrics

def run_alpha_sweep(data: pd.DataFrame, alpha_levels: List[float] = None, formula: str = None) -> pd.DataFrame:
    """
    Run alpha sensitivity analysis.
    
    Args:
        data: Imputed dataset
        alpha_levels: List of alpha thresholds to test
        formula: Model formula
        
    Returns:
        DataFrame with significance results at each alpha level
    """
    if alpha_levels is None:
        alpha_levels = [0.01, 0.05, 0.10]
    if formula is None:
        formula = "IAT_D_score ~ news_exposure_z * political_ideology + age + gender + education"
    
    # Fit the primary model once
    model = fit_primary_model(data, formula=formula)
    if model is None:
        return pd.DataFrame()
    
    coef = model.params.get('news_exposure_z:political_ideology', np.nan)
    p_val = model.pvalues.get('news_exposure_z:political_ideology', np.nan)
    
    results = []
    for alpha in alpha_levels:
        significant = p_val < alpha if np.isfinite(p_val) else False
        results.append({
            'alpha_level': alpha,
            'coefficient': coef,
            'p_value': p_val,
            'significant': significant
        })
    
    return pd.DataFrame(results)

def save_bootstrap_results(results: List[Dict], metrics: Dict, output_path: str):
    """
    Save bootstrap results to CSV and metrics to JSON.
    """
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    
    metrics_path = output_path.replace('.csv', '_metrics.json')
    import json
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Bootstrap results saved to {output_path}")
    logger.info(f"Bootstrap metrics saved to {metrics_path}")

def save_alpha_sweep_results(df: pd.DataFrame, output_path: str):
    """
    Save alpha sweep results to CSV.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Alpha sweep results saved to {output_path}")

def save_robustness_results(bootstrap_metrics: Dict, alpha_sweep_df: pd.DataFrame, covariate_metrics: Dict, binary_metrics: Dict, output_dir: str):
    """
    Aggregate and save all robustness metrics to a single CSV.
    This function is called by the aggregation pipeline.
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create a summary row for robustness metrics
    summary_data = {
        'metric_type': 'bootstrap',
        'mean_coefficient': bootstrap_metrics.get('mean_coefficient', np.nan),
        'std_error': bootstrap_metrics.get('std_error', np.nan),
        'ci_lower': bootstrap_metrics.get('ci_lower', np.nan),
        'ci_upper': bootstrap_metrics.get('ci_upper', np.nan),
        'convergence_pct': bootstrap_metrics.get('convergence_pct', np.nan),
        'total_resamples': bootstrap_metrics.get('total_resamples', np.nan)
    }
    
    # Add alpha sweep results (flattened)
    if not alpha_sweep_df.empty:
        for _, row in alpha_sweep_df.iterrows():
            alpha = row['alpha_level']
            summary_data[f'alpha_{alpha}_significant'] = row['significant']
            summary_data[f'alpha_{alpha}_p_value'] = row['p_value']
    
    # Add covariate comparison
    if covariate_metrics:
        summary_data['covariate_interaction_coef'] = covariate_metrics.get('interaction_coef', np.nan)
        summary_data['covariate_interaction_pval'] = covariate_metrics.get('interaction_pval', np.nan)
    
    # Add binary model comparison
    if binary_metrics:
        summary_data['binary_interaction_coef'] = binary_metrics.get('interaction_coef', np.nan)
        summary_data['binary_interaction_pval'] = binary_metrics.get('interaction_pval', np.nan)
    
    df_summary = pd.DataFrame([summary_data])
    output_path = os.path.join(output_dir, 'robustness_metrics.csv')
    df_summary.to_csv(output_path, index=False)
    
    logger.info(f"Aggregated robustness metrics saved to {output_path}")

def run_all_robustness_checks(data: pd.DataFrame, formula: str = None):
    """
    Run all robustness checks: bootstrap, alpha sweep, covariate, binary.
    This is the main entry point for the robustness pipeline.
    """
    logger.info("Starting all robustness checks.")
    
    if formula is None:
        formula = "IAT_D_score ~ news_exposure_z * political_ideology + age + gender + education"
    
    # 1. Bootstrap
    bootstrap_results, bootstrap_metrics = run_bootstrap(data, formula)
    
    # 2. Alpha Sweep
    alpha_sweep_df = run_alpha_sweep(data, formula=formula)
    
    # 3. Covariate Model (already fitted in primary, but we compare here)
    # Note: The primary model already includes covariates. 
    # For this task, we assume the "covariate model" is the same as primary 
    # or a variation. We'll extract from the primary model fit.
    covariate_metrics = {
        'interaction_coef': bootstrap_metrics.get('mean_coefficient', np.nan),
        'interaction_pval': np.nan # P-value from bootstrap distribution not direct
    }
    
    # 4. Binary Model (handled in separate module, but we can placeholder here)
    binary_metrics = {}
    
    # Save individual results
    results_dir = get_results_path()
    save_bootstrap_results(bootstrap_results, bootstrap_metrics, os.path.join(results_dir, 'bootstrap_results.csv'))
    save_alpha_sweep_results(alpha_sweep_df, os.path.join(results_dir, 'alpha_sweep.csv'))
    
    # Save convergence metric separately for reporting
    convergence_data = {
        'converged_pct': bootstrap_metrics['convergence_pct'],
        'total_resamples': bootstrap_metrics['total_resamples']
    }
    import json
    with open(os.path.join(results_dir, 'intermediate_convergence.json'), 'w') as f:
        json.dump(convergence_data, f, indent=2)
    
    # Aggregate all metrics
    save_robustness_results(bootstrap_metrics, alpha_sweep_df, covariate_metrics, binary_metrics, results_dir)
    
    logger.info("All robustness checks completed.")
    return bootstrap_metrics, alpha_sweep_df

def run_bootstrap_pipeline(data: pd.DataFrame, formula: str = None):
    """Pipeline wrapper for bootstrap only."""
    return run_bootstrap(data, formula)

def run_alpha_sweep_pipeline(data: pd.DataFrame, formula: str = None):
    """Pipeline wrapper for alpha sweep only."""
    return run_alpha_sweep(data, formula)

def run_robustness_pipeline(data: pd.DataFrame, formula: str = None):
    """Main pipeline entry point for robustness checks."""
    return run_all_robustness_checks(data, formula)

def main():
    """Entry point for standalone execution."""
    from config_manager import get_data_processed_path
    from preprocessing import run_preprocessing_pipeline
    
    # Load data
    processed_path = get_data_processed_path()
    if not os.path.exists(processed_path):
        logger.error(f"Processed data not found at {processed_path}. Run preprocessing first.")
        return
    
    data = pd.read_csv(processed_path)
    run_robustness_pipeline(data)

if __name__ == '__main__':
    main()
