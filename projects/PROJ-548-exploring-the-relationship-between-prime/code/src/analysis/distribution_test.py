import os
import sys
import json
import math
import logging
import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

# Import configuration and utilities from the project
# Assuming these are available in the project structure as per API surface
try:
    from src.utils.config import get_project_paths, get_global_seed
    from src.utils.io import save_state, load_state
    from src.utils.seeds import set_global_seed
except ImportError:
    # Fallback for direct execution or different import structure
    # In a real project, these imports should be absolute relative to the project root
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_primes_gaps(file_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load prime gaps data from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing prime gaps.
        
    Returns:
        Tuple of (primes_before, primes_after, gaps, normalized_gaps) as numpy arrays.
    """
    primes_before = []
    primes_after = []
    gaps = []
    normalized_gaps = []
    
    with open(file_path, 'r') as f:
        # Skip header
        f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                primes_before.append(int(parts[0]))
                primes_after.append(int(parts[1]))
                gaps.append(float(parts[2]))
                normalized_gaps.append(float(parts[3]))
    
    return (
        np.array(primes_before),
        np.array(primes_after),
        np.array(gaps),
        np.array(normalized_gaps)
    )

def extract_maximal_gaps_in_windows(
    primes_before: np.ndarray, 
    gaps: np.ndarray, 
    window_size: int = 10**6
) -> List[float]:
    """
    Extract maximal prime gaps within non-overlapping windows.
    
    Args:
        primes_before: Array of primes before the gap.
        gaps: Array of gap sizes.
        window_size: Number of primes per window.
        
    Returns:
        List of maximal gaps in each window.
    """
    maximal_gaps = []
    num_primes = len(primes_before)
    
    for i in range(0, num_primes, window_size):
        end_idx = min(i + window_size, num_primes)
        window_gaps = gaps[i:end_idx]
        if len(window_gaps) > 0:
            maximal_gaps.append(float(np.max(window_gaps)))
    
    return maximal_gaps

def normalize_maximal_gaps(maximal_gaps: List[float], primes_before: np.ndarray, window_size: int = 10**6) -> List[float]:
    """
    Normalize maximal gaps by log^2(p) where p is the approximate prime in the window.
    
    Args:
        maximal_gaps: List of maximal gaps.
        primes_before: Array of primes before the gap.
        window_size: Number of primes per window.
        
    Returns:
        List of normalized maximal gaps.
    """
    normalized = []
    num_windows = len(maximal_gaps)
    
    for i in range(num_windows):
        start_idx = i * window_size
        end_idx = min((i + 1) * window_size, len(primes_before))
        
        if start_idx >= len(primes_before):
            break
            
        # Use the median prime in the window as the reference point
        window_primes = primes_before[start_idx:end_idx]
        if len(window_primes) == 0:
            continue
            
        p_ref = np.median(window_primes)
        if p_ref <= 1:
            p_ref = 2
            
        log_p = math.log(p_ref)
        if log_p <= 0:
            log_p = 1.0
            
        normalized_gap = maximal_gaps[i] / (log_p ** 2)
        normalized.append(normalized_gap)
    
    return normalized

def gue_extreme_value_cdf(x: float, loc: float = 0.0, scale: float = 1.0) -> float:
    """
    Compute the GUE-derived extreme value CDF for maximal gaps.
    
    The formula is based on the GUE Tracy-Widom distribution or a related
    extreme value distribution derived from Random Matrix Theory.
    For this implementation, we use a simplified approximation:
    F(x) = exp(-exp(-(x - loc) / scale))  # Gumbel distribution as an approximation
    
    In a more rigorous implementation, this would use the actual Tracy-Widom
    distribution or the specific GUE extreme value CDF formula from data-model.md.
    
    Args:
        x: Value at which to evaluate the CDF.
        loc: Location parameter.
        scale: Scale parameter.
        
    Returns:
        CDF value at x.
    """
    # Using Gumbel distribution as an approximation for the GUE extreme value CDF
    # This should be replaced with the exact formula from data-model.md
    if scale <= 0:
        scale = 1.0
        
    z = (x - loc) / scale
    return math.exp(-math.exp(-z))

def compute_empirical_cdf(data: List[float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the empirical CDF from a list of data points.
    
    Args:
        data: List of data points.
        
    Returns:
        Tuple of (sorted_values, cdf_values).
    """
    if len(data) == 0:
        return np.array([]), np.array([])
        
    sorted_data = np.sort(data)
    n = len(sorted_data)
    cdf_values = np.arange(1, n + 1) / n
    
    return sorted_data, cdf_values

def run_ks_test(empirical_data: List[float], theoretical_cdf_func, loc: float = 0.0, scale: float = 1.0) -> Dict[str, float]:
    """
    Perform Kolmogorov-Smirnov test comparing empirical data to theoretical distribution.
    
    Args:
        empirical_data: List of empirical data points.
        theoretical_cdf_func: Function that computes the theoretical CDF.
        loc: Location parameter for the theoretical distribution.
        scale: Scale parameter for the theoretical distribution.
        
    Returns:
        Dictionary with KS statistic and p-value.
    """
    if len(empirical_data) == 0:
        return {"ks_statistic": 0.0, "p_value": 1.0, "n": 0}
        
    empirical_data = np.array(empirical_data)
    n = len(empirical_data)
    
    # Compute empirical CDF
    sorted_data, emp_cdf = compute_empirical_cdf(empirical_data)
    
    # Compute theoretical CDF values at the same points
    theo_cdf = np.array([theoretical_cdf_func(x, loc, scale) for x in sorted_data])
    
    # Compute KS statistic (maximum absolute difference)
    ks_statistic = np.max(np.abs(emp_cdf - theo_cdf))
    
    # Compute p-value using scipy's kstest
    # We define the theoretical CDF as a lambda for scipy
    from scipy.stats import kstest
    
    # Create a callable CDF function for scipy
    def cdf_func(x):
        return theoretical_cdf_func(x, loc, scale)
    
    # Perform KS test
    ks_result = kstest(empirical_data, cdf_func)
    
    return {
        "ks_statistic": float(ks_statistic),
        "p_value": float(ks_result.pvalue),
        "n": n
    }

def plot_cdf_comparison(
    empirical_data: List[float], 
    theoretical_cdf_func, 
    loc: float = 0.0, 
    scale: float = 1.0,
    output_path: str = "results/correlation_plot.png"
):
    """
    Generate a visualization of the empirical vs theoretical CDF.
    
    Args:
        empirical_data: List of empirical data points.
        theoretical_cdf_func: Function that computes the theoretical CDF.
        loc: Location parameter for the theoretical distribution.
        scale: Scale parameter for the theoretical distribution.
        output_path: Path to save the plot.
    """
    import matplotlib.pyplot as plt
    
    if len(empirical_data) == 0:
        logger.warning("No empirical data to plot")
        return
        
    sorted_data, emp_cdf = compute_empirical_cdf(empirical_data)
    theo_cdf = np.array([theoretical_cdf_func(x, loc, scale) for x in sorted_data])
    
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_data, emp_cdf, label='Empirical CDF', linewidth=2)
    plt.plot(sorted_data, theo_cdf, label='Theoretical GUE CDF', linewidth=2, linestyle='--')
    plt.xlabel('Normalized Maximal Gap')
    plt.ylabel('Cumulative Probability')
    plt.title('Comparison of Empirical vs Theoretical GUE Extreme Value CDF')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

