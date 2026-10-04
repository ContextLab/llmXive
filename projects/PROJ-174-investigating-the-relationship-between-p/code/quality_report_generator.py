"""
T038: Generate final quality report.

Explicitly generates `results/quality_report.csv` as a distinct deliverable
by consuming logs and exclusion data from T005 (LoggingContext) and T017 (filter.py).

This script acts as the final aggregation step for the quality reporting pipeline.
It reads the existing `results/quality_report.csv` (initialized by T005 and updated by T017),
validates its schema, and ensures the file is finalized as the distinct deliverable.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from logging_config import LoggingContext, get_logger, initialize_quality_report

logger = get_logger(__name__)

def validate_quality_report_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the quality report has the required schema.
    Required columns: ['exclusion_type', 'count']
    """
    required_cols = {'exclusion_type', 'count'}
    if not required_cols.issubset(set(df.columns)):
        missing = required_cols - set(df.columns)
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        return False
    
    # Ensure 'count' is numeric
    if not pd.api.types.is_numeric_dtype(df['count']):
        logger.error(f"Column 'count' must be numeric. Found: {df['count'].dtype}")
        return False
        
    return True

def generate_final_report(output_path: Path) -> None:
    """
    Generate the final quality report by:
    1. Ensuring the report file exists (initialized by T005).
    2. Validating the schema (T005/T017 contract).
    3. Writing a confirmation log entry.
    4. Saving the final artifact.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists (it should from T005/T017)
    if not output_path.exists():
        logger.warning(f"Quality report not found at {output_path}. Initializing empty report.")
        # Initialize if missing (fallback for clean runs where T017 might not have run yet)
        initialize_quality_report(str(output_path))
    
    # Load existing data
    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        logger.error(f"Failed to read existing quality report: {e}")
        # If we can't read it, try to re-initialize
        initialize_quality_report(str(output_path))
        df = pd.read_csv(output_path)
    
    # Validate schema
    if not validate_quality_report_schema(df):
        raise ValueError(f"Quality report schema validation failed. File: {output_path}")
    
    # Log summary
    total_exclusions = df['count'].sum()
    exclusion_types = df['exclusion_type'].tolist()
    logger.info(f"Quality Report Generated: {output_path}")
    logger.info(f"Total Exclusion Types: {len(exclusion_types)}")
    logger.info(f"Total Exclusion Count: {total_exclusions}")
    logger.info(f"Exclusion Types: {exclusion_types}")
    
    # Re-save to ensure final state (though typically no change needed)
    df.to_csv(output_path, index=False)
    logger.info(f"Final quality report successfully written to {output_path}")

def main():
    """Main entry point for T038."""
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths relative to project root
    output_path = project_root / "results" / "quality_report.csv"
    
    try:
        logger.info("Starting T038: Generate final quality report.")
        generate_final_report(output_path)
        logger.info("T038 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T038 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())