"""
Data validation module for plant defense compound prediction pipeline.
Merges datasets, performs listwise deletion, and validates data integrity.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np

from config import get_config
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError

logger = get_module_logger(__name__)

def load_json_data(file_path: Path) -> pd.DataFrame:
    """
    Load JSON data into a pandas DataFrame.
    
    Args:
        file_path: Path to JSON file.
        
    Returns:
        DataFrame.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def merge_datasets(
    genomic_df: pd.DataFrame,
    env_df: pd.DataFrame,
    compound_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge genomic, environmental, and compound datasets.
    
    Args:
        genomic_df: Genomic data DataFrame.
        env_df: Environmental data DataFrame.
        compound_df: Compound data DataFrame.
        
    Returns:
        Merged DataFrame.
    """
    logger.info("Merging datasets...")
    
    # Ensure all have population_id
    for df_name, df in [('genomic', genomic_df), ('env', env_df), ('compound', compound_df)]:
        if 'population_id' not in df.columns:
            logger.error(f"{df_name} data missing 'population_id' column.")
            raise ValueError(f"{df_name} data must contain 'population_id'")
    
    # Merge sequentially
    merged = genomic_df.merge(env_df, on='population_id', how='inner')
    merged = merged.merge(compound_df, on='population_id', how='inner')
    
    logger.info(f"Merged data shape: {merged.shape}")
    return merged

def perform_listwise_deletion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform listwise deletion for missing modalities (FR-003).
    
    Removes rows with any missing values across key columns.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with complete cases only.
    """
    logger.info("Performing listwise deletion...")
    
    initial_count = len(df)
    df_clean = df.dropna()
    final_count = len(df_clean)
    
    excluded = initial_count - final_count
    logger.info(f"Excluded {excluded} rows ({excluded/initial_count*100:.1f}%) due to missing data.")
    
    return df_clean

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """
    Validate data integrity: check for required columns and non-null IDs.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    required_cols = ['population_id', 'env_id', 'compound_id']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
        if df[col].isnull().any():
            logger.error(f"Column {col} contains null values.")
            return False
    
    logger.info("Data integrity validation passed.")
    return True

def calculate_retention_percentage(initial_count: int, final_count: int) -> float:
    """
    Calculate retention percentage after listwise deletion.
    
    Args:
        initial_count: Initial number of rows.
        final_count: Final number of rows.
        
    Returns:
        Retention percentage.
    """
    if initial_count == 0:
        return 0.0
    return (final_count / initial_count) * 100

def run_validation_pipeline(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Run the full validation pipeline.
    
    Steps:
    1. Load JSON data files.
    2. Merge datasets.
    3. Perform listwise deletion.
    4. Validate integrity and calculate retention.
    
    Args:
        config: Optional configuration dictionary.
        
    Returns:
        0 on success, non-zero on failure.
    """
    if config is None:
        config = get_config()
    
    try:
        logger.info("Starting validation pipeline...")
        
        raw_dir = Path(config.get('paths', {}).get('raw', 'data/raw'))
        processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        genomic_path = raw_dir / 'genomic_vcf.json'
        env_path = raw_dir / 'env_data.json'
        compound_path = raw_dir / 'compound_data.json'
        
        if not all([genomic_path.exists(), env_path.exists(), compound_path.exists()]):
            logger.error("Raw data files not found. Run ingestion first.")
            return 1
        
        genomic_df = load_json_data(genomic_path)
        env_df = load_json_data(env_path)
        compound_df = load_json_data(compound_path)
        
        # Merge
        merged_df = merge_datasets(genomic_df, env_df, compound_df)
        
        initial_count = len(merged_df)
        
        # Listwise deletion
        clean_df = perform_listwise_deletion(merged_df)
        final_count = len(clean_df)
        
        retention = calculate_retention_percentage(initial_count, final_count)
        logger.info(f"Retention percentage: {retention:.1f}%")
        
        # Validate integrity
        if not validate_data_integrity(clean_df):
            logger.error("Data integrity validation failed.")
            return 1
        
        # Save filtered data
        filtered_path = processed_dir / 'filtered.csv'
        clean_df.to_csv(filtered_path, index=False)
        logger.info(f"Filtered data saved to {filtered_path}")
        
        # Check retention threshold (SC-001)
        if retention < 80:
            logger.warning(f"Retention ({retention:.1f}%) is below 80% threshold.")
            # Do not raise SystemExit here; let T014 handle it if needed
        
        check_disk_space(filtered_path.stat().st_size)
        
        return 0
        
    except DiskSpaceError as e:
        logger.error(f"Validation failed due to disk space: {e}")
        return 2
    except Exception as e:
        logger.error(f"Validation pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main(*args, **kwargs) -> int:
    """
    Main entry point for validation module.
    """
    from utils.logging import configure_root_logger
    configure_root_logger()
    
    config = get_config()
    if args and isinstance(args[0], dict):
        config = args[0]
    elif 'config' in kwargs:
        config = kwargs['config']
    
    return run_validation_pipeline(config)

if __name__ == '__main__':
    sys.exit(main())
