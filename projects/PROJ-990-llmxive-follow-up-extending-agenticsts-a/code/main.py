"""
Main pipeline orchestrator.
Executes the core data flow: T005c -> T005b -> T005a -> T006a -> ...
"""
import os
import sys
import argparse
import logging
import json
from pathlib import Path
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define the pipeline stages (ordered list of script modules to run)
PIPELINE_STAGES = [
    "code/t005c_fetch_manifest.py",      # T005c: Fetch Manifest
    "code/t005b_ingest_data.py",         # T005b: Ingest Data (Placeholder for T005b logic)
    "code/t005a_no_data_warning.py",     # T005a: Log Status
    "code/parser.py",                    # T006a: Parse
    "code/entropy.py",                   # T006b: Entropy
    "code/splitter.py",                  # T014a: Split
    # Note: Subsequent stages (T008, T018, etc.) depend on data existence
]

def run_stage(stage_path: str) -> bool:
    """Run a specific pipeline stage script."""
    logger.info(f"Running stage: {stage_path}")
    try:
        result = subprocess.run(
            [sys.executable, stage_path],
            check=True,
            capture_output=False,
            cwd=Path(__file__).parent.parent
        )
        if result.returncode != 0:
            logger.error(f"Stage {stage_path} failed with code {result.returncode}")
            return False
        logger.info(f"Stage {stage_path} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Stage {stage_path} raised CalledProcessError: {e}")
        return False
    except FileNotFoundError:
        logger.error(f"Stage script not found: {stage_path}")
        return False

def run_full_pipeline():
    """Execute the full pipeline sequentially."""
    logger.info("Starting FULL pipeline execution.")
    
    # Ensure data directories exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    for stage in PIPELINE_STAGES:
        if not run_stage(stage):
            logger.error(f"Pipeline failed at stage: {stage}")
            return False
    
    logger.info("Pipeline completed successfully.")
    return True

def run_dry_run_pipeline():
    """Validate pipeline structure without execution."""
    logger.info("Running dry-run (validation only).")
    missing = []
    for stage in PIPELINE_STAGES:
        if not Path(stage).exists():
            missing.append(stage)
    
    if missing:
        logger.error(f"Missing stage scripts: {missing}")
        return False
    
    logger.info("All stage scripts found.")
    return True

def main():
    parser = argparse.ArgumentParser(description="LLMxive Pipeline Runner")
    parser.add_argument("--dry-run", action="store_true", help="Validate scripts without running")
    args = parser.parse_args()

    if args.dry_run:
        success = run_dry_run_pipeline()
    else:
        success = run_full_pipeline()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
