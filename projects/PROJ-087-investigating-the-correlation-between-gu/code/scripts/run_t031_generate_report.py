import sys
import os
import logging
from pathlib import Path

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.report_final import run_final_report_generation

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("Executing T031: Generate final HTML report")

    try:
        run_final_report_generation(
            correlation_results_path="data/processed/correlation_results.csv",
            ingestion_report_path="data/processed/ingestion_report.json",
            plots_directory="data/processed/plots",
            output_path="data/processed/final_report.html"
        )
        logger.info("T031 completed successfully. Report generated at data/processed/final_report.html")
    except Exception as e:
        logger.error(f"T031 failed: {e}")
        raise

if __name__ == "__main__":
    main()
