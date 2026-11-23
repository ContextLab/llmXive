"""
Main orchestrator for the Brain Network Efficiency pipeline.

Runs the complete pipeline: Download → Preprocess → Graph → Stats
"""
import sys
from pathlib import Path

from config import ensure_directories, validate_config
from utils.logging import get_logger, setup_logging, info, error

logger = get_logger(__name__)


def main() -> int:
    """
    Execute the full pipeline.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Setup
        setup_logging()
        info(logger, "Starting Brain Network Efficiency pipeline")

        # Validate configuration
        validate_config()
        info(logger, "Configuration validated")

        # Ensure directories exist
        ensure_directories()
        info(logger, "Directory structure ready")

        # TODO: Implement pipeline stages
        # 1. Download HCP data
        # 2. Preprocess fMRI data
        # 3. Compute graph metrics
        # 4. Run statistical analysis

        info(logger, "Pipeline execution complete")
        return 0

    except Exception as e:
        error(logger, f"Pipeline failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
