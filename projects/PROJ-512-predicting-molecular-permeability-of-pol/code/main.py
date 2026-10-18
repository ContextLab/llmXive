"""
Main orchestration script for the polymer permeability prediction pipeline.

Run from the code/ directory:
    python main.py [--max-records N] [--skip-training]

Pipeline stages:
    1. Data ingestion (real NIST/PubChem data only; halts loudly if unavailable)
    2. Preprocessing (graph construction, feature extraction, scaffold split)
    3. Model training (GNN + Random Forest + Linear Regression baselines)
    4. Evaluation and statistical validation (Wilcoxon, VIF, sensitivity)

Per SC-001, no simulation fallback is permitted: if real data cannot be
fetched, the pipeline exits with a non-zero status code.
"""
import argparse
import logging
import sys

from data.utils import setup_logging, ensure_seed_initialized, get_seed

logger = logging.getLogger(__name__)


def check_environment() -> bool:
    """Verify the runtime environment is CPU-only-compatible.

    Returns:
        True if the environment is suitable for the pipeline.
    """
    ok = True
    try:
        import torch

        if torch.cuda.is_available():
            logger.warning(
                "CUDA device detected; this project targets CPU-only CI. "
                "Continuing on CPU."
            )
        logger.info("PyTorch %s available (CUDA available: %s)",
                    torch.__version__, torch.cuda.is_available())
    except ImportError:
        logger.error("PyTorch is not installed; model training is unavailable.")
        ok = False

    try:
        from rdkit import rdBase  # noqa: F401

        logger.info("RDKit %s available.", rdBase.rdkitVersion)
    except ImportError:
        logger.error("RDKit is not installed; SMILES parsing is unavailable.")
        ok = False

    return ok


def run_ingestion(max_records: int) -> bool:
    """Run the data ingestion stage (real data only)."""
    from data.ingestion import main as ingestion_main, DataUnavailableError

    try:
        ingestion_main()
    except DataUnavailableError as exc:
        logger.error(str(exc))
        return False
    except SystemExit as exc:
        if exc.code not in (0, None):
            logger.error("Ingestion failed with exit code %s.", exc.code)
            return False
    return True


def run_preprocessing() -> bool:
    """Run the preprocessing / scaffold-split stage."""
    try:
        from data.preprocessing import main as preprocessing_main

        preprocessing_main()
        return True
    except Exception as exc:  # fail loudly, no silent fallback
        logger.error("Preprocessing failed: %s", exc)
        return False


def run_training() -> bool:
    """Run model training and evaluation stages."""
    try:
        from models.trainer import main as trainer_main

        trainer_main()
        return True
    except Exception as exc:
        logger.error("Training failed: %s", exc)
        return False


def run_evaluation() -> bool:
    """Run evaluation and statistical reporting stages."""
    try:
        from evaluation.report import main as report_main

        report_main()
        return True
    except Exception as exc:
        logger.error("Evaluation failed: %s", exc)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Polymer permeability prediction pipeline"
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=2000,
        help="Maximum number of records to process (RAM safety cap).",
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Skip the model training stage.",
    )
    args = parser.parse_args()

    setup_logging(level="INFO")
    ensure_seed_initialized()
    logger.info("Pipeline started (seed=%d, max_records=%d)",
                get_seed(), args.max_records)

    if not check_environment():
        logger.error("Environment check failed. Aborting.")
        return 1

    if not run_ingestion(args.max_records):
        return 1
    if not run_preprocessing():
        return 1
    if not args.skip_training:
        if not run_training():
            return 1
    if not run_evaluation():
        return 1

    logger.info("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())