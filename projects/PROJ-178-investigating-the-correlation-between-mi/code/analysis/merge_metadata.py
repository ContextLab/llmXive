import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths, ensure_directories

logger = logging.getLogger(__name__)

def ensure_dirs():
    ensure_directories()

def load_burden_data(filepath: str) -> pd.DataFrame:
    """Load burden data from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Burden data not found at {filepath}")
    return pd.read_csv(path)

def load_haplogroup_data(filepath: str) -> pd.DataFrame:
    """Load haplogroup data from CSV."""
    path = Path(filepath)
    if not path.exists():
        # If haplogroup file doesn't exist, return empty DF with expected schema
        logger.warning(f"Haplogroup data not found at {filepath}. Returning empty DF.")
        return pd.DataFrame(columns=['sample_id', 'haplogroup'])
    return pd.read_csv(path)

def load_metadata_panel(filepath: str) -> pd.DataFrame:
    """Load metadata panel from TSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Metadata panel not found at {filepath}")
    return pd.read_csv(path, sep='\t')

def merge_datasets(burden_df: pd.DataFrame, haplogroup_df: pd.DataFrame, meta_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge burden, haplogroup, and metadata into a single dataset.
    """
    logger.info("Merging datasets...")
    
    # Ensure sample_id is consistent
    if 'sample_id' not in burden_df.columns:
        burden_df = burden_df.rename(columns={burden_df.columns[0]: 'sample_id'})
    
    # Merge burden with metadata
    df = burden_df.merge(meta_df, on='sample_id', how='inner')
    logger.info(f"After merging burden and metadata: {len(df)} samples")
    
    # Merge with haplogroup
    df = df.merge(haplogroup_df, on='sample_id', how='left')
    logger.info(f"After merging haplogroup: {len(df)} samples")
    
    return df

def main():
    """Main entry point for merging metadata."""
    logging.basicConfig(level=logging.INFO)
    paths = get_local_paths()
    
    burden_file = paths['processed'] / 'burden_raw.csv'
    meta_file = paths['raw'] / '1000G_metadata.tsv'
    haplogroup_file = paths['processed'] / 'haplogroups.csv'
    output_file = paths['processed'] / 'mito_aging_dataset.csv'
    
    try:
        burden_df = load_burden_data(str(burden_file))
        meta_df = load_metadata_panel(str(meta_file))
        haplogroup_df = load_haplogroup_data(str(haplogroup_file))
        
        merged_df = merge_datasets(burden_df, haplogroup_df, meta_df)
        
        merged_df.to_csv(output_file, index=False)
        logger.info(f"Merged dataset saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error merging datasets: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
