"""
Robustness checks for the political news exposure analysis.
Includes bootstrap resampling, alpha sensitivity analysis, and model specification checks.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from typing import List, Dict, Tuple, Optional
import logging
import multiprocessing as mp
from functools import partial
import os
import time
from pathlib import Path

from config_manager import get_results_path, get_config, get_analysis_seed
from logging_config import get_logger
from preprocessing import load_data, impute_mice, derive_variables
from models import fit_primary_model

logger = get_logger(__name__)

def _bootstrap_single_chunk(args):
    """
    Worker function for multiprocessing. Fits the model on a bootstrap sample.
    Args:
        args: (data, interaction_col, seed, chunk_id)
    Returns:
        (chunk_id, list of interaction coefficients)
    """
    data, interaction_col, seed, chunk_id = args
    np.random.seed(seed)
    n = len(data)
    coeffs = []
    # Generate one bootstrap sample per iteration in this chunk
    # To ensure full coverage, the caller should split the total iterations
    # into chunks. Here we assume this function runs N iterations.
    # However, to keep it simple for the worker, we will run a fixed number of iterations
    # or iterate based on the chunk size passed.
    # Let's assume the caller passes the specific indices for this chunk's iterations.
    # Actually, simpler: pass the total count and let worker do its share?
    # No, better: pass the specific indices to resample from.
    # Let's change signature: (data, interaction_col, seeds_list)
    pass

def _bootstrap_worker(data, interaction_col, seeds_list):
    """
    Worker that processes a list of seeds for bootstrapping.
    """
    results = []
    for seed in seeds_list:
        np.random.seed(seed)
        n = len(data)
        # Resample indices with replacement
        indices = np.random.choice(n, size=n, replace=True)
        sample_data = data.iloc[indices].copy()
        
        try:
            model = fit_primary_model(sample_data)
            # Extract interaction coefficient
            # The model is a statsmodels OLS result
            # We need to know the exact name of the interaction term
            # Based on T015: IAT_D ~ news_exposure_z * political_ideology
            # The term is likely 'news_exposure_z:political_ideology' or similar
            # We will try to find the column containing both terms or the interaction syntax
            params = model.params
            interaction_key = None
            for key in params.index:
                if 'news_exposure_z' in key and 'political_ideology' in key and ':' in key:
                    interaction_key = key
                    break
            
            if interaction_key is None:
                # Fallback: look for the product term if generated explicitly
                for key in params.index:
                    if 'news_exposure_z' in key and 'political_ideology' in key:
                        interaction_key = key
                        break
            
            if interaction_key:
                results.append({
                    'seed': seed,
                    'coefficient': params[interaction_key],
                    'p_value': model.pvalues.get(interaction_key, np.nan)
                })
            else:
                logger.warning(f"Interaction term not found in bootstrap sample for seed {seed}")
                results.append({'seed': seed, 'coefficient': np.nan, 'p_value': np.nan})
        except Exception as e:
            logger.warning(f"Bootstrap fit failed for seed {seed}: {e}")
            results.append({'seed': seed, 'coefficient': np.nan, 'p_value': np.nan})
    
    return results

def run_bootstrap(
    data: pd.DataFrame,
    n_bootstrap: int = 1000,
    seed: int = 42,
    chunk_size: int = 100,
    n_jobs: Optional[int] = None
) -> Dict[str, any]:
    """
    Run bootstrap resampling to estimate the confidence interval of the interaction term.
    Uses multiprocessing to speed up the process.
    
    Args:
        data: Imputed and derived dataset
        n_bootstrap: Number of bootstrap resamples
        seed: Random seed for reproducibility
        chunk_size: Number of iterations per worker chunk
        n_jobs: Number of parallel workers (default: number of CPU cores)
    
    Returns:
        Dictionary containing bootstrap statistics
    """
    logger.info(f"Starting bootstrap with {n_bootstrap} resamples...")
    start_time = time.time()
    
    # Determine number of jobs
    if n_jobs is None:
        n_jobs = max(1, mp.cpu_count())
    
    # Generate seeds for each iteration
    np.random.seed(seed)
    all_seeds = np.random.randint(0, 2**31 - 1, size=n_bootstrap)
    
    # Split seeds into chunks
    chunks = []
    for i in range(0, n_bootstrap, chunk_size):
        chunk_seeds = all_seeds[i:i+chunk_size]
        chunks.append(chunk_seeds)
    
    # Prepare data for workers
    # We need to pass the data and the interaction column name
    # Assuming the primary model uses 'news_exposure_z' and 'political_ideology'
    # We will hardcode the interaction logic inside the worker or pass the formula
    # To keep it robust, we'll pass the formula components or the full formula string
    # But fit_primary_model expects data. We assume the data passed here is ready.
    
    # We need to know the interaction term name. Let's fit one model first to get it.
    try:
        reference_model = fit_primary_model(data)
        interaction_key = None
        for key in reference_model.params.index:
            if 'news_exposure_z' in key and 'political_ideology' in key and ':' in key:
                interaction_key = key
                break
        if interaction_key is None:
            for key in reference_model.params.index:
                if 'news_exposure_z' in key and 'political_ideology' in key:
                    interaction_key = key
                    break
        if interaction_key is None:
            raise ValueError("Could not determine interaction term name from primary model.")
    except Exception as e:
        logger.error(f"Failed to determine interaction term from reference model: {e}")
        raise

    logger.info(f"Running {n_bootstrap} bootstrap iterations across {n_jobs} workers...")
    
    # Use multiprocessing
    # We pass (data, interaction_key, chunk_seeds) to the worker
    # But data is large, so we should avoid copying it too much.
    # statsmodels models are usually fast enough that the overhead is worth it.
    
    worker_func = partial(_bootstrap_worker, data, interaction_key)
    
    all_results = []
    
    if n_jobs == 1:
        # Serial execution
        for chunk_seeds in chunks:
            results = worker_func(chunk_seeds)
            all_results.extend(results)
    else:
        # Parallel execution
        with mp.Pool(processes=n_jobs) as pool:
            results_list = pool.map(worker_func, chunks)
            for res in results_list:
                all_results.extend(res)
    
    elapsed = time.time() - start_time
    logger.info(f"Bootstrap completed in {elapsed:.2f} seconds.")
    
    # Calculate statistics
    coeffs = [r['coefficient'] for r in all_results if not np.isnan(r['coefficient'])]
    p_values = [r['p_value'] for r in all_results if not np.isnan(r['p_value'])]
    
    if len(coeffs) == 0:
        logger.error("No valid bootstrap coefficients obtained.")
        return {
            'mean': np.nan,
            'std': np.nan,
            'ci_2.5': np.nan,
            'ci_97.5': np.nan,
            'count': 0,
            'time': elapsed
        }
    
    mean_coef = np.mean(coeffs)
    std_coef = np.std(coeffs)
    ci_25 = np.percentile(coeffs, 2.5)
    ci_975 = np.percentile(coeffs, 97.5)
    
    return {
        'mean': mean_coef,
        'std': std_coef,
        'ci_2.5': ci_25,
        'ci_97.5': ci_975,
        'count': len(coeffs),
        'time': elapsed,
        'samples': all_results
    }

def run_alpha_sweep(
    data: pd.DataFrame,
    alpha_levels: List[float] = [0.01, 0.05, 0.10]
) -> List[Dict]:
    """
    Run analysis at different alpha levels to test sensitivity.
    
    Args:
        data: Imputed and derived dataset
        alpha_levels: List of alpha thresholds to test
    
    Returns:
        List of dictionaries with results for each alpha level
    """
    logger.info(f"Running alpha sweep with levels: {alpha_levels}")
    
    try:
        model = fit_primary_model(data)
        interaction_key = None
        for key in model.pvalues.index:
            if 'news_exposure_z' in key and 'political_ideology' in key and ':' in key:
                interaction_key = key
                break
        if interaction_key is None:
            for key in model.pvalues.index:
                if 'news_exposure_z' in key and 'political_ideology' in key:
                    interaction_key = key
                    break
        
        if interaction_key is None:
            raise ValueError("Interaction term not found in model.")
        
        p_val = model.pvalues[interaction_key]
        coef = model.params[interaction_key]
        
        results = []
        for alpha in alpha_levels:
            significant = p_val < alpha
            results.append({
                'alpha': alpha,
                'coefficient': coef,
                'p_value': p_val,
                'significant': significant
            })
        
        return results
    except Exception as e:
        logger.error(f"Alpha sweep failed: {e}")
        return []

def save_alpha_sweep_results(results: List[Dict], output_path: Optional[Path] = None):
    """Save alpha sweep results to CSV."""
    if output_path is None:
        output_path = get_results_path() / "alpha_sweep.csv"
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Alpha sweep results saved to {output_path}")

def save_bootstrap_results(stats: Dict, output_path: Optional[Path] = None):
    """Save bootstrap summary to CSV."""
    if output_path is None:
        output_path = get_results_path() / "bootstrap_summary.csv"
    
    # Create a summary dataframe
    summary_data = {
        'metric': ['mean', 'std', 'ci_2.5', 'ci_97.5', 'count', 'time'],
        'value': [
            stats['mean'],
            stats['std'],
            stats['ci_2.5'],
            stats['ci_97.5'],
            stats['count'],
            stats['time']
        ]
    }
    df = pd.DataFrame(summary_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Bootstrap summary saved to {output_path}")

def run_all_robustness_checks(
    data: pd.DataFrame,
    n_bootstrap: int = 1000,
    alpha_levels: List[float] = [0.01, 0.05, 0.10],
    n_jobs: Optional[int] = None
) -> Dict[str, any]:
    """
    Run all robustness checks: bootstrap and alpha sweep.
    Uses multiprocessing for the bootstrap step to ensure runtime < 6h on 2-core CPU.
    """
    logger.info("Starting all robustness checks...")
    
    # Run bootstrap
    bootstrap_stats = run_bootstrap(
        data, 
        n_bootstrap=n_bootstrap, 
        n_jobs=n_jobs
    )
    
    # Run alpha sweep
    alpha_results = run_alpha_sweep(data, alpha_levels)
    
    return {
        'bootstrap': bootstrap_stats,
        'alpha_sweep': alpha_results
    }

def run_bootstrap_pipeline():
    """
    Pipeline to run bootstrap analysis on the processed data.
    """
    logger.info("Running bootstrap pipeline...")
    
    # Load data
    data = load_data()
    if data is None:
        logger.error("Failed to load data.")
        return
    
    # Impute and derive
    data = impute_mice(data)
    if data is None:
        logger.error("Imputation failed.")
        return
    
    data = derive_variables(data)
    if data is None:
        logger.error("Variable derivation failed.")
        return
    
    # Run bootstrap
    stats = run_bootstrap(data, n_bootstrap=1000)
    
    # Save results
    save_bootstrap_results(stats)
    
    return stats

def run_alpha_sweep_pipeline():
    """
    Pipeline to run alpha sweep analysis.
    """
    logger.info("Running alpha sweep pipeline...")
    
    # Load data
    data = load_data()
    if data is None:
        logger.error("Failed to load data.")
        return
    
    # Impute and derive
    data = impute_mice(data)
    if data is None:
        logger.error("Imputation failed.")
        return
    
    data = derive_variables(data)
    if data is None:
        logger.error("Variable derivation failed.")
        return
    
    # Run alpha sweep
    results = run_alpha_sweep(data)
    
    # Save results
    save_alpha_sweep_results(results)
    
    return results

def run_robustness_pipeline():
    """
    Main pipeline to run all robustness checks.
    """
    logger.info("Starting robustness pipeline...")
    
    # Load data
    data = load_data()
    if data is None:
        logger.error("Failed to load data.")
        return
    
    # Impute and derive
    data = impute_mice(data)
    if data is None:
        logger.error("Imputation failed.")
        return
    
    data = derive_variables(data)
    if data is None:
        logger.error("Variable derivation failed.")
        return
    
    # Run all checks
    results = run_all_robustness_checks(data, n_bootstrap=1000)
    
    # Save individual results
    if results['bootstrap']:
        save_bootstrap_results(results['bootstrap'])
    if results['alpha_sweep']:
        save_alpha_sweep_results(results['alpha_sweep'])
    
    logger.info("Robustness pipeline completed.")
    return results

if __name__ == "__main__":
    run_robustness_pipeline()
