"""
Main entry point for the Resting-State fMRI Global Signal analysis pipeline.

This orchestrator runs the full workflow:
1. Ingestion (creates `data/processed/cleaned_data.csv`)
2. Modeling (ridge regression, null distribution)
3. Diagnostics
4. Robustness analysis
5. Visualisations
6. Final report generation

The script exits with status 0 on success and logs progress to
`data/logs/pipeline.log`.
"""

import sys
import logging
from pathlib import Path

# Ensure project root is on the import path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils import get_logger, setup_logging

# Pipeline step imports
from run_ingestion_pipeline import main as run_ingestion
from modeling import main as run_modeling
from diagnostics import main as run_diagnostics
from robustness import main as run_robustness
from visualizations import main as run_visualizations
from run_final_report import main as run_final_report


def main() -> None:
    """Execute the full analysis pipeline."""
    # Initialise logging early so that all steps record to the same file.
    setup_logging()
    logger = get_logger("main")

    logger.info("=== Starting Resting‑State fMRI Global Signal Pipeline ===")

    # ------------------------------------------------------------------
    # Ensure directory structure exists
    # ------------------------------------------------------------------
    ensure_directories()
    logger.info("Project directories verified/created.")

    # ------------------------------------------------------------------
    # Step 1 – Data ingestion
    # ------------------------------------------------------------------
    logger.info("Step 1/6: Data ingestion")
    try:
        run_ingestion()
        logger.info("✅ Ingestion completed")
    except Exception as exc:
        logger.error(f"❌ Ingestion failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2 – Modeling
    # ------------------------------------------------------------------
    logger.info("Step 2/6: Modeling")
    try:
        run_modeling()
        logger.info("✅ Modeling completed")
    except Exception as exc:
        logger.error(f"❌ Modeling failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 3 – Diagnostics
    # ------------------------------------------------------------------
    logger.info("Step 3/6: Collinearity diagnostics")
    try:
        run_diagnostics()
        logger.info("✅ Diagnostics completed")
    except Exception as exc:
        logger.error(f"❌ Diagnostics failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 4 – Robustness analysis
    # ------------------------------------------------------------------
    logger.info("Step 4/6: Robustness analysis")
    try:
        run_robustness()
        logger.info("✅ Robustness analysis completed")
    except Exception as exc:
        logger.error(f"❌ Robustness analysis failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 5 – Visualisations
    # ------------------------------------------------------------------
    logger.info("Step 5/6: Generating visualisations")
    try:
        run_visualizations()
        logger.info("✅ Visualisations completed")
    except Exception as exc:
        logger.error(f"❌ Visualisations failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 6 – Final report
    # ------------------------------------------------------------------
    logger.info("Step 6/6: Final report aggregation")
    try:
        run_final_report()
        logger.info("✅ Final report generated")
    except Exception as exc:
        logger.error(f"❌ Final report generation failed: {exc}")
        sys.exit(1)

    logger.info("=== Pipeline finished successfully ===")
    logger.info("Results are available under `data/results/`")


if __name__ == "__main__":
    main()
