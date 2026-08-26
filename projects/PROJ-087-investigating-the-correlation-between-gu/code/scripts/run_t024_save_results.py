"""
Script to execute T024: Save correlation results.
This script runs the correlation analysis (if not already done) and saves the results.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config
from src.correlation import run_correlation_analysis
from src.correlation_io import save_correlation_results

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    
    config = load_config()
    
    # Check if input file exists (cleaned dataset)
    cleaned_path = Path(config.get("INPUT_CLEANED_PATH", "data/processed/cleaned_microbiome_sleep.csv"))
    
    if not cleaned_path.exists():
        logger.error(f"Input file not found: {cleaned_path}. T024 cannot proceed without cleaned data.")
        logger.info("Generating blocked results as per project protocol.")
        
        # Create empty results with blocked status
        import pandas as pd
        blocked_df = pd.DataFrame(columns=[
            "sample_id", "diversity_index", "sleep_metric", "r", "p", "q",
            "is_moderate", "is_significant", "status"
        ])
        blocked_df["status"] = "blocked"
        save_correlation_results(blocked_df, status="blocked")
        return 1

    logger.info(f"Running correlation analysis on {cleaned_path}...")
    
    try:
        # Run the full correlation pipeline (loads data, computes, flags)
        results_df = run_correlation_analysis(input_path=str(cleaned_path))
        
        if results_df is None or results_df.empty:
            logger.warning("Correlation analysis returned no results. Saving blocked state.")
            save_correlation_results(pd.DataFrame(), status="no_data")
            return 0
        
        # Save the results
        save_correlation_results(results_df, status="success")
        
        logger.info("T024 completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Error during correlation analysis: {e}", exc_info=True)
        logger.info("Saving blocked results due to analysis failure.")
        import pandas as pd
        blocked_df = pd.DataFrame(columns=[
            "sample_id", "diversity_index", "sleep_metric", "r", "p", "q",
            "is_moderate", "is_significant", "status"
        ])
        blocked_df["status"] = "error"
        save_correlation_results(blocked_df, status="error")
        return 1

if __name__ == "__main__":
    sys.exit(main())