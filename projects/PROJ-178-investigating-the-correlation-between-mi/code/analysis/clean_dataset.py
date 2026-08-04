import os
import sys
import logging
from pathlib import Path
import pandas as pd
from analysis.merge_metadata import ensure_dirs, load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets

logger = logging.getLogger(__name__)

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataset by removing samples with missing age or failed haplogroup assignment.
    
    Args:
        df: Merged DataFrame with burden, haplogroup, and metadata
        
    Returns:
        Cleaned DataFrame with only valid samples
    """
    logger.info(f"Starting cleaning of dataset with {len(df)} rows")
    
    # Check for missing age values
    missing_age = df['age'].isna().sum()
    if missing_age > 0:
        logger.warning(f"Found {missing_age} samples with missing age values")
        df = df.dropna(subset=['age'])
    
    # Check for missing/failed haplogroup assignments
    # Haplogroup assignment might fail and result in NaN or a specific failure code
    missing_haplogroup = df['haplogroup'].isna().sum()
    if missing_haplogroup > 0:
        logger.warning(f"Found {missing_haplogroup} samples with missing haplogroup assignments")
        df = df.dropna(subset=['haplogroup'])
    
    # Also check for specific failure codes if they exist (e.g., 'FAILED', 'NONE')
    if 'haplogroup' in df.columns:
        failure_codes = ['FAILED', 'NONE', 'UNKNOWN', '']
        for code in failure_codes:
            if code in df['haplogroup'].values:
                count = (df['haplogroup'] == code).sum()
                if count > 0:
                    logger.warning(f"Found {count} samples with haplogroup failure code: {code}")
                    df = df[df['haplogroup'] != code]
    
    logger.info(f"Cleaned dataset now has {len(df)} rows")
    return df

def main():
    """
    Main entry point for cleaning the dataset.
    This function loads the merged data, applies exclusion logic,
    and saves the cleaned dataset for T020 to write.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths
    from config.environment import get_local_paths
    paths = get_local_paths()
    
    # Load merged data (output of T018)
    merged_file = os.path.join(paths['processed_data'], 'merged_data.csv')
    
    if not os.path.exists(merged_file):
        raise FileNotFoundError(f"Merged data file not found at {merged_file}. "
                               "Please ensure T018 (merge_metadata) has been completed.")
    
    logger.info(f"Loading merged data from {merged_file}")
    df = pd.read_csv(merged_file)
    
    # Clean the dataset (apply T019 exclusion logic)
    cleaned_df = clean_dataset(df)
    
    # Save cleaned data for T020 to write
    output_file = os.path.join(paths['processed_data'], 'cleaned_data.csv')
    logger.info(f"Saving cleaned data to {output_file}")
    cleaned_df.to_csv(output_file, index=False)
    
    logger.info(f"Cleaned dataset saved with {len(cleaned_df)} rows")
    return cleaned_df

if __name__ == '__main__':
    main()
