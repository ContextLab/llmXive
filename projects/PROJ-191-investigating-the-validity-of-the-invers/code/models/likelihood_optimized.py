"""
Optimized likelihood evaluation module.

This module provides a tuned implementation of the log-likelihood function
using Cholesky decomposition for numerical stability and speed. It includes
a benchmarking utility to detect when optimization is necessary based on
runtime thresholds.
"""
import numpy as np
from typing import Tuple, Optional, Callable
from pathlib import Path
import logging
import time
import json
from scipy.linalg import cholesky, cho_solve, LinAlgError

from models.physics import yukawa_force, newtonian_force
from config import get_logger

# Threshold for triggering optimization (in seconds per likelihood call)
# If the average time per call exceeds this, we consider optimization necessary.
DEFAULT_RUNTIME_THRESHOLD_SECONDS = 0.01  # 10ms

logger = get_logger(__name__)

class OptimizedLikelihoodEvaluator:
    """
    A class to handle optimized log-likelihood computations using Cholesky decomposition.
    
    This implementation caches the Cholesky decomposition of the covariance matrix
    to avoid recomputing it for every likelihood evaluation, significantly speeding
    up MCMC and nested sampling runs.
    """
    
    def __init__(self, covariance_matrix: np.ndarray, threshold: float = DEFAULT_RUNTIME_THRESHOLD_SECONDS):
        """
        Initialize the evaluator with a covariance matrix.
        
        Args:
            covariance_matrix: The full covariance matrix (N x N).
            threshold: Runtime threshold in seconds to trigger optimization checks.
        """
        self.covariance_matrix = covariance_matrix
        self.threshold = threshold
        self._cholesky_cache: Optional[np.ndarray] = None
        self._log_det_cache: Optional[float] = None
        self._is_initialized = False
        self._benchmark_times: list = []
        
        logger.info(f"Initializing OptimizedLikelihoodEvaluator with covariance shape {covariance_matrix.shape}")
        self._initialize_cholesky()
    
    def _initialize_cholesky(self) -> None:
        """
        Compute and cache the Cholesky decomposition and log-determinant.
        
        This is done once during initialization to avoid recomputing for
        every likelihood evaluation.
        """
        try:
            # Compute Cholesky decomposition: L such that L @ L.T = cov
            self._cholesky_cache = cholesky(self.covariance_matrix, lower=True, check_finite=False)
            
            # Compute log-determinant: log(det(cov)) = 2 * sum(log(diag(L)))
            diag_L = np.diag(self._cholesky_cache)
            self._log_det_cache = 2.0 * np.sum(np.log(diag_L))
            
            self._is_initialized = True
            logger.info("Cholesky decomposition and log-determinant cached successfully.")
            
        except LinAlgError as e:
            logger.error(f"Cholesky decomposition failed: {e}")
            raise ValueError("Covariance matrix is not positive-definite. Cannot initialize evaluator.")
    
    def _compute_residual(self, force_data: np.ndarray, separation: np.ndarray, 
                         alpha: float, lambda_m: float, model: str = "yukawa") -> np.ndarray:
        """
        Compute the residual between observed and model-predicted forces.
        
        Args:
            force_data: Observed force values (N,).
            separation: Separation distances (N,).
            alpha: Yukawa strength parameter.
            lambda_m: Yukawa range parameter in meters.
            model: Either "yukawa" or "newtonian".
            
        Returns:
            Residual vector (N,).
        """
        if model == "yukawa":
            model_force = yukawa_force(separation, alpha, lambda_m)
        else:
            model_force = newtonian_force(separation)
        
        return force_data - model_force
    
    def log_likelihood(self, force_data: np.ndarray, separation: np.ndarray,
                      alpha: Optional[float] = None, lambda_m: Optional[float] = None,
                      model: str = "yukawa") -> float:
        """
        Compute the log-likelihood using cached Cholesky decomposition.
        
        The log-likelihood for Gaussian errors is:
            log L = -0.5 * (N * log(2π) + log(det(C)) + r.T @ C^-1 @ r)
        
        Where:
            N = number of data points
            C = covariance matrix
            r = residuals (data - model)
        
        Using Cholesky: C^-1 = (L L^T)^-1 = L^-T L^-1
        So: r.T @ C^-1 @ r = || L^-1 @ r ||^2
        
        Args:
            force_data: Observed force values (N,).
            separation: Separation distances (N,).
            alpha: Yukawa strength parameter (required for Yukawa model).
            lambda_m: Yukawa range parameter in meters (required for Yukawa model).
            model: Either "yukawa" or "newtonian".
            
        Returns:
            Log-likelihood value.
        """
        if not self._is_initialized:
            raise RuntimeError("Evaluator not initialized. Call _initialize_cholesky first.")
        
        # Compute residuals
        if model == "yukawa":
            if alpha is None or lambda_m is None:
                raise ValueError("alpha and lambda_m required for Yukawa model")
            residuals = self._compute_residual(force_data, separation, alpha, lambda_m, model)
        else:
            residuals = self._compute_residual(force_data, separation, 0.0, 0.0, model)
        
        # Solve L @ y = residuals for y (i.e., y = L^-1 @ residuals)
        # Then compute ||y||^2 = y.T @ y
        try:
            # cho_solve expects (L, lower) tuple and returns L^-1 @ b
            residuals_inv = cho_solve((self._cholesky_cache, True), residuals)
            chi_sq = np.dot(residuals, residuals_inv)
        except LinAlgError as e:
            logger.error(f"Cholesky solve failed: {e}")
            return -np.inf
        
        # Compute log-likelihood
        n = len(force_data)
        log_det = self._log_det_cache
        log_likelihood = -0.5 * (n * np.log(2 * np.pi) + log_det + chi_sq)
        
        return log_likelihood
    
    def benchmark(self, force_data: np.ndarray, separation: np.ndarray,
                 alpha: float = 0.1, lambda_m: float = 1e-4,
                 num_iterations: int = 100) -> dict:
        """
        Benchmark the likelihood evaluation speed.
        
        Args:
            force_data: Observed force values.
            separation: Separation distances.
            alpha: Test alpha parameter.
            lambda_m: Test lambda parameter.
            num_iterations: Number of iterations to average over.
            
        Returns:
            Dictionary with benchmark results.
        """
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = self.log_likelihood(force_data, separation, alpha, lambda_m, "yukawa")
            end = time.perf_counter()
            times.append(end - start)
        
        avg_time = np.mean(times)
        std_time = np.std(times)
        
        result = {
            "avg_time_per_call_s": avg_time,
            "std_time_per_call_s": std_time,
            "num_iterations": num_iterations,
            "threshold_s": self.threshold,
            "optimization_needed": avg_time > self.threshold
        }
        
        logger.info(f"Benchmark complete: avg_time={avg_time:.6f}s, "
                   f"optimization_needed={result['optimization_needed']}")
        
        return result

