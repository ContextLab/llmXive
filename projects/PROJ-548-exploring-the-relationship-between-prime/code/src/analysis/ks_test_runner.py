"""
Kolmogorov-Smirnov Test Runner for Prime Gap vs GUE Extreme Value Distribution.

This module implements T022: Perform KS test comparing empirical maximal gap distribution
against the GUE theoretical extreme value distribution.

Output: results/ks_test_results.json
"""
import os
import sys
import json
import math
import logging
import numpy as np
from scipy import stats
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Input/Output paths
INPUT_MAXIMAL_GAPS_FILE = DATA_PROCESSED_DIR / "maximal_gaps.csv"
OUTPUT_KS_RESULTS_FILE = RESULTS_DIR / "ks_test_results.json"

def ensure_directories():
    """Ensure output directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories: {RESULTS_DIR}")

def load_maximal_gaps(filepath: Path) -> np.ndarray:
    """
    Load normalized maximal gaps from CSV.
    Expects columns: window_start, window_end, max_gap, normalized_max_gap
    Returns: numpy array of normalized_max_gap values.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    logger.info(f"Loading maximal gaps from {filepath}")
    gaps = []
    with open(filepath, 'r') as f:
        header = f.readline().strip().split(',')
        # Find index of normalized_max_gap
        if 'normalized_max_gap' not in header:
            raise ValueError(f"Column 'normalized_max_gap' not found in {filepath}. Headers: {header}")
        
        idx = header.index('normalized_max_gap')
        
        for line_num, line in enumerate(f, start=2):
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            try:
                val = float(parts[idx])
                if not math.isnan(val) and not math.isinf(val):
                    gaps.append(val)
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping malformed line {line_num}: {line} - {e}")
    
    if not gaps:
        raise ValueError(f"No valid normalized_max_gap values found in {filepath}")
    
    logger.info(f"Loaded {len(gaps)} normalized maximal gaps")
    return np.array(gaps)

def load_theoretical_samples(n_samples: int = 10000, seed: int = 42) -> np.ndarray:
    """
    Generate samples from the GUE Extreme Value Distribution (Tracy-Widom beta=2).
    Since scipy.stats.tracy_widom provides the CDF, we use inverse transform sampling
    or direct sampling if available. scipy.stats.tracy_widom has a .rvs method.
    
    We generate samples to perform ks_2samp (two-sample KS test) as requested.
    """
    logger.info(f"Generating {n_samples} theoretical samples from GUE Tracy-Widom (beta=2)")
    try:
        # scipy.stats.tracy_widom supports rvs
        tw_dist = stats.tracy_widom(b=2)
        samples = tw_dist.rvs(size=n_samples, random_state=seed)
        logger.info(f"Generated theoretical samples: min={samples.min():.4f}, max={samples.max():.4f}, mean={samples.mean():.4f}")
        return samples
    except Exception as e:
        logger.error(f"Failed to generate Tracy-Widom samples: {e}")
        raise

def perform_ks_test(empirical_data: np.ndarray, theoretical_data: np.ndarray) -> dict:
    """
    Perform Kolmogorov-Smirnov two-sample test.
    
    Returns dict with:
    - ks_statistic: float
    - p_value: float
    - distribution_compared: "GUE_EVF"
    - method: "scipy.stats.ks_2samp"
    """
    logger.info("Performing KS-2samp test...")
    
    if len(empirical_data) == 0 or len(theoretical_data) == 0:
        raise ValueError("Cannot perform KS test on empty data")
    
    # Use scipy.stats.ks_2samp
    statistic, pvalue = stats.ks_2samp(empirical_data, theoretical_data)
    
    result = {
        "ks_statistic": float(statistic),
        "p_value": float(pvalue),
        "distribution_compared": "GUE_EVF",
        "method": "scipy.stats.ks_2samp",
        "empirical_sample_size": len(empirical_data),
        "theoretical_sample_size": len(theoretical_data)
    }
    
    logger.info(f"KS Test Result: Statistic={statistic:.6f}, P-value={pvalue:.6f}")
    return result

def write_results(results: dict, filepath: Path):
    """Write results to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results written to {filepath}")

def run_pipeline():
    """Main pipeline execution for T022."""
    ensure_directories()
    
    # Load empirical data (from T020/T018b)
    try:
        empirical_gaps = load_maximal_gaps(INPUT_MAXIMAL_GAPS_FILE)
    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        logger.error("Please ensure T018b has run and generated data/processed/maximal_gaps.csv")
        raise
    
    # Generate theoretical samples (from T021b logic)
    theoretical_samples = load_theoretical_samples(n_samples=10000)
    
    # Perform KS test
    results = perform_ks_test(empirical_gaps, theoretical_samples)
    
    # Write output
    write_results(results, OUTPUT_KS_RESULTS_FILE)
    
    logger.info("T022 Pipeline completed successfully.")
    return results

def main():
    """Entry point."""
    try:
        run_pipeline()
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()