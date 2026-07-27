"""
Script to run gradient stability analysis comparing baseline and microcircuit models.

This script executes the KS test between baseline and microcircuit gradient norms
and outputs the results to data/results/gradient_stability.json.
"""
import os
import sys
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.statistics import compare_gradient_stability

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run gradient stability analysis."""
    baseline_path = os.path.join(project_root, 'data/logs/gradient_norms.json')
    microcircuit_path = os.path.join(project_root, 'data/logs/gradient_norms_microcircuit.json')
    output_path = os.path.join(project_root, 'data/results/gradient_stability.json')

    # Verify input files exist
    if not os.path.exists(baseline_path):
        logger.error(f"Baseline gradient norms not found: {baseline_path}")
        logger.error("Run baseline training first to generate gradient norms")
        sys.exit(1)

    if not os.path.exists(microcircuit_path):
        logger.error(f"Microcircuit gradient norms not found: {microcircuit_path}")
        logger.error("Run microcircuit training first to generate gradient norms")
        sys.exit(1)

    logger.info("Starting gradient stability analysis...")
    logger.info(f"Baseline norms: {baseline_path}")
    logger.info(f"Microcircuit norms: {microcircuit_path}")
    logger.info(f"Output: {output_path}")

    result = compare_gradient_stability(baseline_path, microcircuit_path, output_path)

    logger.info("Analysis complete!")
    logger.info(f"KS Statistic: {result['ks_statistic']:.4f}")
    logger.info(f"P-value: {result['p_value']:.4f}")
    logger.info(f"Stable: {result['stable']}")

    return result

if __name__ == "__main__":
    main()
