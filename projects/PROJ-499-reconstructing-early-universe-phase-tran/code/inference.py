import os
import json
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from dynesty import NestedSampler, DynamicNestedSampler
from dynesty.utils import resample_equal
from config import get_config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_likelihood(theta: np.ndarray, data: Dict[str, Any]) -> float:
    """
    Compute the log-likelihood for the given parameters.
    
    Parameters:
    - theta: Array of parameters [log_r, log_E_PT]
    - data: Dictionary containing observed data and configuration
    
    Returns:
    - logL: Log-likelihood value
    """
    # Extract parameters
    log_r, log_E_PT = theta
    
    # Apply clamping for physical bounds
    r = np.exp(log_r)
    E_PT = np.exp(log_E_PT)
    
    # Clamp values to prevent numerical instability
    r = np.clip(r, 1e-5, 1.0)
    E_PT = np.clip(E_PT, 1e14, 1e16)
    
    # Get observed data
    l_values = data['l_values']
    cl_obs = data['cl_obs']
    cl_err = data['cl_err']
    
    # Compute theoretical spectrum based on model type
    model_type = data.get('model_type', 'inflation')
    
    if model_type == 'inflation':
        # Inflation model: C_l ~ r * C_l_tensor
        # Simplified approximation for demonstration
        # In practice, this would use a full Boltzmann solver
        cl_theory = r * 1e-12 * (l_values / 100.0)**-1.0
    elif model_type == 'phase_transition':
        # Phase transition model: C_l ~ f(E_PT) * C_l_peak
        # Simplified approximation
        factor = (E_PT / 1e15)**4
        cl_theory = factor * 1e-14 * np.exp(-((l_values - 100)**2) / (2 * 50**2))
    else:
        # Null model
        cl_theory = np.zeros_like(l_values)
    
    # Clamp predictions for l < 2 to avoid divergence
    l_mask = l_values >= 2
    cl_theory[~l_mask] = cl_theory[l_mask][0] if np.any(l_mask) else 0.0
    
    # Compute chi-squared
    diff = cl_obs - cl_theory
    chi2 = np.sum((diff / cl_err)**2)
    
    # Return log-likelihood
    logL = -0.5 * chi2
    
    return logL

def prior_transform(u: np.ndarray) -> np.ndarray:
    """
    Transform unit hypercube to prior space.
    
    Parameters:
    - u: Array of values in [0, 1]
    
    Returns:
    - theta: Array of parameters in prior space
    """
    # Map to log-uniform priors
    log_r = np.log(1e-5) + u[0] * (np.log(1.0) - np.log(1e-5))
    log_E_PT = np.log(1e14) + u[1] * (np.log(1e16) - np.log(1e14))
    
    return np.array([log_r, log_E_PT])

def run_nested_sampling(
    loglik_func,
    ndim: int,
    n_live_points: int = 50,
    maxiter: int = 1000,
    data: Optional[Dict[str, Any]] = None
) -> Tuple[NestedSampler, Dict[str, Any]]:
    """
    Run nested sampling to estimate posterior distributions.
    
    Parameters:
    - loglik_func: Log-likelihood function
    - ndim: Number of dimensions
    - n_live_points: Number of live points
    - maxiter: Maximum number of iterations
    - data: Optional data dictionary for log-likelihood
    
    Returns:
    - sampler: NestedSampler object
    - results: Dictionary with results
    """
    # Initialize sampler
    if data is not None:
        loglik = lambda x: loglik_func(x, data)
    else:
        loglik = loglik_func
        
    sampler = NestedSampler(
        loglik,
        ndim,
        n_live_points=n_live_points,
        maxiter=maxiter
    )
    
    # Run sampler
    sampler.run_nested()
    
    # Extract results
    results = {
        'logz': sampler.results.logz,
        'logzerr': sampler.results.logzerr,
        'samples': sampler.results.samples,
        'logwt': sampler.results.logwt,
        'logl': sampler.results.logl
    }
    
    return sampler, results

def check_convergence(results: Dict[str, Any], threshold: float = 0.1) -> Tuple[bool, str]:
    """
    Check if nested sampling has converged.
    
    Parameters:
    - results: Results dictionary from nested sampling
    - threshold: Convergence threshold for evidence uncertainty
    
    Returns:
    - converged: Boolean indicating convergence
    - message: Status message
    """
    logz = results['logz']
    logzerr = results['logzerr']
    
    # Check relative uncertainty
    relative_err = logzerr / abs(logz) if logz != 0 else np.inf
    
    if relative_err < threshold:
        message = f"Converged: logZ = {logz:.2f} ± {logzerr:.2f} (rel. err. = {relative_err:.3f})"
        return True, message
    else:
        message = f"Warning: Not converged: logZ = {logz:.2f} ± {logzerr:.2f} (rel. err. = {relative_err:.3f})"
        return False, message

def main():
    """
    Main function to run inference pipeline.
    """
    # Load configuration
    config = get_config()
    
    # Set random seed for reproducibility
    np.random.seed(config.get('random_seed', 42))
    
    # Define data dictionary (in practice, loaded from file)
    # This is a placeholder for demonstration
    data = {
        'l_values': np.array([2, 3, 4, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]),
        'cl_obs': np.array([1e-15, 1.2e-15, 1.5e-15, 1.8e-15, 2.5e-15, 3.0e-15, 3.2e-15, 3.3e-15, 3.4e-15, 3.5e-15, 3.4e-15, 3.2e-15, 3.0e-15, 2.8e-15]),
        'cl_err': np.array([0.5e-15, 0.6e-15, 0.7e-15, 0.8e-15, 1.0e-15, 1.2e-15, 1.3e-15, 1.4e-15, 1.5e-15, 1.5e-15, 1.4e-15, 1.3e-15, 1.2e-15, 1.1e-15]),
        'model_type': 'inflation'
    }
    
    # Run nested sampling
    logger.info("Starting nested sampling...")
    sampler, results = run_nested_sampling(
        log_likelihood,
        ndim=2,
        n_live_points=50,
        maxiter=1000,
        data=data
    )
    
    # Check convergence
    converged, message = check_convergence(results)
    logger.info(message)
    
    # Save results
    output_path = os.path.join('data', 'derived', 'inference_results.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert results to JSON-serializable format
    serializable_results = {
        'logz': float(results['logz']),
        'logzerr': float(results['logzerr']),
        'samples': results['samples'].tolist(),
        'logl': results['logl'].tolist(),
        'converged': converged
    }
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    main()