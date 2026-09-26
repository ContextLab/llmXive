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
    ensure_directories([paths['processed']])
    return paths

def load_burden_data():
    """Load the calculated heteroplasmy burden data."""
    paths = get_local_paths()
    burden_path = paths['processed'] / 'burden_per_sample.csv'
    if not burden_path.exists():
        raise FileNotFoundError(f"Burden data not found at {burden_path}. Run preprocessing first.")
    logger.info(f"Loading burden data from {burden_path}")
    return pd.read_csv(burden_path)

def load_haplogroup_data():
    """Load the assigned haplogroup data."""
    paths = get_local_paths()
    hg_path = paths['processed'] / 'haplogroups.csv'
    if not hg_path.exists():
        raise FileNotFoundError(f"Haplogroup data not found at {hg_path}. Run preprocessing first.")
    logger.info(f"Loading haplogroup data from {hg_path}")
    return pd.read_csv(hg_path)

def load_metadata_panel():
    """Load the 1000 Genomes metadata panel containing age, sex, population, PCs."""
    paths = get_local_paths()
    meta_path = paths['raw'] / 'metadata_panel.csv'
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata panel not found at {meta_path}. Download data first.")
    logger.info(f"Loading metadata panel from {meta_path}")
    df = pd.read_csv(meta_path)
    # Ensure 'age' column exists for validation (Phase 0 check)
    if 'age' not in df.columns:
        raise ValueError("Metadata panel missing 'age' column. Pipeline halted per Phase 0 gate.")
    return df

def merge_datasets():
    """
    Join burden, haplogroups, age, sex, population, and PCs into a single dataset.
    Writes merged dataframe to code/data/processed/mito_aging_dataset.csv.
    """
    paths = ensure_dirs()
    
    logger.info("Starting metadata merge...")
    
    # Load sources
    burden_df = load_burden_data()
    hg_df = load_haplogroup_data()
    meta_df = load_metadata_panel()

    # Standardize sample ID column names if necessary (assuming 'sample_id' is consistent)
    # If sources use different names, rename them here.
    # Assuming all use 'sample_id' based on typical pipeline flow.
    burden_df = burden_df.rename(columns={c: c.lower() for c in burden_df.columns})
    hg_df = hg_df.rename(columns={c: c.lower() for c in hg_df.columns})
    meta_df = meta_df.rename(columns={c: c.lower() for c in meta_df.columns})

    # Merge logic: Start with metadata (contains age, sex, population, PCs)
    # Join with burden
    merged = meta_df.merge(burden_df, on='sample_id', how='inner')
    logger.info(f"After burden merge: {len(merged)} samples")

    # Join with haplogroups
    merged = merged.merge(hg_df, on='sample_id', how='left') # Left join to keep samples even if HG failed (handled in exclusion logic)
    logger.info(f"After haplogroup merge: {len(merged)} samples")

    # Select and order columns for final output
    # Priority: sample_id, age, sex, population, PCs, burden, haplogroup
    priority_cols = ['sample_id', 'age', 'sex', 'population', 'pc1', 'pc2', 'pc3', 'pc4', 'pc5']
    # Add burden columns if they exist
    burden_cols = [c for c in merged.columns if 'burden' in c.lower() or 'vaf' in c.lower() or 'depth' in c.lower()]
    # Add haplogroup
    hg_cols = [c for c in merged.columns if 'haplogroup' in c.lower()]
    
    final_cols = priority_cols + burden_cols + hg_cols
    
    # Filter to only existing columns
    final_cols = [c for c in final_cols if c in merged.columns]
    # Add any remaining columns not in priority list
    remaining_cols = [c for c in merged.columns if c not in final_cols]
    final_cols.extend(remaining_cols)

    merged = merged[final_cols]

    output_path = paths['processed'] / 'mito_aging_dataset.csv'
    merged.to_csv(output_path, index=False)
    logger.info(f"Merged dataset written to {output_path} ({len(merged)} rows, {len(merged.columns)} columns)")
    
    return merged

def main():
    """Entry point for the merge script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_local_paths()['logs'] / 'merge_metadata.log')
        ]
    )
    
    try:
        result = merge_datasets()
        print(f"Merge complete. Rows: {len(result)}, Columns: {len(result.columns)}")
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise

if __name__ == '__main__':
    main()
