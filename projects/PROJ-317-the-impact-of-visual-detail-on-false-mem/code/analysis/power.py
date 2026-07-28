"""
Power Analysis Script for PROJ-317.

This script executes the power analysis calculation defined in T012.
It calculates the required sample size for a Repeated-Measures ANOVA
and writes the results to data/analysis/power_report.json.

It is the executable entry point referenced by the quickstart run-book.
"""
import json
import logging
import sys
from pathlib import Path

# Add project root to path if not already present (for local execution)
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_project_root, get_data_dir, get_effect_size, get_alpha_level, get_power_target
from analysis.stats import calculate_anova_power, save_power_analysis
from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

def main():
    """
    Execute power analysis and save results to data/analysis/power_report.json.
    """
    # Setup logging
    setup_logging()
    logger.info("Starting Power Analysis (T073/T012 implementation)...")

    try:
        # Retrieve configuration parameters
        # These are derived from T012.0 documentation: f=0.25, alpha=0.05, power=0.80
        effect_size = get_effect_size()  # Should be 0.25
        alpha = get_alpha_level()        # Should be 0.05
        power = get_power_target()       # Should be 0.80

        logger.info(f"Parameters: effect_size={effect_size}, alpha={alpha}, power={power}")

        # Perform calculation
        # This wraps the logic in stats.py: FTestAnovaPower().solve_power(...)
        result = calculate_anova_power(effect_size=effect_size, alpha=alpha, power=power)

        if result is None:
            logger.error("Power calculation failed to converge.")
            sys.exit(1)

        # Save results to the declared output path
        data_dir = get_data_dir()
        output_path = data_dir / "analysis" / "power_report.json"
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        save_power_analysis(result, output_path)

        logger.info(f"Power analysis complete. Results written to: {output_path}")
        logger.info(f"  - N per group: {result['n_per_group']}")
        logger.info(f"  - Total N: {result['total_n']}")
        logger.info(f"  - Power Insufficient: {result['power_insufficient']}")

        return 0

    except Exception as e:
        logger.exception(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
