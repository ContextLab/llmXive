import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config.environment import get_local_paths, ensure_directories

logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    paths = get_local_paths()
    ensure_directories(paths)

def load_burden_data():
    """
    Load the processed heteroplasmy burden data.
    Expected location: data/processed/heteroplasmy_burden.csv
    """
    paths = get_local_paths()
    burden_path = paths['data_processed'] / 'heteroplasmy_burden.csv'
    
    if not burden_path.exists():
        raise FileNotFoundError(f"Burden data file not found at {burden_path}. "
                                "Run load_data.py and preprocess.py first.")
    
    logger.info(f"Loading burden data from {burden_path}")
    df = pd.read_csv(burden_path)
    return df

def load_haplogroup_data():
    """
    Load the haplogroup assignments.
    Expected location: data/processed/haplogroups.csv
    """
    paths = get_local_paths()
    haplogroup_path = paths['data_processed'] / 'haplogroups.csv'
    
    if not haplogroup_path.exists():
        raise FileNotFoundError(f"Haplogroup data file not found at {haplogroup_path}. "
                                "Run preprocess.py first.")
    
    logger.info(f"Loading haplogroup data from {haplogroup_path}")
    df = pd.read_csv(haplogroup_path)
    return df

def load_metadata_panel():
    """
    Load the metadata panel containing age, sex, population, and PCs.
    Expected location: data/raw/1000G_phase3_sample_info.tsv (or similar)
    This function assumes the metadata has been downloaded by load_data.py.
    """
    paths = get_local_paths()
    # The metadata file is typically downloaded to data/raw
    # We look for the standard 1000 Genomes sample info file
    metadata_path = paths['data_raw'] / 'phase3_sample_info.tsv'
    
    if not metadata_path.exists():
        # Fallback to other common names if the specific file isn't found
        # This handles cases where the filename might differ slightly
        possible_names = [
            '1000G_phase3_sample_info.tsv',
            'sample_info.tsv',
            'metadata.tsv'
        ]
        for name in possible_names:
            alt_path = paths['data_raw'] / name
            if alt_path.exists():
                metadata_path = alt_path
                break
        else:
            raise FileNotFoundError(
                f"Metadata panel not found in {paths['data_raw']}. "
                "Ensure load_data.py has downloaded the metadata."
            )
    
    logger.info(f"Loading metadata panel from {metadata_path}")
    df = pd.read_csv(metadata_path, sep='\t')
    return df

def merge_datasets():
    """
    Merge burden data, haplogroups, and metadata panel into a single analysis-ready dataset.
    
    Returns:
        pd.DataFrame: Merged dataset with columns for burden, haplogroup, age, sex, population, PCs
    
    Raises:
        FileNotFoundError: If any required input files are missing
        ValueError: If required columns are missing in input files
    """
    # Load all source data
    burden_df = load_burden_data()
    haplogroup_df = load_haplogroup_data()
    metadata_df = load_metadata_panel()
    
    logger.info(f"Burden data shape: {burden_df.shape}")
    logger.info(f"Haplogroup data shape: {haplogroup_df.shape}")
    logger.info(f"Metadata data shape: {metadata_df.shape}")
    
    # Ensure sample IDs are consistent (strip any potential whitespace)
    if 'sample_id' in burden_df.columns:
        burden_df['sample_id'] = burden_df['sample_id'].astype(str).str.strip()
    if 'sample_id' in haplogroup_df.columns:
        haplogroup_df['sample_id'] = haplogroup_df['sample_id'].astype(str).str.strip()
    if 'sample_id' in metadata_df.columns:
        metadata_df['sample_id'] = metadata_df['sample_id'].astype(str).str.strip()
    
    # Start with burden data as the base (since it's the primary analysis target)
    merged = burden_df.copy()
    
    # Merge with haplogroup data
    merged = merged.merge(
        haplogroup_df[['sample_id', 'haplogroup']],
        on='sample_id',
        how='left'
    )
    
    # Merge with metadata panel
    # We need to map metadata columns to our expected names
    # Common metadata columns: sample_id, age, sex, superpopulation, PC1-PC10
    merged = merged.merge(
        metadata_df,
        on='sample_id',
        how='left'
    )
    
    # Standardize column names if needed
    # Check for common metadata column name variations
    col_mapping = {}
    if 'superpopulation' in merged.columns:
        col_mapping['superpopulation'] = 'population'
    if 'SEX' in merged.columns:
        col_mapping['SEX'] = 'sex'
    if 'AGE' in merged.columns:
        col_mapping['AGE'] = 'age'
    
    merged = merged.rename(columns=col_mapping)
    
    # Verify required columns exist
    required_cols = ['sample_id', 'heteroplasmy_burden', 'haplogroup', 'age', 'sex', 'population']
    missing_cols = [col for col in required_cols if col not in merged.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in merged dataset: {missing_cols}")
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    logger.info(f"Columns: {list(merged.columns)}")
    
    return merged

def main():
    """Main entry point for merging metadata."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        ensure_dirs()
        merged_df = merge_datasets()
        
        # Write to output file
        paths = get_local_paths()
        output_path = paths['data_processed'] / 'mito_aging_dataset.csv'
        
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote merged dataset to {output_path}")
        logger.info(f"Total samples: {len(merged_df)}")
        
        return merged_df
        
    except Exception as e:
        logger.error(f"Failed to merge datasets: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
