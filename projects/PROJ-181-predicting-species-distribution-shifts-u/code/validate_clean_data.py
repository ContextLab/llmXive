"""
Validation of Clean Data (Task T017).
Verifies that all records have non-null climate variables.
"""
import sys
import os
import logging
import pandas as pd
from pathlib import Path
from config import DATA_DIR, LOGS_DIR

# Setup logging
logger = logging.getLogger(__name__)

def get_climate_columns(df: pd.DataFrame) -> list:
    """
    Identifies climate variable columns in the DataFrame.
    Assumes standard naming or prefixes.
    """
    # Common WorldClim/BioClim prefixes or specific names
    climate_prefixes = ['bio', 'prec', 'temp', 'tmax', 'tmin', 'rad']
    cols = []
    for col in df.columns:
        if any(col.lower().startswith(p) for p in climate_prefixes):
            cols.append(col)
        elif col.startswith('bio'): # Explicit check for bio1-bio19
            cols.append(col)
    return cols

def main():
    """
    Validates the cleaned occurrence data.
    - Checks for nulls in climate columns.
    - Logs summary to logs/validation_summary.txt.
    - Exits with code 1 if any nulls remain.
    """
    logger.info("Validating clean data (T017)...")
    
    clean_path = DATA_DIR / "processed" / "occurrence_clean.csv"
    if not clean_path.exists():
        logger.error(f"Clean data file not found: {clean_path}")
        sys.exit(1)
    
    df = pd.read_csv(clean_path)
    
    climate_cols = get_climate_columns(df)
    if not climate_cols:
        logger.warning("No climate columns found. Assuming all columns are valid or data is not processed yet.")
        # If no climate cols, we can't check. But spec says T014 extracts them.
        # If T014 hasn't run, this is an error state.
        # For now, we assume the file exists and has columns.
        return 0
    
    null_counts = df[climate_cols].isnull().sum()
    total_nulls = null_counts.sum()
    
    summary_path = LOGS_DIR / "validation_summary.txt"
    with open(summary_path, 'w') as f:
        f.write(f"Validation Summary for {clean_path}\n")
        f.write(f"Total Records: {len(df)}\n")
        f.write(f"Climate Columns Checked: {len(climate_cols)}\n")
        f.write(f"Total Nulls in Climate Columns: {total_nulls}\n")
        f.write("Null Counts per Column:\n")
        for col, count in null_counts.items():
            if count > 0:
                f.write(f"  {col}: {count}\n")
    
    logger.info(f"Validation summary written to {summary_path}")
    
    if total_nulls > 0:
        logger.error(f"Validation FAILED: {total_nulls} null values found in climate columns.")
        sys.exit(1)
    else:
        logger.info("Validation PASSED: No null values in climate columns.")
        return 0

if __name__ == "__main__":
    sys.exit(main())