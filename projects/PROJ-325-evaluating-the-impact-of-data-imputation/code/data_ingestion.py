import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MISSINGNESS_THRESHOLD = 0.30  # 30%
REQUIRED_DESIGN_COLUMNS = ['weight', 'psu', 'strata']


def load_gss_data_subset(source_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load GSS data from a CSV file.
    
    Args:
        source_path: Path to the source CSV file. If None, attempts to load 
                     from data/raw/gss_2018_subset.csv.
                     
    Returns:
        pd.DataFrame: The loaded dataset.
                     
    Raises:
        FileNotFoundError: If the source file does not exist.
        ValueError: If the file is empty or unreadable.
    """
    if source_path is None:
        source_path = "data/raw/gss_2018_subset.csv"
    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source data file not found: {source_path}")
    
    logger.info(f"Loading data from {source_path}")
    try:
        df = pd.read_csv(source_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    if df.empty:
        raise ValueError("Loaded DataFrame is empty.")
        
    logger.info(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
    return df


def ensure_design_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verify that the required design columns (weight, psu, strata) exist in the DataFrame.
    
    Args:
        df: The input DataFrame.
        
    Returns:
        pd.DataFrame: The same DataFrame if all columns are present.
        
    Raises:
        ValueError: If any required design column is missing.
    """
    missing_cols = [col for col in REQUIRED_DESIGN_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required design columns: {missing_cols}. "
            f"Required: {REQUIRED_DESIGN_COLUMNS}"
        )
    logger.info("All required design columns (weight, psu, strata) are present.")
    return df


def detect_missingness(df: pd.DataFrame, threshold: float = MISSINGNESS_THRESHOLD) -> Tuple[pd.DataFrame, List[str]]:
    """
    Detect variables with missingness exceeding a specified threshold and skip them.
    
    This function calculates the percentage of missing values for each column.
    Columns exceeding the threshold are logged as warnings and returned in a list
    of skipped columns. The function returns a new DataFrame with these columns
    removed.
    
    Args:
        df: The input DataFrame.
        threshold: The maximum allowed fraction of missing values (default 0.30).
                    
    Returns:
        Tuple containing:
            - pd.DataFrame: The DataFrame with high-missingness columns removed.
            - List[str]: A list of column names that were skipped due to high missingness.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty; returning empty DataFrame.")
        return df, []
    
    # Calculate missingness percentage
    missing_counts = df.isna().sum()
    total_rows = len(df)
    missing_pct = (missing_counts / total_rows) * 100
    
    skipped_columns = []
    
    for col in df.columns:
        pct = missing_pct[col]
        if pct > (threshold * 100):
            skipped_columns.append(col)
            logger.warning(
                f"Skipping variable '{col}' due to high missingness: {pct:.2f}% "
                f"(threshold: {threshold*100:.1f}%)"
            )
    
    if skipped_columns:
        logger.info(f"Dropped {len(skipped_columns)} variables due to missingness > {threshold*100:.1f}%")
        return df.drop(columns=skipped_columns), skipped_columns
    
    logger.info("No variables exceeded the missingness threshold.")
    return df, []


def ingest_and_save(
    source_path: Optional[str] = None,
    output_path: Optional[str] = None,
    apply_missingness_filter: bool = True
) -> Dict[str, Any]:
    """
    Main pipeline function to ingest data, ensure design columns, optionally filter
    high-missingness variables, and save the result.
    
    Args:
        source_path: Path to the input CSV file.
        output_path: Path to save the processed CSV file. Defaults to 
                     'data/processed/gss_cleaned_subset.csv'.
        apply_missingness_filter: If True, removes columns with >30% missingness.
        
    Returns:
        Dict[str, Any]: A summary dictionary containing:
            - 'status': 'success' or 'error'
            - 'rows_loaded': Number of rows loaded
            - 'rows_processed': Number of rows in the final output
            - 'columns_dropped': List of dropped columns (if any)
            - 'output_path': Path where the file was saved
    """
    if output_path is None:
        output_path = "data/processed/gss_cleaned_subset.csv"
    
    result = {
        'status': 'success',
        'rows_loaded': 0,
        'rows_processed': 0,
        'columns_dropped': [],
        'output_path': output_path
    }
    
    try:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Load data
        df = load_gss_data_subset(source_path)
        result['rows_loaded'] = len(df)
        
        # Ensure design columns
        df = ensure_design_columns(df)
        
        # Apply missingness filter if requested
        if apply_missingness_filter:
            df, dropped = detect_missingness(df)
            result['columns_dropped'] = dropped
        
        # Save to disk
        df.to_csv(output_path, index=False)
        result['rows_processed'] = len(df)
        
        logger.info(f"Processed data saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        result['status'] = 'error'
        result['error_message'] = str(e)
        raise
        
    return result


def main():
    """
    Entry point for the data ingestion script.
    Runs the pipeline on the default GSS subset path and saves the result.
    """
    # Default paths relative to project root
    default_source = "data/raw/gss_2018_subset.csv"
    default_output = "data/processed/gss_cleaned_subset.csv"
    
    # Check if source exists before running
    if not os.path.exists(default_source):
        logger.error(f"Source file {default_source} not found. "
                     "Please run T004 (data ingestion) first to generate the raw data.")
        sys.exit(1)
    
    logger.info("Starting data ingestion pipeline (T013 - Missingness Detection)...")
    
    try:
        summary = ingest_and_save(
            source_path=default_source,
            output_path=default_output,
            apply_missingness_filter=True
        )
        logger.info(f"Pipeline completed successfully. Status: {summary['status']}")
        logger.info(f"Rows: {summary['rows_loaded']} -> {summary['rows_processed']}")
        if summary['columns_dropped']:
            logger.info(f"Dropped columns: {summary['columns_dropped']}")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()