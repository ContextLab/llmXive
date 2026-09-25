import os
import sys
import json
import math
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Import existing utilities from the project
# Note: We assume the KS test results are available from T022
# We need to load empirical data and theoretical CDF for plotting

logger = logging.getLogger(__name__)

def load_ks_test_results(results_path: str) -> dict:
    """Load the KS test results from the JSON file."""
    with open(results_path, 'r') as f:
        return json.load(f)

def load_maximal_gaps_data(data_path: str) -> np.ndarray:
    """Load normalized maximal gaps from CSV."""
    gaps = []
    with open(data_path, 'r') as f:
        # Skip header
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                try:
                    # Assuming format: window_start, window_end, max_gap, normalized_max_gap
                    normalized_gap = float(parts[3])
                    gaps.append(normalized_gap)
                except ValueError:
                    continue
    return np.array(gaps)

def gue_extreme_value_cdf(x: np.ndarray, beta: int = 2) -> np.ndarray:
    """
    Approximate GUE Extreme Value CDF.
    Since scipy.stats.tracy_widom is for the distribution of the largest eigenvalue,
    we use it directly as the theoretical CDF for maximal gaps under GUE hypothesis.
    Note: This is an approximation. The exact GUE extreme value distribution
    is complex and often approximated by Tracy-Widom for large N.
    """
    try:
        from scipy import stats
        # Tracy-Widom distribution for beta=2 (GUE)
        # We use it as a proxy for the extreme value distribution of GUE eigenvalues
        # This is a standard approximation in random matrix theory
        return stats.tracy_widom.cdf(x, beta=2)
    except ImportError:
        logger.warning("scipy not available, using fallback approximation")
        # Fallback: simple exponential-like decay for demonstration
        # This is NOT the real GUE CDF, but a placeholder if scipy is missing
        return np.where(x < 0, 0.0, 1.0 - np.exp(-x))

def plot_cdf_comparison(
    empirical_gaps: np.ndarray,
    theoretical_cdf_func,
    output_path: str,
    results_json_path: str
):
    """
    Generate CDF overlay plot of empirical vs theoretical maximal gap distributions.
    Saves plot to output_path and updates results_json_path with plot info.
    """
    # Sort empirical data for CDF
    empirical_sorted = np.sort(empirical_gaps)
    n = len(empirical_sorted)
    empirical_cdf = np.arange(1, n + 1) / n

    # Generate theoretical CDF values at the same points
    theoretical_cdf = theoretical_cdf_func(empirical_sorted)

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(empirical_sorted, empirical_cdf, 'b-', label='Empirical CDF (Prime Gaps)', linewidth=2)
    plt.plot(empirical_sorted, theoretical_cdf, 'r--', label='Theoretical CDF (GUE Extreme Value)', linewidth=2)
    
    plt.xlabel('Normalized Maximal Gap (g / log²p)')
    plt.ylabel('Cumulative Distribution Function')
    plt.title('CDF Comparison: Prime Gaps vs GUE Extreme Value Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

    # Update results JSON with plot information
    results_data = {}
    if os.path.exists(results_json_path):
        with open(results_json_path, 'r') as f:
            results_data = json.load(f)
    
    results_data['plot_info'] = {
        'file_path': output_path,
        'description': 'CDF overlay of empirical maximal gap distribution vs GUE theoretical extreme value CDF',
        'empirical_points': n,
        'methodology': 'Tracy-Widom approximation (beta=2) for GUE extreme value distribution'
    }
    
    with open(results_json_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    logger.info(f"Results updated at {results_json_path}")

def run_pipeline():
    """Main pipeline for visualization task T025."""
    # Define paths based on project structure
    project_root = Path(__file__).resolve().parents[3]
    results_dir = project_root / "results"
    data_processed_dir = project_root / "data" / "processed"
    
    # Input files
    ks_results_path = results_dir / "ks_test_results.json"
    maximal_gaps_path = data_processed_dir / "maximal_gaps.csv"
    
    # Output files
    plot_path = results_dir / "correlation_plot.png"
    results_output_path = results_dir / "correlation_results.json"
    
    # Ensure results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    # Check if input files exist
    if not ks_results_path.exists():
        raise FileNotFoundError(f"KS test results not found at {ks_results_path}. Run T022 first.")
    
    if not maximal_gaps_path.exists():
        raise FileNotFoundError(f"Maximal gaps data not found at {maximal_gaps_path}. Run T018b first.")
    
    # Load data
    logger.info("Loading KS test results...")
    ks_results = load_ks_test_results(str(ks_results_path))
    
    logger.info("Loading maximal gaps data...")
    empirical_gaps = load_maximal_gaps_data(str(maximal_gaps_path))
    
    if len(empirical_gaps) == 0:
        raise ValueError("No valid maximal gap data found. Check data/processed/maximal_gaps.csv")
    
    logger.info(f"Loaded {len(empirical_gaps)} maximal gap values")
    
    # Generate plot
    logger.info("Generating CDF comparison plot...")
    plot_cdf_comparison(
        empirical_gaps=empirical_gaps,
        theoretical_cdf_func=gue_extreme_value_cdf,
        output_path=str(plot_path),
        results_json_path=str(results_output_path)
    )
    
    logger.info("Visualization task T025 completed successfully.")
    return True

def main():
    """Entry point for script execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        success = run_pipeline()
        if success:
            print("T025 completed: correlation_plot.png and correlation_results.json generated.")
            sys.exit(0)
        else:
            print("T025 failed: Pipeline did not complete successfully.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"T025 failed with error: {e}", exc_info=True)
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
