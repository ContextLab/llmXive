"""
Script to execute T024: Save correlation results to CSV.

This script runs the correlation analysis (T021-T023) and saves the results
to data/processed/correlation_results.csv as required by T024.

Usage:
    python code/scripts/run_t024_save_results.py
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config
from src.correlation import run_correlation_analysis
from src.correlation_io import save_correlation_results

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Execute T024: Save correlation results."""
    logger.info("Starting T024: Save correlation results")

    config = load_config()
    input_path = config.get("INPUT_DIVERSITY_PATH", "data/processed/diversity_results.csv")
    output_path = config.get("OUTPUT_CORRELATION_PATH", "data/processed/correlation_results.csv")

    # Check if input file exists
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("T024 cannot proceed without diversity results from T020a")
        sys.exit(1)

    try:
        # Run correlation analysis (T021-T023)
        logger.info(f"Running correlation analysis on {input_file}")
        results_df = run_correlation_analysis(input_path=input_path)

        if results_df is None or results_df.empty:
            logger.warning("Correlation analysis returned empty results")
            # Create empty DataFrame with proper structure for blocked state
            import pandas as pd
            results_df = pd.DataFrame(columns=[
                "sample_id", "diversity_index", "sleep_metric",
                "r", "p", "q", "is_moderate", "is_significant", "status"
            ])
            results_df["status"] = "no_data"

        # Save results (T024)
        logger.info(f"Saving results to {output_path}")
        save_correlation_results(results_df, output_path=output_path)

        logger.info("T024 completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T024: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())