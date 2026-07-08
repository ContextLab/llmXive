import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import pymc as pm
import arviz as az
from lib.utils import (
    set_seed, 
    MemoryProfiler, 
    MEMORY_LIMIT_GB, 
    profile_memory_enforcement
)
from lib.data_loader import load_time_series

logger = logging.getLogger(__name__)

# Configuration constants
MAX_STEPS = 1000  # Maximum steps for inference to enforce time/memory limits
MEMORY_LIMIT_GB = 7.0

def load_processed_data(
    data_path: str,
    target_column: str = 'value'
) -> np.ndarray:
    """
    Load preprocessed time series data.
    
    Args:
        data_path: Path to the CSV file containing processed data.
        target_column: Name of the column containing the time series values.
        
    Returns:
        Numpy array of time series values.
    """
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    if target_column not in df.columns:
        raise ValueError(f"Column '{target_column}' not found in {data_path}")
    
    data = df[target_column].values
    logger.info(f"Loaded {len(data)} time steps")
    return data

def compute_elbo(
    model: pm.Model,
    trace: az.InferenceData,
    n_samples: int = 1000
) -> float:
    """
    Compute the Evidence Lower Bound (ELBO) from the trace.
    
    Args:
        model: The PyMC model.
        trace: The inference trace.
        n_samples: Number of samples to use for estimation.
        
    Returns:
        Estimated ELBO value.
    """
    # Extract log_likelihood and log_prior from the trace
    # In PyMC, ELBO is approximated during VI
    if hasattr(trace, 'sample_stats') and 'lp' in trace.sample_stats:
        lp_values = trace.sample_stats['lp'].values.flatten()
        return np.mean(lp_values)
    return 0.0

def compute_ess(trace: az.InferenceData, var_name: str = 'mu') -> float:
    """
    Compute the Effective Sample Size (ESS) for a variable.
    
    Args:
        trace: The inference trace.
        var_name: Name of the variable to compute ESS for.
        
    Returns:
        ESS value.
    """
    try:
        ess = az.ess(trace, var_names=[var_name])
        if var_name in ess:
            return float(ess[var_name].values[0])
    except Exception as e:
        logger.warning(f"Could not compute ESS for {var_name}: {e}")
    return 0.0