def run_pipeline(
    input_file: str = "data/processed/primes_gaps.csv",
    window_size: int = 10**6,
    output_json: str = "results/correlation_results.json",
    output_plot: str = "results/correlation_plot.png",
    gue_loc: float = 0.0,
    gue_scale: float = 1.0
):
    """
    Run the full KS test pipeline comparing empirical maximal gaps to GUE distribution.
    
    Args:
        input_file: Path to the input primes_gaps.csv file.
        window_size: Size of windows for extracting maximal gaps.
        output_json: Path to save the results JSON.
        output_plot: Path to save the CDF comparison plot.
        gue_loc: Location parameter for GUE distribution.
        gue_scale: Scale parameter for GUE distribution.
    """
    logger.info(f"Starting KS test pipeline with window size {window_size}")
    
    # Load data
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
        
    primes_before, primes_after, gaps, normalized_gaps = load_primes_gaps(input_file)
    logger.info(f"Loaded {len(gaps)} prime gaps")
    
    # Extract maximal gaps in windows
    maximal_gaps = extract_maximal_gaps_in_windows(primes_before, gaps, window_size)
    logger.info(f"Extracted {len(maximal_gaps)} maximal gaps from windows")
    
    # Normalize maximal gaps
    normalized_maximal_gaps = normalize_maximal_gaps(maximal_gaps, primes_before, window_size)
    logger.info(f"Normalized {len(normalized_maximal_gaps)} maximal gaps")
    
    # Perform KS test
    ks_results = run_ks_test(
        normalized_maximal_gaps, 
        gue_extreme_value_cdf, 
        loc=gue_loc, 
        scale=gue_scale
    )
    logger.info(f"KS test completed: statistic={ks_results['ks_statistic']:.4f}, p-value={ks_results['p_value']:.4f}")
    
    # Generate plot
    plot_cdf_comparison(
        normalized_maximal_gaps,
        gue_extreme_value_cdf,
        loc=gue_loc,
        scale=gue_scale,
        output_path=output_plot
    )
    
    # Save results
    results = {
        "window_size": window_size,
        "ks_statistic": ks_results["ks_statistic"],
        "p_value": ks_results["p_value"],
        "sample_size": ks_results["n"],
        "gue_parameters": {"loc": gue_loc, "scale": gue_scale},
        "input_file": input_file,
        "output_plot": output_plot
    }
    
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_json}")
    return results

if __name__ == "__main__":
    # Example usage
    results = run_pipeline()
    print(json.dumps(results, indent=2))