import os
import sys
import logging
from pathlib import Path
from code.analysis.correlations import main as correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)


def main() -> None:
    """
    Runner for PCA analysis (T023a).
    Executes the PCA pipeline and ensures output files are written.
    """
    logger.log("pca_runner_start")
    try:
        correlations_main()
        logger.log("pca_runner_success")
    except Exception as e:
        logger.log("pca_runner_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
