import logging
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from utils import setup_logging, compute_sha256, set_random_seed, load_metadata, update_metadata_entry, save_metadata
from error_handling import DataInsufficiencyError, check_data_sufficiency, exit_on_insufficiency
from data_streamer import stream_data_source

# Ensure output directories exist
OUTPUT_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("artifacts/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger = setup_logging("preprocess")

def load_parsed_data() -> pd.DataFrame:
    """
    Load the parsed geometry data from the intermediate parquet file.
    """
    input_path = Path("data/processed/parsed_geometry.parquet")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading parsed geometry data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parsed geometry data: {e}")
        raise

def validate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter records with missing required features and log exclusion counts.
    Required features: misorientation, boundary_plane_normal, sigma_value, 
    temperature, composition, diffusivity, boundary_width, excess_volume.
    
    Returns:
        Tuple of (filtered_df, exclusion_counts)
    """
    required_features = [
        'misorientation_angle', 
        'boundary_plane_normal', 
        'sigma_value', 
        'temperature', 
        'composition', 
        'diffusivity', 
        'boundary_width', 
        'excess_volume'
    ]
    
    # Track missing counts for specific critical features
    critical_features = ['sigma_value', 'boundary_plane_normal']
    exclusion_counts = {feature: 0 for feature in critical_features}
    
    # Log initial state
    initial_count = len(df)
    logger.info(f"Starting validation with {initial_count} records")
    
    # Identify rows with missing critical features
    missing_critical_mask = pd.Series([False] * len(df), index=df.index)
    
    for feature in critical_features:
        if feature not in df.columns:
            logger.warning(f"Critical feature '{feature}' not found in dataset.")
            exclusion_counts[feature] = initial_count
            missing_critical_mask = pd.Series([True] * len(df), index=df.index)
        else:
            # Check for NaN, None, or empty strings
            mask = df[feature].isna() | (df[feature].apply(lambda x: x is None))
            if feature == 'boundary_plane_normal':
                # Boundary plane normal might be a tuple/list; check if empty
                mask |= df[feature].apply(lambda x: isinstance(x, (list, tuple)) and len(x) == 0)
            
            count_missing = mask.sum()
            exclusion_counts[feature] = count_missing
            logger.info(f"Found {count_missing} records with missing '{feature}'")
            
            missing_critical_mask |= mask

    # Filter out rows with missing critical features
    filtered_df = df[~missing_critical_mask].copy()
    
    # Now check other required features
    for feature in required_features:
        if feature not in df.columns:
            if feature not in critical_features:
                logger.warning(f"Required feature '{feature}' not found in dataset.")
        else:
            mask = filtered_df[feature].isna() | (filtered_df[feature].apply(lambda x: x is None))
            if feature == 'boundary_plane_normal' or feature == 'sigma_value':
                # Already handled above
                continue
            if feature == 'boundary_plane_normal':
                mask |= filtered_df[feature].apply(lambda x: isinstance(x, (list, tuple)) and len(x) == 0)
            
            count_missing = mask.sum()
            if count_missing > 0:
                logger.info(f"Found {count_missing} additional records with missing '{feature}'")
                filtered_df = filtered_df[~mask]
    
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count
    
    logger.info(f"Validation complete. Excluded {excluded_count} records.")
    logger.info(f"Remaining valid records: {final_count}")
    
    return filtered_df, exclusion_counts

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tag simulation_method and potential_id as features if they exist.
    """
    metadata_cols = ['simulation_method', 'potential_id']
    for col in metadata_cols:
        if col in df.columns:
            logger.info(f"Tagging '{col}' as a feature")
            # Ensure they are treated as categorical features
            df[col] = df[col].astype('category')
        else:
            logger.debug(f"Feature '{col}' not found in dataset, skipping.")
    
    return df

def apply_sampling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply deterministic sampling if dataset is too large.
    Reads sampling strategy from data/sample_config.yaml.
    """
    sample_config_path = Path("data/sample_config.yaml")
    
    if not sample_config_path.exists():
        logger.info("No sample_config.yaml found. Using full dataset.")
        return df
    
    try:
        import yaml
        with open(sample_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        strategy = config.get('strategy', 'full')
        sample_size = config.get('sample_size', None)
        
        if strategy == 'full':
            logger.info("Sampling strategy is 'full'. Using full dataset.")
            return df
        elif strategy == 'head':
            if sample_size is None:
                logger.warning("Strategy 'head' specified but sample_size is None. Using full dataset.")
                return df
            logger.info(f"Sampling first {sample_size} rows.")
            return df.head(sample_size)
        elif strategy == 'random':
            if sample_size is None:
                logger.warning("Strategy 'random' specified but sample_size is None. Using full dataset.")
                return df
            seed = config.get('seed', 42)
            logger.info(f"Sampling {sample_size} random rows with seed {seed}.")
            return df.sample(n=sample_size, random_state=seed)
        else:
            logger.warning(f"Unknown sampling strategy '{strategy}'. Using full dataset.")
            return df
            
    except Exception as e:
        logger.error(f"Failed to apply sampling: {e}")
        logger.info("Falling back to full dataset.")
        return df

def enforce_minimum_records(df: pd.DataFrame, required: int = 500) -> None:
    """
    Enforce the n >= 500 constraint.
    Raises DataInsufficiencyError if fewer than required records remain.
    """
    count = len(df)
    if count < required:
        logger.error(f"Data Insufficiency: Retrieved {count}, Valid {count}, Required {required}.")
        # Determine missing features based on validation logic
        missing_features = []
        if 'sigma_value' not in df.columns or df['sigma_value'].isna().any():
            missing_features.append('sigma_value')
        if 'boundary_plane_normal' not in df.columns or df['boundary_plane_normal'].isna().any():
            missing_features.append('boundary_plane_normal')
        # Check other required features
        required_features = ['misorientation_angle', 'temperature', 'composition', 'diffusivity']
        for feat in required_features:
            if feat in df.columns and df[feat].isna().any():
                missing_features.append(feat)
        
        exit_on_insufficiency(retrieved=count, required=required, missing_features=missing_features)
    else:
        logger.info(f"Data sufficiency check passed: {count} >= {required}")

def write_exclusion_report(exclusion_counts: Dict[str, int], total_excluded: int) -> None:
    """
    Write exclusion report to artifacts/reports/exclusion_report.json.
    """
    report_path = ARTIFACTS_DIR / "exclusion_report.json"
    
    report_data = {
        "total_excluded": total_excluded,
        "exclusion_reasons": exclusion_counts,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    try:
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Exclusion report written to {report_path}")
    except Exception as e:
        logger.error(f"Failed to write exclusion report: {e}")

def save_cleaned_data(df: pd.DataFrame) -> None:
    """
    Save the cleaned dataset to data/processed/cleaned_dataset.parquet.
    """
    output_path = OUTPUT_DIR / "cleaned_dataset.parquet"
    
    try:
        df.to_parquet(output_path, index=False)
        logger.info(f"Cleaned dataset saved to {output_path}")
        
        # Compute checksum for metadata
        checksum = compute_sha256(output_path)
        logger.info(f"Checksum for cleaned dataset: {checksum}")
        
        # Update metadata
        update_metadata_entry(
            source="preprocess",
            version="1.0",
            checksum=checksum,
            retrieval_date=pd.Timestamp.now().isoformat(),
            record_count=len(df)
        )
        
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        raise

def main():
    """
    Main execution flow for preprocessing.
    """
    logger.info("Starting preprocessing pipeline")
    set_random_seed(42)
    
    try:
        # 1. Load parsed data
        df = load_parsed_data()
        
        # 2. Validate features and get exclusion counts
        df_valid, exclusion_counts = validate_features(df)
        
        # 3. Tag metadata features
        df_valid = tag_metadata_features(df_valid)
        
        # 4. Apply sampling if needed
        df_final = apply_sampling(df_valid)
        
        # 5. Enforce minimum record count
        enforce_minimum_records(df_final)
        
        # 6. Write exclusion report
        total_excluded = len(df) - len(df_final)
        write_exclusion_report(exclusion_counts, total_excluded)
        
        # 7. Save cleaned data
        save_cleaned_data(df_final)
        
        logger.info("Preprocessing pipeline completed successfully")
        
    except DataInsufficiencyError as e:
        logger.error(f"Data insufficiency error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == "__main__":
    main()