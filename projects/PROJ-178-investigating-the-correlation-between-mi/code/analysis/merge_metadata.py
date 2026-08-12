import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths, ensure_directories

logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all necessary directories exist."""
    paths = get_local_paths()
    ensure_directories(paths)

def load_burden_data():
    """Load the calculated heteroplasmy burden data."""
    paths = get_local_paths()
    burden_path = paths['processed_burden']
    if not os.path.exists(burden_path):
        raise FileNotFoundError(f"Burden data not found at {burden_path}. Run preprocess.py first.")
    logger.info(f"Loading burden data from {burden_path}")
    return pd.read_csv(burden_path)

def load_haplogroup_data():
    """Load the assigned haplogroup data."""
    paths = get_local_paths()
    haplogroup_path = paths['processed_haplogroups']
    if not os.path.exists(haplogroup_path):
        raise FileNotFoundError(f"Haplogroup data not found at {haplogroup_path}. Run preprocess.py first.")
    logger.info(f"Loading haplogroup data from {haplogroup_path}")
    return pd.read_csv(haplogroup_path)

def load_metadata_panel():
    """Load the 1000 Genomes metadata panel containing age, sex, population, and PCs."""
    paths = get_local_paths()
    metadata_path = paths['metadata_panel']
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata panel not found at {metadata_path}. Run load_data.py first.")
    logger.info(f"Loading metadata panel from {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    
    # Ensure standard column names if they differ slightly in source
    # Expected columns: sample_id, age, sex, population, PC1, PC2
    if 'sample_id' not in df.columns:
        # Try to find a common alternative
        possible_ids = ['SampleID', 'Sample_ID', 'sample', 'ID']
        for col in possible_ids:
            if col in df.columns:
                df.rename(columns={col: 'sample_id'}, inplace=True)
                break
        if 'sample_id' not in df.columns:
            raise ValueError("Could not identify sample ID column in metadata panel.")
    
    return df

def merge_datasets():
    """
    Merge burden, haplogroups, and metadata into a single analysis-ready dataset.
    
    Logic:
    1. Load all three sources.
    2. Merge burden and haplogroups on sample_id (inner join to ensure both exist).
    3. Merge result with metadata on sample_id (inner join to ensure age/PCs exist).
    4. Validate critical columns are present and non-null.
    5. Return the merged dataframe.
    """
    logger.info("Starting metadata merge process.")
    
    # Load components
    burden_df = load_burden_data()
    haplogroup_df = load_haplogroup_data()
    metadata_df = load_metadata_panel()
    
    # Ensure sample_id is consistent type (string) for merging
    for df in [burden_df, haplogroup_df, metadata_df]:
        df['sample_id'] = df['sample_id'].astype(str)
    
    # Merge burden and haplogroups
    merged = pd.merge(
        burden_df, 
        haplogroup_df, 
        on='sample_id', 
        how='inner'
    )
    logger.info(f"After merging burden and haplogroups: {len(merged)} samples")
    
    # Merge with metadata
    merged = pd.merge(
        merged, 
        metadata_df, 
        on='sample_id', 
        how='inner'
    )
    logger.info(f"After merging with metadata: {len(merged)} samples")
    
    # Validation: Check for critical columns
    required_cols = ['sample_id', 'age', 'sex', 'population', 'PC1', 'PC2']
    missing_cols = [col for col in required_cols if col not in merged.columns]
    if missing_cols:
        raise ValueError(f"Missing critical columns in merged dataset: {missing_cols}")
    
    # Check for missing values in critical columns
    critical_cols = ['age', 'burden', 'haplogroup']
    for col in critical_cols:
        if col not in merged.columns:
            raise ValueError(f"Critical column '{col}' missing from merged dataset.")
        null_count = merged[col].isna().sum()
        if null_count > 0:
            logger.warning(f"Found {null_count} missing values in critical column '{col}'. "
                         "These will be handled by exclusion logic in T019.")
    
    logger.info("Merge completed successfully.")
    return merged

def main():
    """Main entry point for the merge script."""
    ensure_dirs()
    merged_df = merge_datasets()
    
    paths = get_local_paths()
    output_path = paths['processed_dataset']
    
    logger.info(f"Writing merged dataset to {output_path}")
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(merged_df)} rows to {output_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
