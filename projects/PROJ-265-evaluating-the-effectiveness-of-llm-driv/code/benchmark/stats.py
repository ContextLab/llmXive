import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
import numpy as np

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error

logger = get_logger(__name__)

def check_normality(data: List[float]) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk normality test.
    
    Returns:
        Tuple of (is_normal, p_value)
        is_normal is True if p_value > 0.05 (fail to reject null hypothesis)
    """
    if len(data) < 3:
        # Not enough data for Shapiro-Wilk, assume normal for small samples
        return True, 1.0
    
    stat, p_value = stats.shapiro(data)
    is_normal = p_value > 0.05
    return is_normal, p_value

def perform_statistical_test(
    original_means: List[float],
    simplified_means: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform statistical comparison between original and simplified performance means.
    
    Uses t-test if data is normally distributed, otherwise Wilcoxon signed-rank test.
    Applies Bonferroni correction for multiple comparisons if needed.
    
    Args:
        original_means: List of mean execution times for original functions
        simplified_means: List of mean execution times for simplified functions
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary containing test results
    """
    if len(original_means) != len(simplified_means):
        raise ValueError("Original and simplified means must have same length")
    
    if len(original_means) == 0:
        return {
            "test_used": "none",
            "reason": "empty_data",
            "p_value": None,
            "statistic": None,
            "is_significant": False,
            "alpha": alpha,
            "sample_size": 0
        }
    
    # Check normality of both distributions
    original_normal, original_p = check_normality(original_means)
    simplified_normal, simplified_p = check_normality(simplified_means)
    
    both_normal = original_normal and simplified_normal
    
    # Choose test based on normality
    if both_normal:
        test_name = "paired_t_test"
        statistic, p_value = stats.ttest_rel(original_means, simplified_means)
    else:
        test_name = "wilcoxon"
        statistic, p_value = stats.wilcoxon(original_means, simplified_means)
    
    # Apply Bonferroni correction if multiple comparisons (here we assume 2 comparisons: time and memory)
    # For this specific task, we focus on time, but the correction is ready for extension
    bonferroni_alpha = alpha  # Single comparison for time, no correction needed
    is_significant = p_value < bonferroni_alpha
    
    return {
        "test_used": test_name,
        "normality_original": {
            "is_normal": original_normal,
            "p_value": original_p
        },
        "normality_simplified": {
            "is_normal": simplified_normal,
            "p_value": simplified_p
        },
        "p_value": float(p_value),
        "statistic": float(statistic),
        "is_significant": bool(is_significant),
        "alpha_used": bonferroni_alpha,
        "sample_size": len(original_means),
        "means_original": float(np.mean(original_means)),
        "means_simplified": float(np.mean(simplified_means)),
        "std_original": float(np.std(original_means)),
        "std_simplified": float(np.std(simplified_means))
    }

def analyze_benchmark_results(
    results_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Load benchmark results and perform statistical analysis.
    
    Args:
        results_path: Path to the benchmark results JSON file
        output_path: Path to save the statistical summary
        
    Returns:
        Dictionary containing the full statistical analysis
    """
    log_stage_start(logger, "statistical_analysis", input=str(results_path), output=str(output_path))
    
    try:
        # Load benchmark results
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Extract means for original and simplified functions
        original_means = []
        simplified_means = []
        
        for pair in results.get("pairs", []):
            if "original_stats" in pair and "simplified_stats" in pair:
                orig_stats = pair["original_stats"]
                simp_stats = pair["simplified_stats"]
                
                if "mean_time" in orig_stats and "mean_time" in simp_stats:
                    original_means.append(orig_stats["mean_time"])
                    simplified_means.append(simp_stats["mean_time"])
        
        if len(original_means) == 0:
            raise ValueError("No valid benchmark pairs found in results")
        
        # Perform statistical test on the distribution of means
        # As per FR-009 and SC-001/SC-002, we test on N=200 means, not raw iterations
        test_results = perform_statistical_test(original_means, simplified_means)
        
        # Add summary statistics
        test_results["total_pairs_analyzed"] = len(original_means)
        test_results["original_mean_of_means"] = float(np.mean(original_means))
        test_results["simplified_mean_of_means"] = float(np.mean(simplified_means))
        test_results["original_std_of_means"] = float(np.std(original_means))
        test_results["simplified_std_of_means"] = float(np.std(simplified_means))
        
        # Calculate effect size (Cohen's d) for paired samples
        if len(original_means) > 1:
            diffs = np.array(original_means) - np.array(simplified_means)
            mean_diff = np.mean(diffs)
            std_diff = np.std(diffs)
            if std_diff > 0:
                cohens_d = mean_diff / std_diff
            else:
                cohens_d = 0.0
        else:
            cohens_d = 0.0
        
        test_results["cohens_d"] = float(cohens_d)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        log_stage_complete(logger, "statistical_analysis", output=str(output_path))
        return test_results
        
    except Exception as e:
        log_stage_error(logger, "statistical_analysis", str(e))
        raise

def run_statistical_analysis(
    input_file: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Main entry point for running statistical analysis on benchmark results.
    
    Args:
        input_file: Path to benchmark results JSON
        output_file: Path to save statistical summary JSON
        
    Returns:
        Statistical analysis results dictionary
    """
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    return analyze_benchmark_results(input_path, output_path)

def main():
    """Main entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m benchmark.stats <input_results.json> <output_summary.json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        results = run_statistical_analysis(input_file, output_file)
        print(f"Statistical analysis complete. Results saved to: {output_file}")
        print(f"Test used: {results['test_used']}")
        print(f"P-value: {results['p_value']:.6f}")
        print(f"Significant at alpha={results['alpha_used']}: {results['is_significant']}")
        print(f"Cohen's d: {results['cohens_d']:.4f}")
    except Exception as e:
        print(f"Error during statistical analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()