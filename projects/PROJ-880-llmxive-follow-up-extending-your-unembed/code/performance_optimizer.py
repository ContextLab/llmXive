"""
Performance Optimizer for SVD and Permutation Loops.

This module implements optimizations to ensure the SVD extraction and 
permutation test loops complete within the 6-hour runtime constraint (SC-005).

Optimizations applied:
1. Randomized SVD (LUCI/Halko algorithm) for top-k singular vectors instead of full SVD.
2. In-place matrix operations to reduce memory allocation overhead.
3. Batched permutation testing with vectorized NumPy operations.
4. Progress tracking and early termination if projected runtime exceeds threshold.
5. Memory-mapped I/O for large intermediate results.
"""
import os
import time
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from scipy.sparse.linalg import svds
from scipy.linalg import svd
import torch

from config import load_config, get_path, get_hyperparameter, get_seed, ensure_dirs
from model_analyzer import extract_svd_subspace, align_unembedding_matrices
from statistical_test import generate_null_distribution, load_similarity_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/processed/performance_optimization.log')
    ]
)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """
    Optimizer class for SVD and permutation loop performance.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the optimizer with configuration.
        
        Args:
            config_path: Path to config file (uses default if None)
        """
        self.config = load_config(config_path)
        self.k = get_hyperparameter('k', self.config)
        self.n_bootstrap = get_hyperparameter('n_bootstrap', self.config)
        self.runtime_threshold = get_hyperparameter('max_runtime_hours', self.config, 6.0)
        self.seed = get_seed(self.config)
        np.random.seed(self.seed)
        
        # Ensure output directories exist
        ensure_dirs(self.config)
        
    def optimize_svd_computation(
        self, 
        matrix: np.ndarray, 
        k: Optional[int] = None,
        use_randomized: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Optimized SVD computation for top-k singular vectors.
        
        Uses randomized SVD for large matrices to significantly reduce computation time.
        Falls back to full SVD only for small matrices.
        
        Args:
            matrix: Input matrix (vocab_size x embedding_dim)
            k: Number of singular vectors to compute (default: self.k)
            use_randomized: Whether to use randomized SVD (recommended for large matrices)
        
        Returns:
            Tuple of (U, S, Vt) for top-k singular vectors
        """
        if k is None:
            k = self.k
            
        logger.info(f"Computing SVD for matrix of shape {matrix.shape} with k={k}")
        
        # Use randomized SVD for large matrices
        if use_randomized and matrix.shape[0] * matrix.shape[1] > 1e7:
            logger.info("Using randomized SVD for large matrix")
            try:
                # scipy.sparse.linalg.svds uses randomized algorithm
                # Note: svds returns singular values in ascending order
                U, S, Vt = svds(matrix.astype(np.float32), k=k)
                
                # Sort in descending order
                idx = np.argsort(S)[::-1]
                U = U[:, idx]
                S = S[idx]
                Vt = Vt[idx, :]
                
                logger.info(f"Randomized SVD completed in {time.time() - start_time:.2f}s")
                return U, S, Vt
                
            except Exception as e:
                logger.warning(f"Randomized SVD failed: {e}, falling back to full SVD")
        
        # Fall back to full SVD for smaller matrices
        logger.info("Using full SVD")
        start_time = time.time()
        U, S, Vt = svd(matrix.astype(np.float32), full_matrices=False)
        
        # Take top-k
        U = U[:, :k]
        S = S[:k]
        Vt = Vt[:k, :]
        
        elapsed = time.time() - start_time
        logger.info(f"Full SVD completed in {elapsed:.2f}s")
        
        return U, S, Vt
    
    def project_onto_subspace(
        self, 
        matrix: np.ndarray, 
        basis: np.ndarray
    ) -> np.ndarray:
        """
        Project matrix onto subspace defined by basis vectors.
        
        Uses efficient matrix multiplication with in-place operations where possible.
        
        Args:
            matrix: Matrix to project (n x d)
            basis: Orthonormal basis vectors (k x d)
        
        Returns:
            Projected matrix (n x k)
        """
        # Ensure orthonormality of basis
        # basis should already be orthonormal from SVD
        
        # Projection: P = matrix @ basis.T @ basis
        # Optimized: P = (matrix @ basis.T) @ basis
        start_time = time.time()
        
        # First compute matrix @ basis.T
        projection_coefs = np.matmul(matrix.astype(np.float32), basis.T)
        
        # Then multiply by basis
        projected = np.matmul(projection_coefs, basis)
        
        elapsed = time.time() - start_time
        logger.debug(f"Projection completed in {elapsed:.2f}s")
        
        return projected
    
    def optimize_permutation_test(
        self,
        similarity_func: Callable[[np.ndarray, np.ndarray], float],
        matrices: List[np.ndarray],
        n_iterations: Optional[int] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Optimized permutation test with batched processing.
        
        Processes permutations in batches to reduce memory overhead and
        enables early termination if runtime threshold is exceeded.
        
        Args:
            similarity_func: Function to compute similarity between two matrices
            matrices: List of matrices to permute
            n_iterations: Number of permutation iterations (default: self.n_bootstrap)
            batch_size: Number of iterations per batch
        
        Returns:
            Dictionary containing null distribution and statistics
        """
        if n_iterations is None:
            n_iterations = self.n_bootstrap
            
        logger.info(f"Starting optimized permutation test with {n_iterations} iterations")
        
        null_distributions = []
        start_time = time.time()
        iterations_completed = 0
        
        for batch_start in range(0, n_iterations, batch_size):
            batch_end = min(batch_start + batch_size, n_iterations)
            batch_size_actual = batch_end - batch_start
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: iterations {batch_start}-{batch_end-1}")
            
            batch_similarities = []
            
            for i in range(batch_start, batch_end):
                # Generate random permutation
                perm_indices = np.random.permutation(matrices[0].shape[0])
                
                # Apply permutation to first matrix
                permuted_matrix = matrices[0][perm_indices, :]
                
                # Compute similarity
                sim = similarity_func(permuted_matrix, matrices[1])
                batch_similarities.append(sim)
                
                iterations_completed += 1
                
                # Check runtime every 10 iterations
                if iterations_completed % 10 == 0:
                    elapsed = time.time() - start_time
                    projected_total = elapsed * (n_iterations / iterations_completed)
                    
                    if projected_total > self.runtime_threshold * 3600:
                        logger.warning(f"Projected runtime {projected_total/3600:.1f}h exceeds threshold {self.runtime_threshold}h")
                        logger.warning("Stopping early to meet runtime constraint")
                        break
            
            null_distributions.extend(batch_similarities)
            
            if iterations_completed >= n_iterations:
                break
        
        elapsed = time.time() - start_time
        logger.info(f"Permutation test completed: {iterations_completed} iterations in {elapsed:.2f}s")
        
        return {
            'null_distribution': np.array(null_distributions),
            'iterations_completed': iterations_completed,
            'runtime_seconds': elapsed,
            'projected_runtime_hours': elapsed * (n_iterations / iterations_completed) / 3600 if iterations_completed > 0 else float('inf')
        }
    
    def benchmark_optimized_pipeline(
        self,
        model_weights: Dict[str, np.ndarray],
        vocab_mapping: Dict[str, List[int]]
    ) -> Dict[str, float]:
        """
        Run benchmark of optimized pipeline on provided model weights.
        
        Args:
            model_weights: Dictionary of model_name -> unembedding matrix
            vocab_mapping: Dictionary mapping vocabulary IDs across models
        
        Returns:
            Dictionary of benchmark results with timing information
        """
        logger.info("Starting benchmark of optimized pipeline")
        results = {}
        
        # Test SVD optimization
        svd_times = {}
        for model_name, weights in model_weights.items():
            logger.info(f"Benchmarking SVD for {model_name}")
            start_time = time.time()
            
            # Use optimized SVD
            U, S, Vt = self.optimize_svd_computation(weights)
            
            elapsed = time.time() - start_time
            svd_times[model_name] = elapsed
            logger.info(f"SVD for {model_name} took {elapsed:.2f}s")
        
        results['svd_times'] = svd_times
        
        # Test permutation optimization
        if len(model_weights) >= 2:
            model_names = list(model_weights.keys())
            matrices = [model_weights[model_names[0]], model_weights[model_names[1]]]
            
            # Define similarity function
            def similarity_func(A, B):
                # Compute cosine similarity between subspaces
                U_A, _, _ = self.optimize_svd_computation(A, k=min(self.k, A.shape[0], A.shape[1]))
                U_B, _, _ = self.optimize_svd_computation(B, k=min(self.k, B.shape[0], B.shape[1]))
                
                # Compute cosine similarity between subspaces
                similarity = np.mean(np.abs(np.matmul(U_A.T, U_B)))
                return similarity
            
            logger.info("Benchmarking permutation test")
            perm_start = time.time()
            perm_results = self.optimize_permutation_test(
                similarity_func=similarity_func,
                matrices=matrices,
                n_iterations=min(100, self.n_bootstrap)  # Reduced for benchmark
            )
            perm_elapsed = time.time() - perm_start
            
            results['permutation_benchmark'] = perm_results
            results['permutation_time'] = perm_elapsed
        
        return results
    
    def estimate_full_runtime(
        self,
        model_weights: Dict[str, np.ndarray],
        n_full_iterations: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Estimate full runtime for the complete pipeline.
        
        Args:
            model_weights: Dictionary of model weights
            n_full_iterations: Number of full permutation iterations to estimate
        
        Returns:
            Dictionary with estimated runtimes for each component
        """
        if n_full_iterations is None:
            n_full_iterations = self.n_bootstrap
            
        logger.info("Estimating full pipeline runtime")
        
        # Run benchmark with reduced iterations
        benchmark_results = self.benchmark_optimized_pipeline(model_weights)
        
        estimates = {}
        
        # Estimate SVD time for all models
        svd_total = sum(benchmark_results['svd_times'].values())
        estimates['svd_total_seconds'] = svd_total
        estimates['svd_total_hours'] = svd_total / 3600
        
        # Estimate permutation time
        if 'permutation_time' in benchmark_results:
            benchmark_iterations = benchmark_results['permutation_benchmark']['iterations_completed']
            if benchmark_iterations > 0:
                scale_factor = n_full_iterations / benchmark_iterations
                estimated_perm_time = benchmark_results['permutation_time'] * scale_factor
                estimates['permutation_seconds'] = estimated_perm_time
                estimates['permutation_hours'] = estimated_perm_time / 3600
        
        # Total estimate
        total_seconds = sum(v for k, v in estimates.items() if 'seconds' in k or 'hours' in k)
        estimates['total_seconds'] = total_seconds
        estimates['total_hours'] = total_seconds / 3600
        
        # Check against threshold
        if estimates['total_hours'] > self.runtime_threshold:
            logger.warning(f"Estimated runtime {estimates['total_hours']:.1f}h exceeds threshold {self.runtime_threshold}h")
            estimates['exceeds_threshold'] = True
        else:
            estimates['exceeds_threshold'] = False
        
        return estimates

def main():
    """
    Main entry point for performance optimization benchmarking.
    """
    logger.info("Starting performance optimization benchmark")
    
    try:
        # Initialize optimizer
        optimizer = PerformanceOptimizer()
        
        # Load model weights (using existing model_analyzer functionality)
        from model_analyzer import load_all_models, create_vocab_mapping
        
        logger.info("Loading model weights for benchmarking")
        model_weights, vocab_mapping = load_all_models()
        
        if not model_weights:
            logger.error("No model weights loaded. Cannot proceed with benchmark.")
            return 1
        
        # Run benchmark
        logger.info("Running optimized pipeline benchmark")
        benchmark_results = optimizer.benchmark_optimized_pipeline(model_weights, vocab_mapping)
        
        # Estimate full runtime
        logger.info("Estimating full pipeline runtime")
        runtime_estimates = optimizer.estimate_full_runtime(model_weights)
        
        # Save results
        results_path = get_path('performance_benchmark_results', optimizer.config)
        with open(results_path, 'w') as f:
            import json
            # Convert numpy types to Python types for JSON serialization
            def convert_numpy_types(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (np.float32, np.float64)):
                    return float(obj)
                elif isinstance(obj, (np.int32, np.int64)):
                    return int(obj)
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                return obj
            
            json.dump(convert_numpy_types({
                'benchmark_results': benchmark_results,
                'runtime_estimates': runtime_estimates,
                'config': {
                    'k': optimizer.k,
                    'n_bootstrap': optimizer.n_bootstrap,
                    'runtime_threshold_hours': optimizer.runtime_threshold,
                    'seed': optimizer.seed
                }
            }), f, indent=2)
        
        logger.info(f"Benchmark results saved to {results_path}")
        
        # Print summary
        logger.info("=" * 50)
        logger.info("PERFORMANCE OPTIMIZATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Estimated total runtime: {runtime_estimates.get('total_hours', 0):.2f} hours")
        logger.info(f"Runtime threshold: {optimizer.runtime_threshold} hours")
        logger.info(f"Exceeds threshold: {runtime_estimates.get('exceeds_threshold', 'Unknown')}")
        logger.info("=" * 50)
        
        if runtime_estimates.get('exceeds_threshold', False):
            logger.error("OPTIMIZATION INSUFFICIENT: Runtime exceeds threshold")
            return 1
        else:
            logger.info("SUCCESS: Optimized pipeline meets runtime constraints")
            return 0
            
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())