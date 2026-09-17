"""
Orchestrates the full LlmXive research pipeline:
download -> preprocess -> verify_labels -> embed -> train -> eval -> report -> state-update

This script serves as the single entry point for executing the complete research workflow.
"""
import os
import sys
import argparse
import logging
import time
import traceback
from pathlib import Path
from typing import List, Callable, Dict, Any

# Enforce CPU-only execution immediately
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.env_config import enforce_cpu_only, log_environment_config
from src.utils.logging_config import configure_logging_level, get_logger
from src.utils.config import ensure_dir, load_state, save_state, update_artifact_hash
from src.data.download import main as download_main
from src.data.preprocess import main as preprocess_main
from src.data.verify_labels import main as verify_labels_main
from src.data.embed import main as embed_main
from src.models.train import main as train_main
from src.models.eval import main as eval_main
from src.models.report_generator import main as report_main
from src.cli.update_state import main as update_state_main

logger = get_logger(__name__)


def step_download(args: argparse.Namespace) -> None:
    """Execute the data download step."""
    logger.info("Starting data download step...")
    download_main()
    logger.info("Data download step completed.")


def step_preprocess(args: argparse.Namespace) -> None:
    """Execute the data preprocessing step."""
    logger.info("Starting data preprocessing step...")
    preprocess_main()
    logger.info("Data preprocessing step completed.")


def step_verify_labels(args: argparse.Namespace) -> None:
    """Execute the label verification step."""
    logger.info("Starting label verification step...")
    verify_labels_main()
    logger.info("Label verification step completed.")


def step_embed(args: argparse.Namespace) -> None:
    """Execute the embedding extraction step."""
    logger.info("Starting embedding extraction step...")
    embed_main()
    logger.info("Embedding extraction step completed.")


def step_train(args: argparse.Namespace) -> None:
    """Execute the model training step."""
    logger.info("Starting model training step...")
    train_main()
    logger.info("Model training step completed.")


def step_eval(args: argparse.Namespace) -> None:
    """Execute the model evaluation step."""
    logger.info("Starting model evaluation step...")
    eval_main()
    logger.info("Model evaluation step completed.")


def step_report(args: argparse.Namespace) -> None:
    """Execute the report generation step."""
    logger.info("Starting report generation step...")
    report_main()
    logger.info("Report generation step completed.")


def step_update_state(args: argparse.Namespace) -> None:
    """Execute the state update step."""
    logger.info("Starting state update step...")
    update_state_main()
    logger.info("State update step completed.")


def run_pipeline(args: argparse.Namespace) -> int:
    """
    Execute the full pipeline in sequence.

    Returns:
        int: 0 on success, 1 on failure.
    """
    start_time = time.time()
    enforce_cpu_only()
    log_environment_config()

    steps: List[Callable[[argparse.Namespace], None]] = [
        step_download,
        step_preprocess,
        step_verify_labels,
        step_embed,
        step_train,
        step_eval,
        step_report,
        step_update_state,
    ]

    # Filter steps based on arguments if partial execution is requested
    if args.step:
        valid_steps = [s for s in steps if s.__name__.replace("step_", "") == args.step]
        if not valid_steps:
            logger.error(f"Unknown step: {args.step}")
            return 1
        steps = valid_steps

    try:
        for step_func in steps:
            step_func(args)

        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        logger.error(traceback.format_exc())
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the LlmXive research pipeline."
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["download", "preprocess", "verify_labels", "embed", "train", "eval", "report", "update_state"],
        default=None,
        help="Run a specific step instead of the full pipeline.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level.",
    )

    args = parser.parse_args()
    configure_logging_level(args.log_level)

    return run_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())