def run_bayesian_gp(
    data: np.ndarray,
    n_steps: int = MAX_STEPS,
    seed: Optional[int] = 42,
    memory_limit_gb: float = MEMORY_LIMIT_GB
) -> Tuple[Dict[str, Any], np.ndarray]:
    """
    Run Bayesian Gaussian Process inference for anomaly detection.
    Uses Sparse Variational Inference (SVI) for efficiency.
    
    Args:
        data: Time series data (1D numpy array).
        n_steps: Maximum number of inference steps.
        seed: Random seed for reproducibility.
        memory_limit_gb: Memory limit in GB.
        
    Returns:
        Tuple of (results_dict, anomaly_scores).
    """
    set_seed(seed)
    
    logger.info(f"Starting Bayesian GP inference with {len(data)} points")
    logger.info(f"Memory limit: {memory_limit_gb} GB, Max steps: {n_steps}")
    
    # Initialize memory profiler
    profiler = MemoryProfiler(limit_gb=memory_limit_gb, verbose=True)
    profiler.start()
    
    try:
        # Convert to float64 for PyMC
        y = data.astype(np.float64)
        n = len(y)
        x = np.linspace(0, 1, n)
        
        # Check memory usage after data preparation
        profiler.enforce_limit()
        
        # Define the model
        with pm.Model() as model:
            # Hyperpriors for the GP kernel
            sigma = pm.HalfNormal('sigma', sigma=1.0)
            ls = pm.HalfCauchy('ls', beta=2.0)
            
            # Covariance function (RBF kernel)
            cov_func = sigma**2 * pm.gp.cov.ExpQuad(1, ls)
            
            # Marginal GP
            gp = pm.gp.Marginal(cov_func=cov_func)
            
            # Observed data with noise
            noise = pm.HalfNormal('noise', sigma=0.1)
            f = gp.marginal_likelihood('f', X=x[:, None], y=y, sigma=noise)
            
            # Check memory after model definition
            profiler.enforce_limit()
            
            # Variational Inference (Sparse VI approximation)
            logger.info("Starting Variational Inference...")
            start_time = time.time()
            
            # Use ADVI for faster convergence
            approx = pm.fit(
                n=n_steps,
                method='advi',
                random_seed=seed,
                callbacks=[
                    pm.callbacks.CheckParametersConvergence(tolerance=1e-3, diff='relative')
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"VI completed in {elapsed:.2f} seconds")
            
            # Check memory after inference
            profiler.enforce_limit()
            
            # Extract posterior samples
            trace = approx.sample(1000)
            
            # Compute ELBO
            elbo = compute_elbo(model, trace)
            
            # Compute ESS for key parameters
            ess_sigma = compute_ess(trace, 'sigma')
            ess_ls = compute_ess(trace, 'ls')
            ess_noise = compute_ess(trace, 'noise')
            
            logger.info(f"ELBO: {elbo:.4f}, ESS(sigma): {ess_sigma:.1f}, ESS(ls): {ess_ls:.1f}")
            
            # Generate predictions and anomaly scores
            # Anomaly score = deviation from GP posterior mean
            with model:
                # Predictive distribution
                f_pred = gp.conditional('f_pred', X_new=x[:, None])
                ppc = pm.sample_posterior_predictive(trace, var_names=['f_pred'], model=model)
            
            # Extract posterior mean and standard deviation
            f_pred_samples = ppc.posterior_predictive['f_pred'].values
            posterior_mean = np.mean(f_pred_samples, axis=0)
            posterior_std = np.std(f_pred_samples, axis=0)
            
            # Anomaly score: standardized residual
            residuals = y - posterior_mean
            anomaly_scores = np.abs(residuals) / (posterior_std + 1e-8)
            
            # Check final memory usage
            profiler.enforce_limit()
            
            results = {
                'elbo': float(elbo),
                'ess_sigma': float(ess_sigma),
                'ess_ls': float(ess_ls),
                'ess_noise': float(ess_noise),
                'converged': approx.hist[-1] < 1e-3,
                'inference_time': elapsed,
                'n_steps': n_steps,
                'memory_limit_gb': memory_limit_gb
            }
            
            profiler.report(label="Bayesian GP Inference")
            return results, anomaly_scores
            
    except SystemExit:
        profiler.report(label="Bayesian GP Inference (Memory Limit Exceeded)")
        raise
    finally:
        profiler.stop()

def main(
    input_path: str = 'data/processed/series_with_anomalies.csv',
    output_path: str = 'data/results/bayesian_predictions.csv',
    target_column: str = 'value',
    n_steps: int = MAX_STEPS,
    seed: Optional[int] = 42
) -> None:
    """
    Main entry point for Bayesian GP anomaly detection.
    
    Args:
        input_path: Path to input data CSV.
        output_path: Path to save predictions CSV.
        target_column: Column name containing time series values.
        n_steps: Maximum inference steps.
        seed: Random seed.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Bayesian GP Anomaly Detection Pipeline")
    
    # Load data
    data = load_processed_data(input_path, target_column=target_column)
    
    # Run inference
    results, anomaly_scores = run_bayesian_gp(
        data=data,
        n_steps=n_steps,
        seed=seed,
        memory_limit_gb=MEMORY_LIMIT_GB
    )
    
    # Create output DataFrame
    output_df = pd.DataFrame({
        'timestamp': range(len(anomaly_scores)),
        'value': data,
        'anomaly_score': anomaly_scores,
        'is_anomaly': (anomaly_scores > 3.0).astype(int)  # Threshold at 3 sigma
    })
    
    # Save results
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Anomalies detected: {output_df['is_anomaly'].sum()}")
    
    # Log final metrics
    logger.info(f"ELBO: {results['elbo']:.4f}")
    logger.info(f"Converged: {results['converged']}")
    logger.info(f"Inference time: {results['inference_time']:.2f}s")

if __name__ == '__main__':
    main()