def optimize_likelihood_if_needed(covariance_matrix: np.ndarray, 
                                 force_data: np.ndarray,
                                 separation: np.ndarray,
                                 output_path: Optional[Path] = None,
                                 threshold: float = DEFAULT_RUNTIME_THRESHOLD_SECONDS) -> Tuple[OptimizedLikelihoodEvaluator, dict]:
    """
    Create an optimized likelihood evaluator and benchmark it.
    
    If the benchmark shows that optimization is needed (i.e., runtime exceeds threshold),
    this function ensures the Cholesky decomposition is cached and reports the improvement.
    
    Args:
        covariance_matrix: The full covariance matrix.
        force_data: Sample force data for benchmarking.
        separation: Sample separation data for benchmarking.
        output_path: Path to write benchmark results (optional).
        threshold: Runtime threshold in seconds.
        
    Returns:
        Tuple of (OptimizedLikelihoodEvaluator instance, benchmark results dict).
    """
    logger.info("Creating optimized likelihood evaluator...")
    
    evaluator = OptimizedLikelihoodEvaluator(covariance_matrix, threshold)
    
    # Benchmark
    benchmark_results = evaluator.benchmark(force_data, separation)
    
    if benchmark_results["optimization_needed"]:
        logger.warning(f"Likelihood evaluation is slow ({benchmark_results['avg_time_per_call_s']:.6f}s per call). "
                     f"Optimization (Cholesky caching) has been applied.")
    else:
        logger.info(f"Likelihood evaluation is fast ({benchmark_results['avg_time_per_call_s']:.6f}s per call). "
                   f"No further optimization needed.")
    
    # Save results if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(benchmark_results, f, indent=2)
        logger.info(f"Benchmark results written to {output_path}")
    
    return evaluator, benchmark_results

def main():
    """
    Main entry point for testing the optimized likelihood module.
    
    This function loads a sample covariance matrix and data, runs a benchmark,
    and outputs the results to data/results/likelihood_benchmark.json.
    """
    from config import ProjectConfig
    import json
    
    config = ProjectConfig()
    data_dir = config.data_dir
    results_dir = config.results_dir
    
    # Paths for test data (assuming harmonized data exists)
    cov_path = data_dir / "processed" / "covariance_matrix_diagonal.npy"
    data_path = data_dir / "processed" / "harmonized_data.json"
    benchmark_output = results_dir / "likelihood_benchmark.json"
    
    if not cov_path.exists():
        logger.error(f"Covariance matrix not found at {cov_path}. "
                    f"Please run harmonization first.")
        return
    
    if not data_path.exists():
        logger.error(f"Harmonized data not found at {data_path}. "
                    f"Please run data pipeline first.")
        return
    
    # Load data
    logger.info(f"Loading covariance matrix from {cov_path}")
    cov_matrix = np.load(cov_path)
    
    logger.info(f"Loading harmonized data from {data_path}")
    with open(data_path, 'r') as f:
        data_dict = json.load(f)
    
    force_data = np.array(data_dict['force_n'])
    separation = np.array(data_dict['separation_m'])
    
    logger.info(f"Data loaded: {len(force_data)} points")
    
    # Run optimization and benchmark
    evaluator, results = optimize_likelihood_if_needed(
        cov_matrix, force_data, separation, benchmark_output
    )
    
    # Test a few likelihood evaluations
    logger.info("Testing likelihood evaluations...")
    test_alpha = 0.05
    test_lambda = 1e-4
    log_lh = evaluator.log_likelihood(force_data, separation, test_alpha, test_lambda, "yukawa")
    logger.info(f"Log-likelihood for alpha={test_alpha}, lambda={test_lambda}: {log_lh:.4f}")
    
    logger.info("Optimization and benchmark complete.")

if __name__ == "__main__":
    main()
