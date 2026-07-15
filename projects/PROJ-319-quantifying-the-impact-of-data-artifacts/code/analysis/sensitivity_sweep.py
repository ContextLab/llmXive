"""
T024: Implement sensitivity analysis sweep for saturation-induced bias on asymmetry.

This script performs a sensitivity analysis by iterating over saturation levels
defined in config.py (0.0 to 0.5 in 0.05 increments), injecting saturation into
synthetic planetary nebulae, measuring asymmetry, and computing statistical summaries.

Output:
    data/processed/saturation_sweep.csv: Contains [saturation_fraction, asymmetry_mean, asymmetry_std]
    logs/sensitivity_summary.json: Statistical summary verifying p < 0.05 and monotonic trends.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from scipy import stats

# Import from project API
from code.config import get_project_root, SATURATION_LEVELS, SEED
from code.synthetic.generator import generate_synthetic_nebula
from code.synthetic.artifacts import clip_saturation
from code.metrics.asymmetry import calculate_asymmetry
from code.io.writer import save_metadata_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(get_project_root()) / 'logs' / 'sensitivity_sweep.log')
    ]
)
logger = logging.getLogger(__name__)

def run_sensitivity_sweep() -> Tuple[List[Dict[str, float]], Dict[str, Any]]:
    """
    Run the saturation sensitivity sweep.

    Returns:
        results: List of dicts with saturation_fraction, asymmetry_mean, asymmetry_std
        summary: Statistical summary dict
    """
    logger.info(f"Starting sensitivity sweep with {len(SATURATION_LEVELS)} saturation levels.")
    logger.info(f"Saturation levels: {SATURATION_LEVELS}")

    rng = np.random.default_rng(SEED)
    results = []

    # Generate a clean base image once (ground truth is constant)
    # Using a single seed for the base image to ensure consistency across the sweep
    base_image = generate_synthetic_nebula(seed=SEED)
    logger.info(f"Generated base synthetic nebula with shape {base_image.shape}")

    # Store asymmetry measurements for statistical testing
    all_asymmetries = []
    saturation_fractions = []

    for sat_level in SATURATION_LEVELS:
        logger.info(f"Processing saturation level: {sat_level:.2f}")

        # Inject saturation
        # clip_saturation expects (image, saturation_fraction)
        saturated_image = clip_saturation(base_image.copy(), sat_level)

        # Calculate asymmetry
        # calculate_asymmetry returns (asymmetry_value, center_x, center_y)
        asymmetry_val, _, _ = calculate_asymmetry(saturated_image)

        results.append({
            'saturation_fraction': sat_level,
            'asymmetry_mean': asymmetry_val,
            'asymmetry_std': 0.0  # Single measurement per level in this sweep design
        })

        # For statistical testing, we need multiple samples per level
        # To satisfy the "monotonic trend" and "p < 0.05" requirement robustly,
        # we will generate N=30 independent samples for each saturation level
        # to perform a proper trend analysis or t-test against baseline.
        # However, the task description implies a sweep over levels.
        # Let's refine: The task asks for a CSV with mean/std.
        # To get a meaningful std, we must repeat the measurement.
        
        # Re-run with Monte Carlo for this level to get std and p-value
        n_samples = 30
        sample_asymmetries = []
        for _ in range(n_samples):
            # Regenerate base image with varying noise to simulate observational variance
            # OR keep base image constant and vary noise? 
            # The task is about SATURATION bias. We should keep the underlying object constant
            # but vary the noise realization to get a distribution of asymmetry measurements.
            # However, clip_saturation is deterministic given the image.
            # To get a std, we need to vary the input image (noise).
            noisy_base = generate_synthetic_nebula(seed=int(SEED + _ * 1000)) # Vary seed
            sat_img = clip_saturation(noisy_base, sat_level)
            asym, _, _ = calculate_asymmetry(sat_img)
            sample_asymmetries.append(asym)

        mean_asym = float(np.mean(sample_asymmetries))
        std_asym = float(np.std(sample_asymmetries))
        
        # Update the result for this level with proper statistics
        results[-1]['asymmetry_mean'] = mean_asym
        results[-1]['asymmetry_std'] = std_asym

        saturation_fractions.append(sat_level)
        all_asymmetries.append(sample_asymmetries)

    # Statistical Summary Generation
    summary = {
        'sweep_parameters': {
            'min_saturation': min(SATURATION_LEVELS),
            'max_saturation': max(SATURATION_LEVELS),
            'step': 0.05,
            'n_samples_per_level': 30
        },
        'monotonicity_check': False,
        'significance_check': False,
        'p_value_baseline_vs_max': None,
        'trend_direction': None
    }

    # 1. Check Monotonicity
    means = [r['asymmetry_mean'] for r in results]
    is_monotonic = all(means[i] <= means[i+1] for i in range(len(means)-1))
    # Allow small floating point tolerance
    is_monotonic = all(means[i] <= means[i+1] + 1e-6 for i in range(len(means)-1))
    summary['monotonicity_check'] = is_monotonic
    summary['trend_direction'] = "increasing" if is_monotonic else "non-monotonic"
    logger.info(f"Monotonicity check: {is_monotonic} (Trend: {summary['trend_direction']})")

    # 2. Significance Check (t-test: Baseline vs Max Saturation)
    if len(all_asymmetries) >= 2:
        baseline_samples = all_asymmetries[0] # Saturation 0.0
        max_sat_samples = all_asymmetries[-1] # Saturation 0.5
        
        t_stat, p_val = stats.ttest_ind(baseline_samples, max_sat_samples)
        summary['p_value_baseline_vs_max'] = float(p_val)
        summary['significance_check'] = p_val < 0.05
        
        logger.info(f"T-test (0.0 vs 0.5): t={t_stat:.4f}, p={p_val:.4f}")
        logger.info(f"Significance (p < 0.05): {summary['significance_check']}")

    return results, summary

def save_results(results: List[Dict[str, float]], summary: Dict[str, Any]) -> None:
    """Save results to CSV and summary to JSON."""
    root = get_project_root()
    processed_dir = Path(root) / 'data' / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)

    csv_path = processed_dir / 'saturation_sweep.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['saturation_fraction', 'asymmetry_mean', 'asymmetry_std'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved sweep results to {csv_path}")

    # Save summary
    summary_path = Path(root) / 'logs' / 'sensitivity_summary.json'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved statistical summary to {summary_path}")

def main():
    """Entry point for the sensitivity sweep."""
    try:
        results, summary = run_sensitivity_sweep()
        save_results(results, summary)
        
        # Final verification
        if not summary['significance_check']:
            logger.warning("Statistical significance (p < 0.05) was NOT achieved.")
        if not summary['monotonicity_check']:
            logger.warning("Monotonic trend was NOT observed.")
        
        logger.info("Sensitivity analysis sweep completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity sweep failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()