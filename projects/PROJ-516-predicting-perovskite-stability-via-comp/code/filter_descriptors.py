import logging
import sys
from pathlib import Path
from typing import Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the input and output paths based on project conventions
INPUT_PATH = Path("data/processed/descriptors.csv")
OUTPUT_PATH = Path("data/processed/descriptors_filtered.csv")
MISSING_THRESHOLD = 2

def load_descriptors(path: Path) -> pd.DataFrame:
    """Load the descriptors CSV file."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def count_missing_values(df: pd.DataFrame, columns: list) -> pd.Series:
    """
    Count the number of missing values per row for a specific set of columns.
    
    Args:
        df: The input DataFrame.
        columns: List of column names to check for missing values.
        
    Returns:
        A Series with the count of missing values for each row.
    """
    if not columns:
        # If no columns specified, check all numeric/object columns
        cols_to_check = df.select_dtypes(include=['number', 'object', 'string']).columns.tolist()
    else:
        # Validate that requested columns exist
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            logger.warning(f"Requested columns not found in DataFrame: {missing_cols}")
            cols_to_check = [c for c in columns if c in df.columns]
        else:
            cols_to_check = columns

    if not cols_to_check:
        return pd.Series([0] * len(df), index=df.index)

    return df[cols_to_check].isna().sum(axis=1)

def filter_entries(df: pd.DataFrame, threshold: int = MISSING_THRESHOLD) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter out entries that have >= threshold missing descriptor values.
    
    Args:
        df: The input DataFrame.
        threshold: The minimum number of missing values that triggers exclusion.
        
    Returns:
        A tuple of (filtered_df, excluded_df).
    """
    # Identify descriptor columns. Usually these are the feature columns, 
    # excluding metadata like 'formula', 'source', 'T_d', 'perovskite_family', 'T_d_uncertainty'.
    # We assume the target variable and metadata should not count towards "descriptor missingness"
    # for the purpose of feature availability, but if the task implies "any data column",
    # we adjust. Based on typical ML pipelines, we filter based on feature columns.
    
    exclude_from_check = {'formula', 'source', 'T_d', 'perovskite_family', 'T_d_uncertainty', 'index'}
    feature_cols = [c for c in df.columns if c not in exclude_from_check]
    
    if not feature_cols:
        logger.warning("No feature columns found to check for missing values.")
        return df, pd.DataFrame()

    missing_counts = count_missing_values(df, feature_cols)
    
    mask = missing_counts < threshold
    filtered_df = df[mask].copy()
    excluded_df = df[~mask].copy()
    
    return filtered_df, excluded_df

def save_filtered_data(filtered_df: pd.DataFrame, output_path: Path) -> None:
    """Save the filtered DataFrame to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(filtered_df)} rows to {output_path}")

def log_exclusion_counts(total: int, kept: int, excluded: int, excluded_df: pd.DataFrame) -> None:
    """Log the exclusion statistics."""
    logger.info(f"Total entries: {total}")
    logger.info(f"Entries kept: {kept}")
    logger.info(f"Entries excluded (>= {MISSING_THRESHOLD} missing descriptors): {excluded}")
    
    if excluded > 0:
        logger.warning(f"Excluded {excluded} entries due to excessive missing data.")
        # Log sample of excluded formulas if available
        if 'formula' in excluded_df.columns:
            sample_formulas = excluded_df['formula'].head(5).tolist()
            logger.info(f"Sample excluded formulas: {sample_formulas}")
    else:
        logger.info("No entries were excluded.")

def main():
    """Main entry point for the filtering task."""
    logger.info(f"Starting descriptor filtering. Threshold: >= {MISSING_THRESHOLD} missing values.")
    
    try:
        # Load data
        df = load_descriptors(INPUT_PATH)
        
        # Filter
        filtered_df, excluded_df = filter_entries(df, threshold=MISSING_THRESHOLD)
        
        # Log results
        log_exclusion_counts(len(df), len(filtered_df), len(excluded_df), excluded_df)
        
        # Save
        save_filtered_data(filtered_df, OUTPUT_PATH)
        
        logger.info("Filtering completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during filtering: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()