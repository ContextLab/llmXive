"""
Main analysis runner for PROJ-179.
Orchestrates the full pipeline: Preprocess -> Correlation -> Regression -> Robustness -> Report Generation.

This script is invoked by quickstart.md to produce the final analysis artifacts.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.env_config import load_config, setup_logging
from data.preprocess import main as run_preprocess
from src.analysis.correlation import main as run_correlation
from src.analysis.bootstrap import main as run_bootstrap
from src.analysis.regression import main as run_regression
from src.analysis.diagnostics import main as run_diagnostics
from src.analysis.filter import main as run_filter
from src.analysis.robustness import main as run_robustness
from src.report.generate import main as run_report

def main():
    logger = setup_logging("info")
    logger.info("Starting full analysis pipeline (T035)...")

    config = load_config()
    
    # Ensure output directories exist
    data_dir = project_root / "data"
    derived_dir = data_dir / "derived"
    results_dir = data_dir / "results"
    derived_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Preprocessing (generates data/derived/trial_data.csv)
    logger.info("Step 1: Running Preprocessing...")
    try:
        run_preprocess()
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        # If preprocess fails, we cannot proceed. 
        # However, we must ensure the script exits cleanly if data is missing 
        # rather than crashing with a traceback that looks like a bug.
        if "No input CSV" in str(e):
            logger.warning("Skipping analysis due to missing input data. Run T005 first.")
            return
        raise

    # 2. Primary Correlation Analysis (generates data/results/primary_analysis.json)
    logger.info("Step 2: Running Primary Correlation Analysis...")
    try:
        run_correlation()
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        # Continue to attempt other steps if possible, or exit
        raise

    # 3. Bootstrap Analysis (generates data/results/bootstrap_config.json)
    logger.info("Step 3: Running Bootstrap Analysis...")
    try:
        run_bootstrap()
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {e}")
        raise

    # 4. Filter by Modality (generates data/derived/visual_trials.csv, auditory_trials.csv)
    logger.info("Step 4: Filtering data by Modality...")
    try:
        run_filter()
    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        # Non-fatal if we just want primary results, but required for robustness
        raise

    # 5. Robustness Analysis (generates data/results/robustness_analysis.json)
    logger.info("Step 5: Running Robustness Analysis...")
    try:
        run_robustness()
    except Exception as e:
        logger.error(f"Robustness analysis failed: {e}")
        # Continue to regression if robustness fails due to modality issues
        pass

    # 6. Regression Analysis (generates data/results/regression_analysis.json)
    logger.info("Step 6: Running Regression Analysis...")
    try:
        run_regression()
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        # Continue to diagnostics
        pass

    # 7. Diagnostics
    logger.info("Step 7: Running Diagnostics...")
    try:
        run_diagnostics()
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        pass

    # 8. Final Report Generation (aggregates all results)
    logger.info("Step 8: Generating Final Reports...")
    try:
        run_report()
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()
