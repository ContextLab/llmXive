import cProfile
import pstats
import io
import sys
import os
import logging

from data.pipeline import run_pipeline
from models.train import run_training_pipeline
from models.evaluate import run_evaluation_pipeline


def run_full_pipeline(root_dir: str = ".") -> None:
    """
    Run the full HEA yield strength prediction pipeline.

    Args:
        root_dir: Project root directory
    """
    os.chdir(root_dir)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting full pipeline execution...")

    # Step 1: Data Pipeline
    logger.info("Step 1: Running data pipeline...")
    try:
        run_pipeline()
        logger.info("Data pipeline completed.")
    except Exception as e:
        logger.error(f"Data pipeline failed: {e}")
        raise

    # Step 2: Training Pipeline
    logger.info("Step 2: Running training pipeline...")
    try:
        run_training_pipeline()
        logger.info("Training pipeline completed.")
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        raise

    # Step 3: Evaluation Pipeline
    logger.info("Step 3: Running evaluation pipeline...")
    try:
        run_evaluation_pipeline()
        logger.info("Evaluation pipeline completed.")
    except Exception as e:
        logger.error(f"Evaluation pipeline failed: {e}")
        raise

    logger.info("Full pipeline completed successfully.")


def profile_and_report(root_dir: str = ".") -> None:
    """
    Profile the full pipeline and generate a report.

    Args:
        root_dir: Project root directory
    """
    os.chdir(root_dir)

    pr = cProfile.Profile()
    pr.enable()

    try:
        run_full_pipeline(root_dir)
    finally:
        pr.disable()

    # Generate stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Top 20 functions

    print("\n=== Profiling Report ===")
    print(s.getvalue())


def main() -> None:
    """Main entry point for profiler."""
    root = os.getenv("PROJECT_ROOT", ".")
    mode = os.getenv("PROFILE_MODE", "run")

    if mode == "profile":
        profile_and_report(root)
    else:
        run_full_pipeline(root)


if __name__ == "__main__":
    main()