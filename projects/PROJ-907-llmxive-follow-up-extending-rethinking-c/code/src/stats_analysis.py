import json
import logging
import os
import sys
import subprocess
import shutil
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    import random
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def run_benchmark_with_seed(seed: int) -> Tuple[float, float]:
    """
    Re-execute the benchmark script with a specific seed.
    Returns (static_fid, dynamic_fid).
    """
    logger.info(f"Running benchmark with seed {seed}...")
    set_seed(seed)
    
    # Construct environment with specific seed
    env = os.environ.copy()
    env['RANDOM_SEED'] = str(seed)
    
    # Path to the benchmark script
    benchmark_script = Path(__file__).parent / "benchmark.py"
    
    try:
        # Run the benchmark script
        result = subprocess.run(
            [sys.executable, str(benchmark_script)],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output to extract FID scores
        # We expect the benchmark script to print or log the final FID scores
        # For robustness, we assume the benchmark writes to benchmark_results.json
        # and we read the latest entry for this seed
        
        results_file = Path(__file__).parent.parent / "data" / "results" / "benchmark_results.json"
        if not results_file.exists():
            raise RuntimeError(f"Benchmark results file not found: {results_file}")
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Find the entries for this seed
        seed_results = [r for r in results if r.get('seed') == seed]
        if len(seed_results) < 2:
            raise RuntimeError(f"Could not find both static and dynamic results for seed {seed}")
        
        static_fid = None
        dynamic_fid = None
        
        for r in seed_results:
            if r.get('model_type') == 'static':
                static_fid = r.get('fid_score')
            elif r.get('model_type') == 'dynamic':
                dynamic_fid = r.get('fid_score')
        
        if static_fid is None or dynamic_fid is None:
            raise RuntimeError(f"Missing FID scores for seed {seed}")
        
        return float(static_fid), float(dynamic_fid)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Benchmark script failed for seed {seed}: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error processing results for seed {seed}: {e}")
        raise

def compute_paired_difference_stats(differences: List[float]) -> Dict[str, float]:
    """
    Compute mean and standard deviation of paired differences.
    """
    if not differences:
        return {"mean": 0.0, "std": 0.0}
    
    mean_diff = float(np.mean(differences))
    std_diff = float(np.std(differences, ddof=1)) if len(differences) > 1 else 0.0
    
    return {
        "mean": mean_diff,
        "std": std_diff,
        "n": len(differences)
    }

def perform_bootstrap_test(
    differences: List[float],
    n_resamples: int = 10000,
    confidence_level: float = 0.95,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Perform non-parametric bootstrap test on paired differences.
    
    Args:
        differences: List of paired differences (static - dynamic)
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level for interval (default 0.95)
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary containing bootstrap results including p-values,
        confidence intervals, and distribution statistics.
    """
    np.random.seed(random_state)
    n = len(differences)
    
    if n == 0:
        logger.warning("No differences provided for bootstrap test")
        return {
            "p_value": 1.0,
            "confidence_interval": [0.0, 0.0],
            "bootstrap_mean": 0.0,
            "bootstrap_std": 0.0,
            "bootstrap_distribution": []
        }
    
    # Generate bootstrap samples
    bootstrap_means = []
    for _ in range(n_resamples):
        # Resample with replacement
        resample = np.random.choice(differences, size=n, replace=True)
        bootstrap_means.append(float(np.mean(resample)))
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Calculate p-value (two-tailed test: H0: mean difference = 0)
    # Count how many bootstrap means are as extreme or more extreme than 0
    # using the absolute value
    observed_mean = np.mean(differences)
    extreme_count = np.sum(np.abs(bootstrap_means) >= np.abs(observed_mean))
    p_value = extreme_count / n_resamples
    
    # Calculate 95% confidence interval using percentile method
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    ci_lower = float(np.percentile(bootstrap_means, lower_percentile))
    ci_upper = float(np.percentile(bootstrap_means, upper_percentile))
    
    return {
        "p_value": float(p_value),
        "confidence_interval": [ci_lower, ci_upper],
        "confidence_level": confidence_level,
        "bootstrap_mean": float(np.mean(bootstrap_means)),
        "bootstrap_std": float(np.std(bootstrap_means)),
        "bootstrap_distribution": bootstrap_means.tolist(),
        "n_resamples": n_resamples,
        "original_mean": observed_mean,
        "original_std": float(np.std(differences, ddof=1)) if n > 1 else 0.0
    }

def run_statistical_analysis(
    n_seeds: int = 5,
    seeds: List[int] = None,
    n_resamples: int = 10000,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Run full statistical analysis pipeline:
    1. Execute benchmark with multiple seeds
    2. Compute paired differences
    3. Perform bootstrap significance test
    4. Document limitations
    
    Args:
        n_seeds: Number of seeds to run (default 5)
        seeds: Specific seeds to use (if None, generates sequential seeds)
        n_resamples: Number of bootstrap resamples
        output_path: Path to save results (default: data/results/statistical_analysis.json)
        
    Returns:
        Dictionary containing all analysis results
    """
    if seeds is None:
        # Generate 5 sequential seeds starting from 42
        base_seed = 42
        seeds = [base_seed + i for i in range(n_seeds)]
    
    logger.info(f"Starting statistical analysis with {n_seeds} seeds: {seeds}")
    
    paired_differences = []
    all_results = []
    
    # Run benchmark for each seed
    for seed in seeds:
        try:
            static_fid, dynamic_fid = run_benchmark_with_seed(seed)
            difference = static_fid - dynamic_fid
            paired_differences.append(difference)
            
            result_entry = {
                "seed": seed,
                "static_fid": static_fid,
                "dynamic_fid": dynamic_fid,
                "difference": difference
            }
            all_results.append(result_entry)
            
            logger.info(f"Seed {seed}: Static={static_fid:.4f}, Dynamic={dynamic_fid:.4f}, Diff={difference:.4f}")
            
        except Exception as e:
            logger.error(f"Failed to process seed {seed}: {e}")
            # Continue with other seeds even if one fails
            continue
    
    if not paired_differences:
        raise RuntimeError("No valid paired differences computed. Check benchmark execution.")
    
    logger.info(f"Computed {len(paired_differences)} paired differences")
    
    # Compute basic statistics
    basic_stats = compute_paired_difference_stats(paired_differences)
    
    # Perform bootstrap test
    bootstrap_results = perform_bootstrap_test(
        differences=paired_differences,
        n_resamples=n_resamples,
        confidence_level=0.95,
        random_state=42
    )
    
    # Document statistical limitations (Constitution Principle VI, Spec FR-006)
    # N=5 is too small for parametric tests (normality assumption cannot be verified)
    statistical_limitations = (
        "Statistical Limitations (Constitution Principle VI, Spec FR-006): "
        "This analysis is based on N=5 independent runs. This sample size is insufficient "
        "to reliably assume normality of the difference distribution, which is required "
        "for parametric tests (e.g., paired t-test). Therefore, we employ a non-parametric "
        "bootstrap approach with percentile-based confidence intervals, which does not "
        "rely on distributional assumptions. However, with N=5, the bootstrap distribution "
        "may still be coarse, and the resulting confidence intervals and p-values should "
        "be interpreted with caution. The power of this test is limited, and small but "
        "meaningful effects may not be detected. These results are preliminary and "
        "should be validated with a larger sample size in future work."
    )
    
    # Compile final results
    analysis_results = {
        "n_seeds": n_seeds,
        "seeds_used": seeds,
        "paired_differences": paired_differences,
        "basic_statistics": basic_stats,
        "bootstrap_results": bootstrap_results,
        "statistical_limitations": statistical_limitations,
        "individual_run_results": all_results,
        "methodology": {
            "test_type": "non-parametric bootstrap",
            "confidence_level": 0.95,
            "interval_method": "percentile",
            "n_resamples": n_resamples,
            "null_hypothesis": "mean difference = 0 (static and dynamic models perform equally)"
        }
    }
    
    # Save results to file
    if output_path is None:
        output_path = Path(__file__).parent.parent / "data" / "results" / "statistical_analysis.json"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Statistical analysis results saved to {output_path}")
    
    return analysis_results

def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting statistical analysis (T026)...")
    
    try:
        results = run_statistical_analysis(
            n_seeds=5,
            n_resamples=10000
        )
        
        logger.info("Statistical analysis completed successfully")
        logger.info(f"P-value: {results['bootstrap_results']['p_value']:.4f}")
        logger.info(f"95% CI: [{results['bootstrap_results']['confidence_interval'][0]:.4f}, "
                    f"{results['bootstrap_results']['confidence_interval'][1]:.4f}]")
        
        return 0
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())