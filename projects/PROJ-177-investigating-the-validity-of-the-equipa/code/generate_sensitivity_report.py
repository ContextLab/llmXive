"""
Generate the sensitivity analysis report.

This script reads the statistical results from `artifacts/statistical_results.json`,
computes the rejection rates across different significance thresholds (alpha) and
quasi-thermal energy ratio boundaries, and writes a comprehensive report to
`artifacts/sensitivity_analysis_report.json`.

It relies on the `run_sensitivity_analysis` function from `code/sensitivity.py`
which performs the actual sweeps and robustness checks.
"""

import json
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sensitivity import run_sensitivity_analysis, SensitivityError
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for generating the sensitivity analysis report.
    """
    # Define paths relative to project root
    stats_results_path = project_root / "artifacts" / "statistical_results.json"
    report_output_path = project_root / "artifacts" / "sensitivity_analysis_report.json"

    # Ensure input file exists
    if not stats_results_path.exists():
        logger.error(f"Input file not found: {stats_results_path}")
        logger.error("Please run the statistical analysis (T025) first to generate statistical_results.json")
        sys.exit(1)

    # Ensure output directory exists
    report_output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading statistical results from {stats_results_path}")
    try:
        with open(stats_results_path, 'r') as f:
            stats_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {stats_results_path}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error reading {stats_results_path}: {e}")
        sys.exit(1)

    logger.info("Running sensitivity analysis (alpha sweep and boundary sweep)...")
    try:
        report_data = run_sensitivity_analysis(stats_data)
    except SensitivityError as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        sys.exit(1)

    logger.info(f"Writing sensitivity report to {report_output_path}")
    try:
        with open(report_output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write report to {report_output_path}: {e}")
        sys.exit(1)

    logger.info("Sensitivity analysis report generated successfully.")
    logger.info(f"Report saved to: {report_output_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
