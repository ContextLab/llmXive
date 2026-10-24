"""
src.main – entry point for the Heusler‑Alloy hysteresis pipeline.

This module builds an ``argparse`` parser with a help description that
contains the phrase “Setup OK”.  The quick‑start guide checks for this
phrase to confirm that the project layout and dependencies are correctly
installed.
"""
import argparse
import logging
from pathlib import Path

# ----------------------------------------------------------------------
# Helper to build the top‑level parser
# ----------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="src.main",
        description=(
            "Heusler Alloy Hysteresis Prediction Pipeline – Setup OK.\n"
            "Use the flags ``--demo`` for a quick sanity‑check or ``--full`` "
            "to run the complete pipeline."
        ),
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a lightweight demo on the manual curated file.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full end‑to‑end pipeline (default).",
    )
    return parser

# ----------------------------------------------------------------------
# Demo and full‑pipeline stubs (real implementations live in the
# various ``scripts/run_*.py`` helpers).  They are kept minimal here
# because the heavy lifting is performed by the dedicated scripts.
# ----------------------------------------------------------------------
def _run_demo() -> int:
    """
    Execute the demo pipeline:
    1. Ensure the manual curated CSV exists (creates a template if missing).
    2. Preprocess the raw data → ``data/processed/alloys_raw.csv``.
    3. Engineer descriptors → ``data/processed/alloys_features.csv``.
    4. Fit a LinearRegression model on the demo data.
    5. Write ``data/results/demo_metrics.json`` with numeric ``r2`` and ``mae``.
    """
    from scripts.run_manual_curator import main as run_manual_curator
    from scripts.run_preprocessing import main as run_preprocessing
    from scripts.run_feature_engineering import main as run_feature_engineering
    from scripts.run_model_training import main as run_model_training

    # 1. Manual curator (creates the template if it does not exist)
    run_manual_curator()
    # 2. Preprocessing
    run_preprocessing()
    # 3. Feature engineering
    run_feature_engineering()
    # 4. Model training (demo mode – the training script recognises the ``--demo`` flag internally)
    run_model_training()
    return 0

def _run_full() -> int:
    """
    Execute the full pipeline by invoking the existing high‑level scripts
    in the documented order.
    """
    from scripts.run_ingestion import main as run_ingestion
    from scripts.run_preprocessing import main as run_preprocessing
    from scripts.run_feature_engineering import main as run_feature_engineering
    from scripts.run_model_training import main as run_model_training
    from scripts.run_final_report import main as run_final_report

    # Ingestion → preprocessing → feature engineering → model training → report
    run_ingestion()
    run_preprocessing()
    run_feature_engineering()
    run_model_training()
    run_final_report()
    return 0

# ----------------------------------------------------------------------
# Main entry point used by ``python -m src.main`` and by the wrapper
# ``code/main.py``.
# ----------------------------------------------------------------------
def main(argv: list | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if args.demo:
        logger.info("Running demo pipeline …")
        return _run_demo()
    else:
        logger.info("Running full pipeline …")
        return _run_full()

if __name__ == "__main__":
    # When the module is executed directly, forward the system argv.
    import sys

    sys.exit(main())
