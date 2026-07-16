import logging
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from utils import setup_logging, raise_data_insufficiency
from error_handling import check_data_sufficiency, exit_on_insufficiency
from models.grain_boundary_record import GrainBoundaryRecord
from data_streamer import stream_data_source

logger = setup_logging("preprocess")

# Required features for a valid record
REQUIRED_FEATURES = [
    'misorientation_angle',
    'rodrigues_vector',
    'boundary_plane_normal_h',
    'boundary_plane_normal_k',
    'boundary_plane_normal_l',
    'sigma_value',
    'temperature',
    'composition',
    'diffusivity',
    'boundary_width',
    'excess_volume',
    'simulation_method',
    'potential_id'
]

def load_parsed_data(parsed_path: str) -> pd.DataFrame:
    """Load the parsed geometry data from parquet."""
    path = Path(parsed_path)
    if not path.exists():
        raise FileNotFoundError(f"Parsed geometry file not found: {parsed_path}")
    
    # Use streaming if file is large, otherwise load directly
    # For simplicity in this implementation, we load directly but handle errors
    try:
        df = pd.read_parquet(parsed_path)
        logger.info(f"Loaded {len(df)} records from {parsed_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parsed data: {e}")
        raise

def validate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter records with missing required features.
    Returns cleaned dataframe and list of missing feature names found.
    """
    missing_features = []
    
    # Check which required columns exist
    existing_cols = set(df.columns)
    required_set = set(REQUIRED_FEATURES)
    missing_cols = required_set - existing_cols
    
    if missing_cols:
        logger.warning(f"Missing columns in dataset: {missing_cols}")
        missing_features.extend(missing_cols)
    
    # Filter rows where any required feature is NaN or None
    valid_mask = pd.Series([True] * len(df), index=df.index)
    
    for feature in REQUIRED_FEATURES:
        if feature in df.columns:
            # Handle different types of missing values
            valid_mask &= df[feature].notna()
            # Also check for specific invalid values like NaN in sigma_value
            if feature == 'sigma_value':
                valid_mask &= (df[feature] != np.nan)
                # Check for NaN specifically
                valid_mask &= ~df[feature].isna()
            # For rodrigues_vector, check if it's a valid array/tuple
            elif feature == 'rodrigues_vector':
                def is_valid_vector(val):
                    if pd.isna(val):
                        return False
                    if isinstance(val, (list, tuple, np.ndarray)):
                        return len(val) == 3 and not any(pd.isna(x) for x in val)
                    return False
                valid_mask &= df[feature].apply(is_valid_vector)
    
    cleaned_df = df[valid_mask].reset_index(drop=True)
    excluded_count = len(df) - len(cleaned_df)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} records due to missing required features")
    
    return cleaned_df, missing_features

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """Tag simulation_method and potential_id as features if not already present."""
    # These should already be in the dataset from download/geometry_parser
    # If not, we ensure they exist as columns (might be NaN)
    if 'simulation_method' not in df.columns:
        df['simulation_method'] = None
        logger.warning("simulation_method column not found, adding as None")
    
    if 'potential_id' not in df.columns:
        df['potential_id'] = None
        logger.warning("potential_id column not found, adding as None")
    
    return df

def apply_sampling(df: pd.DataFrame, sample_config_path: str = "data/sample_config.yaml") -> pd.DataFrame:
    """Apply deterministic sampling if dataset is too large."""
    sample_config = Path(sample_config_path)
    
    if not sample_config.exists():
        logger.info("No sample_config.yaml found, using full dataset")
        return df
    
    try:
        import yaml
        with open(sample_config, 'r') as f:
            config = yaml.safe_load(f)
        
        if config and 'strategy' in config:
            strategy = config['strategy']
            n_samples = config.get('n_samples', 1000)
            
            if strategy == 'islice' and n_samples < len(df):
                logger.info(f"Applying islice sampling: taking first {n_samples} rows")
                return df.head(n_samples)
            elif strategy == 'random' and n_samples < len(df):
                seed = config.get('seed', 42)
                logger.info(f"Applying random sampling: {n_samples} rows with seed {seed}")
                return df.sample(n=n_samples, random_state=seed)
    except Exception as e:
        logger.warning(f"Failed to apply sampling strategy: {e}, using full dataset")
    
    return df

def enforce_minimum_records(df: pd.DataFrame, min_records: int = 500) -> Tuple[pd.DataFrame, bool]:
    """
    Enforce n >= 500 constraint.
    Returns (df, success) where success is False if insufficient records.
    """
    valid_count = len(df)
    
    if valid_count < min_records:
        logger.error(f"Data Insufficiency: Retrieved {valid_count}, Valid {valid_count}, Required {min_records}")
        return df, False
    
    logger.info(f"Data sufficiency check passed: {valid_count} >= {min_records}")
    return df, True

def write_exclusion_report(excluded_count: int, missing_features: List[str], output_path: str = "artifacts/reports/exclusion_report.json"):
    """Write the exclusion report to satisfy FR-006."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "excluded_count": excluded_count,
        "missing_features": missing_features,
        "timestamp": pd.Timestamp.now().isoformat(),
        "reason": "Records excluded due to missing required features"
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Wrote exclusion report to {output_path}")

def save_cleaned_data(df: pd.DataFrame, output_path: str = "data/processed/cleaned_dataset.parquet"):
    """Save the cleaned dataset to parquet."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved cleaned dataset with {len(df)} records to {output_path}")

def main():
    """Main entry point for preprocessing."""
    parsed_path = "data/processed/parsed_geometry.parquet"
    output_path = "data/processed/cleaned_dataset.parquet"
    
    try:
        # Load parsed data
        df = load_parsed_data(parsed_path)
        
        # Validate and filter features
        cleaned_df, missing_features = validate_features(df)
        
        # Tag metadata features
        cleaned_df = tag_metadata_features(cleaned_df)
        
        # Apply sampling if needed
        cleaned_df = apply_sampling(cleaned_df)
        
        # Check minimum records
        final_df, success = enforce_minimum_records(cleaned_df, min_records=500)
        
        if not success:
            # Write exclusion report before exiting
            write_exclusion_report(
                excluded_count=len(df) - len(final_df),
                missing_features=missing_features
            )
            # Raise the insufficiency error
            raise_data_insufficiency(
                retrieved=len(df),
                required=500,
                missing_features=missing_features
            )
        
        # Save cleaned data
        save_cleaned_data(final_df, output_path)
        
        logger.info("Preprocessing completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()