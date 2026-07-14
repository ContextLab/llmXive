"""
Runner script for full analysis pipeline.
Orchestrates metrics extraction and correlation analysis.
"""
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """Main entry point."""
    logger.log("run_analysis_start", {})

    try:
        # Run correlation analysis (includes metrics aggregation and full metrics generation)
        correlations_main()
        logger.log("run_analysis_complete", {})
    except Exception as e:
        logger.log("run_analysis_error", {"error": str(e)})
        raise

if __name__ == "__main__":
    main()
