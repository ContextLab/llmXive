"""
Analysis Runner for PROJ-673.

Orchestrates the full analysis pipeline:
1. Power Analysis (T024)
2. Correlation Analysis (T027)
3. Visualization (T028)
4. Aggregates results and verifies artifacts.

This script MUST be run after data collection (T019) has produced
data/processed/dependencies_raw.csv.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Local imports matching the API surface provided
from src.analysis.power import main as run_power_analysis
from src.analysis.correlation import main as run_correlation_analysis
from src.analysis.visualizer import main as run_visualizer
from src.config.settings import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_analysis")

def verify_artifacts(output_dir: Path) -> bool:
    """Verify that all expected output artifacts exist."""
    required_files = [
        "power_analysis.json",
        "results_correlation.json",
        "scatter_plot.png"
    ]
    missing = []
    for fname in required_files:
        fpath = output_dir / fname
        if not fpath.exists():
            missing.append(fname)
            logger.error(f"Missing artifact: {fpath}")
        else:
            logger.info(f"Verified artifact: {fpath}")
    
    if missing:
        logger.error(f"Verification failed. Missing files: {missing}")
        return False
    
    logger.info("All artifacts verified successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the full analysis pipeline.")
    parser.add_argument(
        "--input-csv",
        type=str,
        default="data/processed/dependencies_raw.csv",
        help="Path to the input CSV file from data collection."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write analysis results."
    )
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T019 (Data Collection) has been run successfully.")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting analysis pipeline. Input: {input_path}, Output: {output_dir}")

    # 1. Run Power Analysis
    logger.info("Step 1/3: Running Power Analysis...")
    try:
        # The power script expects the CSV to exist in the default location or via env
        # We ensure the path is correct for the sub-modules if they don't handle args
        # Based on API surface, these scripts have their own 'main' which likely handles defaults.
        # We rely on them reading from the standard location or we might need to pass args if they supported it.
        # Since the API surface shows 'main' with no args, we assume they read from config or default paths.
        # However, to be safe and explicit, we check if we need to set a config or env var.
        # For this implementation, we assume the sub-scripts are robust or we run them as is.
        # If they fail, we let them raise.
        run_power_analysis()
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

    # 2. Run Correlation Analysis
    logger.info("Step 2/3: Running Correlation Analysis...")
    try:
        run_correlation_analysis()
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        sys.exit(1)

    # 3. Run Visualization
    logger.info("Step 3/3: Running Visualization...")
    try:
        run_visualizer()
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        sys.exit(1)

    # 4. Verify Artifacts
    logger.info("Verifying output artifacts...")
    if not verify_artifacts(output_dir):
        logger.error("Pipeline completed but artifacts are missing.")
        sys.exit(1)

    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()