"""
Entry point for the network synchronization pipeline.

This minimal implementation provides a runnable module that satisfies the
quick‑start guide. It loads the configuration, logs the start of the pipeline,
and exits successfully. The full processing steps (data download, metric
computation, simulation, regression, visualisation) will be added in later
tasks.
"""

import argparse
import sys
from pathlib import Path

from config import load_config
from src.utils import get_logger


def main() -> int:
    """
    Parse command‑line arguments, load the configuration, and run the pipeline.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="Run the network synchronization pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the YAML configuration file (default: config.yaml).",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(str(config_path))

    logger = get_logger(__name__)
    logger.info(f"Starting pipeline with configuration: {config_path}")

    # Placeholder for the full pipeline implementation.
    # In later phases this function will invoke:
    #   - data download (src.loader)
    #   - metric computation (src.topology)
    #   - Kuramoto simulation (src.simulation)
    #   - regression analysis (src.stats)
    #   - visualisation (src.viz)
    #
    # For now we simply log that the entry point was reached.
    logger.info("Pipeline entry point reached – full implementation pending.")

    return 0


if __name__ == "__main__":
    sys.exit(main())