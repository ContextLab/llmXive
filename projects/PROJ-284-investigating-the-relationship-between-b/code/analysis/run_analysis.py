"""
Runner script to execute the full analysis pipeline including FDR correction.
This script ensures that data/analysis/full_metrics.csv is generated.
"""
import shutil
from pathlib import Path
from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)


def main() -> None:
    """
    Execute the analysis pipeline.
    This wraps the correlations module to ensure it runs as a standalone step.
    """
    logger.log("run_analysis_start", step="analyze")
    try:
        # Ensure output directories exist
        output_dir = Path("data/analysis")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run the correlation and FDR pipeline
        # This function is responsible for writing data/analysis/full_metrics.csv
        correlations_main()

        logger.log("run_analysis_complete", status="success")

    except Exception as e:
        logger.log("run_analysis_error", error=str(e))
        raise


if __name__ == "__main__":
    main()
