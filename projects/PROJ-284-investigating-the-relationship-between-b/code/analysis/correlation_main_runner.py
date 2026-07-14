import logging
from pathlib import Path

from code.analysis.correlations import main as _correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)


def main() -> None:
    """
    Main entry point for the correlation analysis pipeline.
    Orchestrates T023a (PCA), T023b (Full Metrics), and prepares for T024/T025.
    """
    logger.log("correlation_main_runner", operation="start", status="running")
    try:
        # Run the core correlations module which handles T023a and T023b
        _correlations_main()
        
        logger.log("correlation_main_runner", operation="complete", status="success")
    except Exception as e:
        logger.log("correlation_main_runner", operation="fail", error=str(e))
        raise


if __name__ == "__main__":
    main()