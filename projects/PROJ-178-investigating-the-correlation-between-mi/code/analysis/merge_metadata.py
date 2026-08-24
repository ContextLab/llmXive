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
    ensure_directories(paths['processed_data'])
    return paths

def load_burden_data(paths):
    """Load heteroplasmy burden data from preprocess output."""
    burden_path = paths['processed_data'] / 'burden_per_sample.csv'
    if not burden_path.exists():
        raise FileNotFoundError(f"Burden data not found at {burden_path}. Run preprocess.py first.")
    logger.info(f"Loading burden data from {burden_path}")
    df = pd.read_csv(burden_path)
    # Ensure sample ID column is consistent
    if 'sample_id' not in df.columns:
        # Try to infer if column name is different
        if 'SampleID' in df.columns:
            df.rename(columns={'SampleID': 'sample_id'}, inplace=True)
        else:
            raise ValueError("Burden data missing 'sample_id' column")
    return df

def load_haplogroup_data(paths):
    """Load haplogroup assignments from haplogrep2 output."""
    # Haplogrep2 typically outputs a specific format; we assume a standardized CSV
    hg_path = paths['processed_data'] / 'haplogroups.csv'
    if not hg_path.exists():
        raise FileNotFoundError(f"Haplogroup data not found at {hg_path}. Run preprocess.py (assign_haplogroups) first.")
    logger.info(f"Loading haplogroup data from {hg_path}")
    df = pd.read_csv(hg_path)
    if 'sample_id' not in df.columns:
        if 'SampleID' in df.columns:
            df.rename(columns={'SampleID': 'sample_id'}, inplace=True)
        else:
            raise ValueError("Haplogroup data missing 'sample_id' column")
    return df

def load_metadata_panel(paths):
    """Load 1000 Genomes metadata panel (age, sex, population, PCs)."""
    meta_path = paths['raw_data'] / 'metadata_panel.csv'
    if not meta_path.exists():
        # Fallback for downloaded metadata if named differently
        meta_path = paths['raw_data'] / 'phase3_sample_info.tsv'
        if meta_path.exists():
            df = pd.read_csv(meta_path, sep='\t')
        else:
            raise FileNotFoundError(f"Metadata panel not found at {paths['raw_data']}. Run load_data.py first.")
    else:
        df = pd.read_csv(meta_path)
    
    logger.info(f"Loading metadata panel from {meta_path}")
    
    # Standardize column names
    # Expected columns: sample_id, age, sex, population, PC1, PC2, ...
    rename_map = {}
    for col in df.columns:
        lower_col = col.lower()
        if 'sample' in lower_col and 'id' in lower_col:
            rename_map[col] = 'sample_id'
        elif 'age' in lower_col and 'years' not in lower_col:
            rename_map[col] = 'age'
        elif 'sex' in lower_col or 'gender' in lower_col:
            rename_map[col] = 'sex'
        elif 'population' in lower_col or 'superpopulation' in lower_col:
            rename_map[col] = 'population'
        elif 'pc1' in lower_col:
            rename_map[col] = 'PC1'
        elif 'pc2' in lower_col:
            rename_map[col] = 'PC2'
    
    if rename_map:
        df.rename(columns=rename_map, inplace=True)
    
    # Ensure sample_id is string for joining
    if 'sample_id' in df.columns:
        df['sample_id'] = df['sample_id'].astype(str)
    
    return df

def merge_datasets(burden_df, haplogroup_df, metadata_df):
    """
    Merge burden, haplogroups, and metadata into a single dataframe.
    Inner join on sample_id to ensure all rows have complete data for this stage.
    """
    logger.info("Merging datasets...")
    
    # Start with burden
    merged = burden_df.copy()
    
    # Merge haplogroups
    merged = merged.merge(haplogroup_df[['sample_id', 'haplogroup']], on='sample_id', how='inner')
    
    # Merge metadata
    merged = merged.merge(metadata_df, on='sample_id', how='inner')
    
    logger.info(f"Merged dataset shape: {merged.shape}")
    logger.info(f"Columns: {list(merged.columns)}")
    
    return merged

def main():
    """Main entry point for metadata merging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('code/logs/merge_metadata.log')
        ]
    )
    
    paths = ensure_dirs()
    
    try:
        burden_df = load_burden_data(paths)
        haplogroup_df = load_haplogroup_data(paths)
        metadata_df = load_metadata_panel(paths)
        
        merged_df = merge_datasets(burden_df, haplogroup_df, metadata_df)
        
        output_path = paths['processed_data'] / 'mito_aging_dataset.csv'
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote merged dataset to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to merge datasets: {e}")
        raise

if __name__ == "__main__":
    main()
