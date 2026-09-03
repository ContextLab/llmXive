"""
Runner script for T045 - Analysis Summary Generation
This script is invoked by the quickstart run-book to generate the analysis summary.
"""
import os
import sys
import logging

# Add the code directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code.logging_config import setup_logging
from code.analysis_summary import main

def main_run():
    """Main entry point for the analysis summary generation."""
    logger = setup_logging()
    
    # Default paths based on project structure
    feature_importance_path = os.path.join("data", "processed", "feature_importance.csv")
    correlation_path = os.path.join("data", "processed", "correlation_results.csv")
    output_path = os.path.join("data", "processed", "analysis_summary.json")
    
    logger.info("Starting analysis summary generation (T045)")
    
    try:
        main(
            feature_importance_path=feature_importance_path,
            correlation_path=correlation_path,
            output_path=output_path,
            top_n=10
        )
        logger.info("Analysis summary generation completed successfully")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        logger.error("Ensure that feature_importance.csv and correlation_results.csv exist in data/processed/")
        return 1
    except Exception as e:
        logger.error(f"Error during analysis summary generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_run())
