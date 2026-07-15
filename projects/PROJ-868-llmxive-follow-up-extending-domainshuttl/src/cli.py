"""
Command Line Interface for the llmXive pipeline.
Orchestrates the full workflow: Load -> Complexity -> Embed -> Save.
"""
import argparse
import sys
from pathlib import Path

from src.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="llmXive DomainShuttle Pipeline")
    parser.add_argument(
        "--stage",
        type=str,
        choices=["setup", "data", "train", "analyze", "full"],
        default="full",
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom config file (optional)",
    )
    
    args = parser.parse_args()
    logger.info(f"Starting pipeline stage: {args.stage}")
    
    settings = get_settings()
    logger.info(f"Project root: {settings.project_root}")
    logger.info(f"Fidelity threshold: {settings.fidelity_threshold}")
    
    # Placeholder for stage execution logic
    # This will be expanded in T012, T016, T020
    if args.stage == "setup":
        logger.info("Setup stage: Ensuring directories and config.")
        settings.ensure_dirs()
        logger.info("Setup complete.")
    elif args.stage == "full":
        logger.warning("Full pipeline not yet implemented. Run individual stages.")
        return 1
    else:
        logger.warning(f"Stage '{args.stage}' not yet implemented.")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
