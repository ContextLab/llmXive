"""
Main entry point for the Neural Mechanisms Underlying Adaptive Decision-Making pipeline.

This script initializes the configuration and logging infrastructure.
It does NOT execute pipeline logic yet (that is handled in subsequent tasks T028, T037).
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, load_config_from_yaml, set_seed
from utils.logger import get_logger, setup_file_logging
from utils.io import ensure_dir, load_json

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Neural Mechanisms Adaptive Decision-Making Pipeline"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration YAML file",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (overrides config)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Root output directory for artifacts",
    )
    return parser.parse_args()

def main():
    """
    Initialize the pipeline environment.

    This function:
    1. Parses command line arguments.
    2. Loads configuration from YAML.
    3. Sets random seeds.
    4. Initializes logging.
    5. Ensures output directories exist.

    Note: This is a setup-only entry point. No processing logic is executed here.
    """
    args = parse_args()

    # 1. Load Configuration
    config_path = Path(args.config)
    if not config_path.exists():
        # Fallback to default if specific path not found, but warn
        logging.basicConfig(level=logging.WARNING)
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        config = {}
    else:
        config = load_config_from_yaml(config_path)

    # 2. Apply CLI overrides
    if args.seed is not None:
        config["seed"] = args.seed
    config["output_dir"] = args.output_dir

    # 3. Set Seeds
    seed = config.get("seed", 42)
    set_seed(seed)
    logger = get_logger()
    logger.info(f"Pipeline initialized with seed: {seed}")

    # 4. Setup Logging
    # Ensure output directory exists for logs
    ensure_dir(Path(args.output_dir) / "logs")
    log_file = Path(args.output_dir) / "logs" / "pipeline.log"
    setup_file_logging(
        level=args.log_level,
        log_file=log_file,
        logger_name="pipeline",
    )
    logger.info("Logging infrastructure initialized.")
    logger.info(f"Output directory: {args.output_dir}")

    # 5. Ensure Directory Structure
    # Based on T001 and T007 requirements
    sub_dirs = [
        "raw", "processed", "models", "reports", "figures", "logs"
    ]
    for subdir in sub_dirs:
        ensure_dir(Path(args.output_dir) / subdir)
    logger.debug("Ensured data directory structure exists.")

    logger.info("Setup complete. Ready for pipeline execution (T028/T037).")

    # Explicitly do NOT run pipeline logic here as per task description
    return 0

if __name__ == "__main__":
    sys.exit(main())