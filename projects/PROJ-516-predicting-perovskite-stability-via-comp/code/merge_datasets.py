import logging
import sys
from pathlib import Path
from typing import Tuple
import pandas as pd
from utils.state_manager import compute_sha256, update_artifact_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_csv_safe(file_path: Path) -> pd.DataFrame:
    """
    Load a CSV file safely.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        DataFrame
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file is empty or invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            raise ValueError(f"File is empty: {file_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        raise

def merge_perovskite_datasets(nrel_path: Path, mp_path: Path) -> pd.DataFrame:
    """
    Merge NREL and MP datasets based on formula and source.
    
    Args:
        nrel_path: Path to NREL CSV
        mp_path: Path to MP CSV
        
    Returns:
        Merged DataFrame
    """
    logger.info("Loading NREL dataset...")
    nrel_df = load_csv_safe(nrel_path)
    
    logger.info("Loading MP dataset...")
    mp_df = load_csv_safe(mp_path)
    
    # Ensure source column is present
    if 'source' not in nrel_df.columns:
        nrel_df['source'] = 'NREL'
    if 'source' not in mp_df.columns:
        mp_df['source'] = 'MaterialsProject'
    
    # Concatenate
    logger.info("Concatenating datasets...")
    merged_df = pd.concat([nrel_df, mp_df], ignore_index=True)
    
    # Log duplicate count
    initial_count = len(merged_df)
    # Drop duplicates based on formula and source
    merged_df = merged_df.drop_duplicates(subset=['formula', 'source'], keep='first')
    duplicates_removed = initial_count - len(merged_df)
    
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate entries.")
    else:
        logger.info("No duplicate entries found.")
    
    return merged_df

def main():
    """Main entry point for merging datasets."""
    logger.info("Starting T012c: Merge Datasets")
    
    nrel_path = Path("data/raw/nrel_perovskites.csv")
    mp_path = Path("data/raw/mp_perovskites.csv")
    output_path = Path("data/raw/perovskites_merged.csv")
    
    try:
        merged_df = merge_perovskite_datasets(nrel_path, mp_path)
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Merge failed: {e}")
        sys.exit(1)
    
    # Save merged dataset
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path} ({len(merged_df)} rows)")
    
    # Update state
    try:
        update_artifact_state(output_path)
        logger.info("State updated successfully.")
    except Exception as e:
        logger.warning(f"Failed to update state: {e}")
    
    logger.info("T012c completed successfully.")

if __name__ == "__main__":
    main()
