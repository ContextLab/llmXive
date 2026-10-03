"""
Main orchestration entry point.
"""
import argparse
import sys
import logging
from pathlib import Path
from config import Config
from utils import setup_logging

# Import setup_dirs functions to allow running T004 directly
from setup_dirs import main as setup_dirs_main

def run_stage(stage_name: str, config: Config) -> None:
    """
    Run a specific stage of the pipeline.
    Currently, this is a placeholder for future stage execution logic.
    For T004, we rely on the direct execution of setup_dirs.py.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running stage: {stage_name}")
    # Future implementation will dispatch to specific stage scripts

def main() -> None:
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Avian Song Variation Analysis Pipeline")
    parser.add_argument("--stage", type=str, help="Stage to run (e.g., setup, ingestion, eda, modeling)")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")

    args = parser.parse_args()

    logger = setup_logging("main")

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        config = Config()
    else:
        config = Config.load(config_path)

    if args.stage:
        run_stage(args.stage, config)
    else:
        logger.info("No stage specified. Use --stage to run a specific stage.")
        # For T004 setup, users should run: python code/setup_dirs.py

if __name__ == "__main__":
    main()