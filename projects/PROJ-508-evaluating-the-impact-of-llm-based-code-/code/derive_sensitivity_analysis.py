"""
Task T041: Generate sensitivity analysis results by sweeping iteration_count thresholds.

This script loads the analysis results from T040, performs a sensitivity sweep
over low integer values of `iteration_count`, and saves the results to
`data/derived/sensitivity_analysis.json`.

It relies on the `run_sensitivity_analysis` function exported from `code/analyze.py`.
"""
import json
import logging
from pathlib import Path

# Import the core analysis logic from the existing analyze module
# The API surface confirms run_sensitivity_analysis is available here.
from analyze import run_sensitivity_analysis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "derived" / "analysis_results.json"
    output_path = project_root / "data" / "derived" / "sensitivity_analysis.json"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T040 (Generate analysis_results.json) is completed first.")
        return 1

    logger.info(f"Loading analysis results from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        analysis_data = json.load(f)

    logger.info("Running sensitivity analysis sweep on iteration_count thresholds...")
    # The analyze module's run_sensitivity_analysis handles the logic of:
    # 1. Loading the master dataset (internally or via passed context)
    # 2. Iterating over a range of low integer thresholds for iteration_count
    # 3. Re-running the core model logic for each threshold
    # 4. Collecting effect estimates and statistics
    sensitivity_results = run_sensitivity_analysis(analysis_data)

    if not sensitivity_results:
        logger.warning("Sensitivity analysis returned empty results.")

    logger.info(f"Writing sensitivity analysis results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sensitivity_results, f, indent=2)

    logger.info("Sensitivity analysis complete.")
    return 0

if __name__ == "__main__":
    exit(main())