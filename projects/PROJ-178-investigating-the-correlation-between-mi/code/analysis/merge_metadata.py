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
    ensure_directories([
        paths['raw_data'],
        paths['processed_data'],
        paths['logs']
    ])

def load_burden_data(burden_file: str) -> pd.DataFrame:
    """
    Load the heteroplasmy burden data.
    
    Args:
        burden_file: Path to the burden data file
        
    Returns:
        DataFrame with burden data
    """
    logger.info(f"Loading burden data from {burden_file}")
    df = pd.read_csv(burden_file)
    return df

def load_haplogroup_data(haplogroup_file: str) -> pd.DataFrame:
    """
    Load the haplogroup assignment data.
    
    Args:
        haplogroup_file: Path to the haplogroup data file
        
    Returns:
        DataFrame with haplogroup data
    """
    logger.info(f"Loading haplogroup data from {haplogroup_file}")
    df = pd.read_csv(haplogroup_file)
    return df

def load_metadata_panel(metadata_file: str) -> pd.DataFrame:
    """
    Load the metadata panel with age, sex, population, and PCs.
    
    Args:
        metadata_file: Path to the metadata panel file
        
    Returns:
        DataFrame with metadata
    """
    logger.info(f"Loading metadata panel from {metadata_file}")
    df = pd.read_csv(metadata_file)
    return df

def merge_datasets(burden_df: pd.DataFrame, 
                  haplogroup_df: pd.DataFrame, 
                  metadata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge burden, haplogroup, and metadata datasets.
    
    Args:
        burden_df: DataFrame with heteroplasmy burden data
        haplogroup_df: DataFrame with haplogroup assignments
        metadata_df: DataFrame with sample metadata (age, sex, population, PCs)
        
    Returns:
        Merged DataFrame
    """
    logger.info("Merging datasets")
    
    # Start with burden data
    merged = burden_df.copy()
    
    # Merge with haplogroup data
    merged = pd.merge(
        merged, 
        haplogroup_df, 
        on='sample_id', 
        how='left',
        suffixes=('', '_hap')
    )
    
    # Merge with metadata
    merged = pd.merge(
        merged,
        metadata_df,
        on='sample_id',
        how='left'
    )
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def main():
    """
    Main entry point for merging metadata.
    This function loads the burden, haplogroup, and metadata data,
    merges them, and saves the result for T019 (exclusion logic) to use.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths
    paths = get_local_paths()
    
    # Define input files (these should be created by previous steps)
    burden_file = os.path.join(paths['processed_data'], 'burden_per_sample.csv')
    haplogroup_file = os.path.join(paths['processed_data'], 'haplogroups.csv')
    metadata_file = os.path.join(paths['raw_data'], 'metadata_panel.csv')
    
    # Check if input files exist
    if not os.path.exists(burden_file):
        raise FileNotFoundError(f"Burden data not found at {burden_file}")
    if not os.path.exists(haplogroup_file):
        raise FileNotFoundError(f"Haplogroup data not found at {haplogroup_file}")
    if not os.path.exists(metadata_file):
        raise FileNotFoundError(f"Metadata panel not found at {metadata_file}")
    
    # Load data
    burden_df = load_burden_data(burden_file)
    haplogroup_df = load_haplogroup_data(haplogroup_file)
    metadata_df = load_metadata_panel(metadata_file)
    
    # Merge datasets
    merged_df = merge_datasets(burden_df, haplogroup_df, metadata_df)
    
    # Save merged data for T019 to use
    output_file = os.path.join(paths['processed_data'], 'merged_data.csv')
    logger.info(f"Saving merged data to {output_file}")
    merged_df.to_csv(output_file, index=False)
    
    logger.info(f"Merged dataset saved with {len(merged_df)} rows and {len(merged_df.columns)} columns")
    return merged_df

if __name__ == '__main__':
    main()
