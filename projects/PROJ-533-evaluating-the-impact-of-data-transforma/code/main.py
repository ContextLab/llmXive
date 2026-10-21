import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from code.utils.checkpointing import load_state

# Import stage entry points
from code.data.download_datasets import main as download_main
from code.data.checksum_datasets import main as checksum_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger("pipeline")

def _has_raw_datasets() -> bool:
    """Return True if the raw data directory contains at least one dataset file."""
    raw_dir = Path("data") / "raw"
    if not raw_dir.is_dir():
        return False
    for ext in ("parquet", "csv", "arff"):
        if any(raw_dir.glob(f"*.{ext}")):
            return True
    return False

def run_stage(stage: str, resume: bool, run_id: str, logger: logging.Logger):
    """
    Orchestrates the execution of a specific pipeline stage.
    """
    state = None
    if resume:
        logger.info(f"Attempting to resume from checkpoint: {run_id}")
        state = load_state(run_id)
        if state:
            logger.info("Checkpoint loaded successfully.")
        else:
            logger.warning("No checkpoint found for run_id. Starting from scratch.")

    if stage == "download":
        logger.info("Executing stage: download")
        if _has_raw_datasets():
            logger.info("Raw datasets already present – skipping download.")
        else:
            download_main()
            checksum_main()
    elif stage == "filter":
        logger.info("Executing stage: filter")
        # Placeholder – actual implementation resides in later tasks
    elif stage == "simulate":
        logger.info("Executing stage: simulate")
        # Placeholder – actual implementation resides in later tasks
    elif stage == "aggregate":
        logger.info("Executing stage: aggregate")
        # Placeholder – actual implementation resides in later tasks
    elif stage == "all":
        logger.info("Executing full pipeline: download -> checksum")
        if _has_raw_datasets():
            logger.info("Raw datasets already present – skipping download.")
        else:
            download_main()
            checksum_main()
        logger.info("All implemented stages completed successfully.")
    else:
        raise ValueError(f"Unknown stage: {stage}")

def main():
    parser = argparse.ArgumentParser(description="llmXive Data Transformation Pipeline")
    parser.add_argument(
        "--stage",
        choices=["download", "filter", "simulate", "aggregate", "all"],
        required=True,
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Resume from the last checkpoint"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intended operations and exit",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="default_run",
        help="Unique identifier for the run",
    )

    args = parser.parse_args()
    logger = setup_logging()

    if args.dry_run:
        logger.info("DRY RUN ENABLED. No changes will be made to the filesystem.")
        stage_summaries = {
            "download": "Download datasets from OpenML/UCI, verify URLs, and compute SHA-256 checksums.",
            "filter": "Impute missing values and filter datasets based on normality (Shapiro-Wilk) and sample size (N >= 30).",
            "simulate": "Generate simulated datasets with known effect sizes (Cohen's d) for power analysis.",
            "aggregate": "Aggregate Type I error and power results, compute bootstrap CIs, and perform Friedman tests.",
            "all": "Execute all stages in sequence: download -> checksum -> (future stages).",
        }

        print(f"\n--- Dry Run Summary ---")
        print(f"Stage: {args.stage}")
        print(f"Operation: {stage_summaries[args.stage]}")
        print(f"Resume: {args.resume}")
        print(f"Run ID: {args.run_id}")
        print(f"-----------------------\n")
        sys.exit(0)

    try:
        run_stage(args.stage, args.resume, args.run_id, logger)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
