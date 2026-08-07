import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths, ensure_directories

logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all required output directories exist."""
    paths = get_local_paths()
    ensure_directories([
        paths['processed_data'],
        paths['logs']
    ])

def load_burden_data():
    """Load the calculated heteroplasmy burden data."""
    paths = get_local_paths()
    burden_path = paths['processed_data'] / 'burden_per_sample.csv'
    
    if not burden_path.exists():
        raise FileNotFoundError(f"Burden data not found at {burden_path}. "
                                "Run preprocess.py (T015/T016) first.")
    
    logger.info(f"Loading burden data from {burden_path}")
    df = pd.read_csv(burden_path)
    return df

def load_haplogroup_data():
    """Load the assigned haplogroup data."""
    paths = get_local_paths()
    haplogroup_path = paths['processed_data'] / 'haplogroups.csv'
    
    if not haplogroup_path.exists():
        raise FileNotFoundError(f"Haplogroup data not found at {haplogroup_path}. "
                                "Run preprocess.py (T017) first.")
    
    logger.info(f"Loading haplogroup data from {haplogroup_path}")
    df = pd.read_csv(haplogroup_path)
    return df

def load_metadata_panel():
    """Load the 1000 Genomes metadata panel containing age, sex, population, and PCs."""
    paths = get_local_paths()
    # Expected path based on T012/T009 setup
    metadata_path = paths['raw_data'] / '1000G_metadata_panel.csv'
    
    if not metadata_path.exists():
        # Fallback to processed if raw wasn't saved separately but loaded into memory
        # or if the task T012 saved it to processed
        processed_metadata_path = paths['processed_data'] / '1000G_metadata_panel.csv'
        if processed_metadata_path.exists():
            metadata_path = processed_metadata_path
        else:
            raise FileNotFoundError(f"Metadata panel not found at {metadata_path} or {processed_metadata_path}. "
                                    "Run load_data.py (T012) first.")
    
    logger.info(f"Loading metadata panel from {metadata_path}")
    df = pd.read_csv(metadata_path)
    return df

def merge_datasets():
    """
    Join burden, haplogroups, age, sex, population, and PCs.
    
    Returns:
        pd.DataFrame: Merged dataset ready for analysis.
    """
    logger.info("Starting metadata merge logic (T018)")
    
    # Load components
    burden_df = load_burden_data()
    haplogroup_df = load_haplogroup_data()
    metadata_df = load_metadata_panel()
    
    # Standardize sample ID column name if necessary
    # Assuming 'sample_id' or 'Sample' is the key. 
    # T012/T015 usually produce 'sample_id'.
    common_key = 'sample_id'
    if 'Sample' in metadata_df.columns and common_key not in metadata_df.columns:
        metadata_df = metadata_df.rename(columns={'Sample': common_key})
    if 'Sample' in burden_df.columns and common_key not in burden_df.columns:
        burden_df = burden_df.rename(columns={'Sample': common_key})
    if 'Sample' in haplogroup_df.columns and common_key not in haplogroup_df.columns:
        haplogroup_df = haplogroup_df.rename(columns={'Sample': common_key})
    
    # Merge burden (left) with haplogroup
    merged = pd.merge(
        burden_df, 
        haplogroup_df, 
        on=common_key, 
        how='left'
    )
    
    # Merge result with metadata
    merged = pd.merge(
        merged,
        metadata_df,
        on=common_key,
        how='left'
    )
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    logger.info(f"Columns: {list(merged.columns)}")
    
    return merged

def main():
    """Main entry point for T018."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    ensure_dirs()
    merged_df = merge_datasets()
    
    paths = get_local_paths()
    output_path = paths['processed_data'] / 'mito_aging_dataset.csv'
    
    logger.info(f"Writing merged dataset to {output_path}")
    merged_df.to_csv(output_path, index=False)
    
    logger.info(f"T018 Complete: Wrote {len(merged_df)} samples to {output_path}")
    return output_path

if __name__ == '__main__':
    main()
