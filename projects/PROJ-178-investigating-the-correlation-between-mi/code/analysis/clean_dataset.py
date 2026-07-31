import os
import sys
import logging
from pathlib import Path
import pandas as pd
from analysis.merge_metadata import ensure_dirs, load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets

logger = logging.getLogger(__name__)

def clean_dataset(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Load the merged dataset, exclude samples with missing age or failed haplogroup assignment,
    and return the cleaned DataFrame.
    
    Args:
        input_path: Path to the merged dataset CSV (from T018/T019 merge step).
        output_path: Path where the cleaned CSV will be written.
        
    Returns:
        The cleaned DataFrame ready for analysis.
    """
    logger.info(f"Loading merged dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    initial_count = len(df)
    logger.info(f"Initial dataset size: {initial_count} samples")
    
    # Identify columns expected from merge_datasets
    # Based on T018: burden, haplogroups, age, sex, population, PCs
    age_col = 'age'
    haplogroup_col = 'haplogroup'
    
    # Check if required columns exist
    if age_col not in df.columns:
        raise ValueError(f"Required column '{age_col}' not found in dataset. Columns: {list(df.columns)}")
    if haplogroup_col not in df.columns:
        raise ValueError(f"Required column '{haplogroup_col}' not found in dataset. Columns: {list(df.columns)}")
        
    # Exclude samples with missing age
    missing_age = df[age_col].isna().sum()
    if missing_age > 0:
        logger.warning(f"Excluding {missing_age} samples with missing age values")
        df = df.dropna(subset=[age_col])
        
    # Exclude samples with missing or failed haplogroup assignment
    # Failed assignments are typically marked as 'Unknown', 'Failed', or empty strings
    failed_hg_mask = df[haplogroup_col].isna() | (df[haplogroup_col].isin(['Unknown', 'Failed', '']))
    failed_hg_count = failed_hg_mask.sum()
    if failed_hg_count > 0:
        logger.warning(f"Excluding {failed_hg_count} samples with failed or missing haplogroup assignment")
        df = df[~failed_hg_mask]
        
    final_count = len(df)
    logger.info(f"Final dataset size after exclusions: {final_count} samples")
    logger.info(f"Total excluded: {initial_count - final_count} samples")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write cleaned dataset
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned dataset written to {output_path}")
    
    return df

def main():
    """
    Main entry point for the clean_dataset script.
    Reads the merged dataset, applies exclusion logic, and writes the cleaned dataset.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths from environment or defaults
    # Assuming the merge step writes to a standard location
    input_path = os.environ.get('MERGED_DATASET_PATH', 'code/data/processed/merged_dataset.csv')
    output_path = os.environ.get('CLEANED_DATASET_PATH', 'code/data/processed/mito_aging_dataset_clean.csv')
    
    # Ensure directories exist
    ensure_dirs()
    
    try:
        df = clean_dataset(input_path, output_path)
        logger.info("Dataset cleaning completed successfully")
    except Exception as e:
        logger.error(f"Dataset cleaning failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()