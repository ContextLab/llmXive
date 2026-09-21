"""
Task T022: Perform Kolmogorov-Smirnov (KS) test comparing empirical maximal gap
distribution against GUE theoretical extreme value distribution and pair-correlation
distribution.

Reads:
  - data/processed/maximal_gaps_normalized.csv (from T020)
  - data/results/gue_cdf_samples.csv (from T021b)
  - data/results/pc_distribution_samples.csv (from T021c)

Writes:
  - results/ks_test_results.json
"""

import os
import sys
import json
import math
import logging
import numpy as np
from scipy import stats
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.distribution_test import compute_empirical_cdf, gue_extreme_value_cdf, pair_correlation_distribution
from src.utils.config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_maximal_gaps(filepath: str) -> np.ndarray:
    """
    Load normalized maximal gaps from CSV file.
    Expected format: prime_before, gap_size, normalized_gap
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Maximal gaps file not found: {filepath}")

    gaps = []
    with open(filepath, 'r') as f:
        header = f.readline()  # Skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                try:
                    normalized_gap = float(parts[2])
                    if not math.isnan(normalized_gap) and not math.isinf(normalized_gap):
                        gaps.append(normalized_gap)
                except ValueError:
                    continue

    if not gaps:
        raise ValueError("No valid data found in maximal gaps file")

    logger.info(f"Loaded {len(gaps)} normalized maximal gaps from {filepath}")
    return np.array(gaps)

def load_theoretical_samples(filepath: str) -> np.ndarray:
    """
    Load theoretical distribution samples from CSV file.
    Expected format: value, probability (or just value if generated from CDF)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Theoretical samples file not found: {filepath}")

    values = []
    with open(filepath, 'r') as f:
        header = f.readline()  # Skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 1:
                try:
                    val = float(parts[0])
                    if not math.isnan(val) and not math.isinf(val):
                        values.append(val)
                except ValueError:
                    continue

    if not values:
        raise ValueError("No valid data found in theoretical samples file")

    logger.info(f"Loaded {len(values)} theoretical samples from {filepath}")
    return np.array(values)

def perform_ks_test(empirical_data: np.ndarray, theoretical_data: np.ndarray, test_name: str) -> dict:
    """
    Perform Kolmogorov-Smirnov test between empirical and theoretical distributions.
    """
    try:
        # scipy.stats.ks_2samp performs the two-sample KS test
        ks_statistic, p_value = stats.ks_2samp(empirical_data, theoretical_data)

        result = {
            "test_name": test_name,
            "ks_statistic": float(ks_statistic),
            "p_value": float(p_value),
            "empirical_sample_size": len(empirical_data),
            "theoretical_sample_size": len(theoretical_data),
            "interpretation": "reject_null" if p_value < 0.05 else "fail_to_reject_null"
        }

        logger.info(f"KS Test '{test_name}': statistic={ks_statistic:.6f}, p-value={p_value:.6f}")
        return result

    except Exception as e:
        logger.error(f"Error performing KS test for {test_name}: {e}")
        raise

def run_pipeline():
    """
    Main pipeline for Task T022: Perform KS tests comparing empirical maximal gaps
    against GUE and pair-correlation theoretical distributions.
    """
    # Ensure output directories exist
    ensure_directories()

    # Define file paths
    empirical_file = str(project_root / "data" / "processed" / "maximal_gaps_normalized.csv")
    gue_samples_file = str(project_root / "data" / "results" / "gue_cdf_samples.csv")
    pc_samples_file = str(project_root / "data" / "results" / "pc_distribution_samples.csv")
    output_file = str(project_root / "results" / "ks_test_results.json")

    logger.info(f"Starting KS Test Pipeline (Task T022)")
    logger.info(f"Empirical data: {empirical_file}")
    logger.info(f"GUE samples: {gue_samples_file}")
    logger.info(f"Pair-correlation samples: {pc_samples_file}")

    # Load empirical data
    try:
        empirical_gaps = load_maximal_gaps(empirical_file)
    except Exception as e:
        logger.error(f"Failed to load empirical data: {e}")
        raise

    # Load GUE theoretical samples
    try:
        gue_samples = load_theoretical_samples(gue_samples_file)
    except Exception as e:
        logger.error(f"Failed to load GUE samples: {e}")
        raise

    # Load Pair-Correlation theoretical samples
    try:
        pc_samples = load_theoretical_samples(pc_samples_file)
    except Exception as e:
        logger.error(f"Failed to load Pair-Correlation samples: {e}")
        raise

    # Perform KS tests
    results = {
        "pipeline": "T022_KS_Test",
        "status": "completed",
        "timestamp": "2026-01-01T00:00:00Z",  # Placeholder, real implementation would use datetime
        "tests": []
    }

    # Test 1: Empirical vs GUE Extreme Value Distribution
    logger.info("Performing KS test: Empirical vs GUE Extreme Value Distribution")
    try:
        gue_result = perform_ks_test(empirical_gaps, gue_samples, "Empirical_vs_GUE")
        results["tests"].append(gue_result)
    except Exception as e:
        results["tests"].append({
            "test_name": "Empirical_vs_GUE",
            "status": "failed",
            "error": str(e)
        })

    # Test 2: Empirical vs Pair-Correlation Distribution
    logger.info("Performing KS test: Empirical vs Pair-Correlation Distribution")
    try:
        pc_result = perform_ks_test(empirical_gaps, pc_samples, "Empirical_vs_PairCorrelation")
        results["tests"].append(pc_result)
    except Exception as e:
        results["tests"].append({
            "test_name": "Empirical_vs_PairCorrelation",
            "status": "failed",
            "error": str(e)
        })

    # Save results
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise

    return results

def main():
    """
    Entry point for the KS test runner.
    """
    try:
        results = run_pipeline()
        print(json.dumps(results, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())