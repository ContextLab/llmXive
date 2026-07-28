"""
feature_save.py

Task: T016 [US1] Save final feature-rich dataset to `data/processed/features.csv`.

This module orchestrates the final step of User Story 1:
1. Ensures the raw feature data (from T013/T014) exists.
2. Ensures the validation flags (from T015) exist.
3. Merges them into a single DataFrame.
4. Saves the result to `data/processed/features.csv`.
5. Logs the operation and verifies the output file exists.
"""
import os
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules as per API surface
from features import run_feature_extraction
from validation_logic import run_t015_validation_pipeline
from config import get_config
from validation import check_pipeline_limit, get_tracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_feature_data_exists(config: Dict[str, Any]) -> Path:
    """
    Ensures that the raw feature data exists.
    If not, it triggers the feature extraction pipeline (T014) or ingestion (T013).
    For T016, we assume T013 and T014 have run, but we verify existence.
    """
    raw_features_path = Path(config['paths']['raw_features'])
    
    if not raw_features_path.exists():
        logger.warning(f"Raw feature data not found at {raw_features_path}. "
                       "Attempting to run feature extraction pipeline.")
        # Trigger feature extraction if missing
        run_feature_extraction(config)
    
    if not raw_features_path.exists():
        raise FileNotFoundError(
            f"Feature data file {raw_features_path} does not exist after "
            "attempting extraction. Ensure T013 (ingestion) and T014 (features) "
            "have been completed successfully."
        )
    
    logger.info(f"Feature data found at {raw_features_path}")
    return raw_features_path

def ensure_validation_data_exists(config: Dict[str, Any]) -> Path:
    """
    Ensures that the validation data (T015 flags) exists.
    If not, triggers the validation logic.
    """
    validation_path = Path(config['paths']['validation_flags'])
    
    if not validation_path.exists():
        logger.warning(f"Validation flags not found at {validation_path}. "
                       "Attempting to run T015 validation pipeline.")
        run_t015_validation_pipeline(config)
    
    if not validation_path.exists():
        raise FileNotFoundError(
            f"Validation flags file {validation_path} does not exist. "
            "Ensure T015 has been completed."
        )
    
    logger.info(f"Validation data found at {validation_path}")
    return validation_path

def merge_and_save_features(config: Dict[str, Any]) -> Path:
    """
    Merges raw features and validation flags, then saves to the final processed location.
    """
    import pandas as pd

    features_path = ensure_feature_data_exists(config)
    validation_path = ensure_validation_data_exists(config)
    
    # Load raw features
    logger.info(f"Loading features from {features_path}")
    df_features = pd.read_csv(features_path)
    
    # Load validation flags
    logger.info(f"Loading validation flags from {validation_path}")
    df_validation = pd.read_csv(validation_path)
    
    # Merge on prompt_id
    if 'prompt_id' not in df_features.columns or 'prompt_id' not in df_validation.columns:
        raise ValueError("Both feature and validation files must contain 'prompt_id' column.")
    
    logger.info(f"Merging datasets on 'prompt_id'. "
                f"Features shape: {df_features.shape}, Validation shape: {df_validation.shape}")
    
    df_merged = pd.merge(
        df_features, 
        df_validation, 
        on='prompt_id', 
        how='left'  # Keep all features, add flags where available
    )
    
    # Fill NaN in validation columns with False/0 if appropriate, 
    # though T015 should flag all rows. 
    # Assuming T015 adds 'has_undefined_imperative_ratio' (bool)
    # and 'imperative_ratio' (float, might be NaN if undefined)
    
    # Ensure final output directory exists
    output_dir = Path(config['paths']['processed_features']).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = Path(config['paths']['processed_features'])
    
    # Save to CSV
    logger.info(f"Saving merged dataset to {output_path}")
    df_merged.to_csv(output_path, index=False)
    
    # Verify output
    if not output_path.exists():
        raise RuntimeError(f"Failed to write output file to {output_path}")
    
    logger.info(f"Successfully saved {len(df_merged)} rows to {output_path}")
    return output_path

def main():
    """
    Entry point for T016.
    """
    logger.info("Starting T016: Saving final feature-rich dataset.")
    
    # Check pipeline time limit
    if not check_pipeline_limit():
        logger.error("Pipeline time limit exceeded. Aborting T016.")
        sys.exit(1)
    
    try:
        config = get_config()
        
        # Ensure paths are set correctly in config if not already
        # (Assuming config.py handles defaults, but we can enforce here)
        if 'paths' not in config:
            config['paths'] = {}
        
        # Define paths based on project structure
        # Assuming config has defaults, but we map them explicitly for T016
        base_path = Path(config.get('project_root', '.'))
        
        # Default paths if not in config (fallback)
        paths = config.get('paths', {})
        paths['raw_features'] = paths.get('raw_features', str(base_path / 'data' / 'interim' / 'features_raw.csv'))
        paths['validation_flags'] = paths.get('validation_flags', str(base_path / 'data' / 'interim' / 'validation_flags.csv'))
        paths['processed_features'] = paths.get('processed_features', str(base_path / 'data' / 'processed' / 'features.csv'))
        
        config['paths'] = paths
        
        output_path = merge_and_save_features(config)
        
        logger.info(f"T016 completed successfully. Output: {output_path}")
        
    except Exception as e:
        logger.exception(f"T016 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
