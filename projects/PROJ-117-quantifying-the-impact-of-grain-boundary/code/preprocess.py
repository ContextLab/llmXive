import logging
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np

from models.grain_boundary_record import GrainBoundaryRecord
from utils import setup_logging, load_metadata, update_metadata_entry, save_metadata, raise_data_insufficiency
from error_handling import DataInsufficiencyError, exit_on_insufficiency
from data_streamer import stream_data_source

# Configure logging
logger = setup_logging(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PARSED_GEOMETRY_PATH = PROJECT_ROOT / "data" / "processed" / "parsed_geometry.parquet"
CLEANED_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.parquet"
EXCLUSION_REPORT_PATH = PROJECT_ROOT / "artifacts" / "reports" / "exclusion_report.json"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.yaml"
SAMPLE_CONFIG_PATH = PROJECT_ROOT / "data" / "sample_config.yaml"

def load_parsed_data() -> pd.DataFrame:
    """Load the parsed geometry data from the parquet file."""
    if not PARSED_GEOMETRY_PATH.exists():
        raise FileNotFoundError(f"Parsed geometry file not found at {PARSED_GEOMETRY_PATH}. Run T010 first.")
    
    logger.info(f"Loading parsed geometry data from {PARSED_GEOMETRY_PATH}")
    df = pd.read_parquet(PARSED_GEOMETRY_PATH)
    logger.info(f"Loaded {len(df)} records from parsed geometry file.")
    return df

def validate_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter records with missing required features.
    
    Required features:
    - misorientation_angle
    - boundary_plane_normal (h, k, l)
    - sigma_value (calculated or extracted)
    - temperature
    - composition
    - diffusivity
    - boundary_width
    - excess_volume
    
    Returns:
        Tuple of (cleaned_df, exclusion_counts)
    """
    required_features = [
        'misorientation_angle', 
        'boundary_plane_normal_h', 'boundary_plane_normal_k', 'boundary_plane_normal_l',
        'sigma_value',
        'temperature', 
        'composition', 
        'diffusivity', 
        'boundary_width', 
        'excess_volume'
    ]
    
    exclusion_counts = {feature: 0 for feature in required_features}
    total_records = len(df)
    
    # Track which rows are dropped and why
    dropped_indices = set()
    exclusion_details = {feature: [] for feature in required_features}
    
    # Check each required feature
    for feature in required_features:
        if feature in ['boundary_plane_normal_h', 'boundary_plane_normal_k', 'boundary_plane_normal_l']:
            # Check if any of the normal components are missing
            mask = df[feature].isna()
            missing_indices = df[mask].index.tolist()
            exclusion_counts[feature] = len(missing_indices)
            for idx in missing_indices:
                if idx not in dropped_indices:
                    dropped_indices.add(idx)
                    exclusion_details[feature].append(idx)
        else:
            mask = df[feature].isna()
            missing_indices = df[mask].index.tolist()
            exclusion_counts[feature] = len(missing_indices)
            for idx in missing_indices:
                if idx not in dropped_indices:
                    dropped_indices.add(idx)
                    exclusion_details[feature].append(idx)
    
    # Also specifically check for missing Sigma values and boundary plane normals as requested by T037
    sigma_missing_mask = df['sigma_value'].isna()
    boundary_plane_missing_mask = (
        df['boundary_plane_normal_h'].isna() | 
        df['boundary_plane_normal_k'].isna() | 
        df['boundary_plane_normal_l'].isna()
    )
    
    sigma_missing_count = sigma_missing_mask.sum()
    boundary_plane_missing_count = boundary_plane_missing_mask.sum()
    
    # Log the specific counts for T037 transparency
    logger.info(f"Records excluded due to missing Sigma value: {sigma_missing_count}")
    logger.info(f"Records excluded due to missing boundary plane normal: {boundary_plane_missing_count}")
    
    # Verify these counts are non-zero if the dataset is incomplete (transparency check)
    if sigma_missing_count > 0 or boundary_plane_missing_count > 0:
        logger.warning(
            f"Data filtering found incomplete records: {sigma_missing_count} missing Sigma, "
            f"{boundary_plane_missing_count} missing boundary plane normal. "
            f"Total records dropped: {len(dropped_indices)}."
        )
    
    # Drop rows with any missing required features
    cleaned_df = df.drop(index=list(dropped_indices))
    final_count = len(cleaned_df)
    
    logger.info(f"Validation complete. Started with {total_records} records, "
                f"dropped {len(dropped_indices)}, kept {final_count} records.")
    
    return cleaned_df, exclusion_counts

def tag_metadata_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tag simulation_method and potential_id as features.
    
    This function ensures that metadata fields are properly tagged for feature engineering.
    """
    # Ensure simulation_method column exists, default to 'unknown' if not present
    if 'simulation_method' not in df.columns:
        df['simulation_method'] = 'unknown'
    
    # Ensure potential_id column exists, default to 'unknown' if not present
    if 'potential_id' not in df.columns:
        df['potential_id'] = 'unknown'
    
    logger.info("Tagged simulation_method and potential_id as features.")
    return df

def apply_sampling(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply deterministic sampling if dataset is too large.
    
    Reads sampling strategy from data/sample_config.yaml.
    """
    if not SAMPLE_CONFIG_PATH.exists():
        logger.warning("Sample config not found. Skipping sampling.")
        return df
    
    try:
        import yaml
        with open(SAMPLE_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        sampling_strategy = config.get('sampling', {})
        strategy_type = sampling_strategy.get('type', 'none')
        
        if strategy_type == 'none':
            return df
        
        if strategy_type == 'first_n':
            n = sampling_strategy.get('n', 1000)
            logger.info(f"Applying 'first_n' sampling: keeping first {n} rows.")
            return df.head(n)
        
        elif strategy_type == 'random_sample':
            seed = sampling_strategy.get('seed', 42)
            n = sampling_strategy.get('n', 1000)
            logger.info(f"Applying 'random_sample' with seed {seed}, keeping {n} rows.")
            np.random.seed(seed)
            return df.sample(n=min(n, len(df)), random_state=seed)
        
        else:
            logger.warning(f"Unknown sampling strategy: {strategy_type}. Skipping.")
            return df
            
    except Exception as e:
        logger.error(f"Error applying sampling: {e}")
        return df

def enforce_minimum_records(df: pd.DataFrame, min_records: int = 500) -> pd.DataFrame:
    """
    Enforce the n >= 500 constraint.
    
    If fewer than min_records remain, log the error and exit with code 1.
    """
    if len(df) < min_records:
        error_msg = (
            f"Data Insufficiency: Retrieved {len(df)}, Valid {len(df)}, Required {min_records}. "
            f"Missing features: See exclusion report for details."
        )
        logger.error(error_msg)
        raise DataInsufficiencyError(error_msg)
    
    logger.info(f"Data sufficiency check passed: {len(df)} records >= {min_records} required.")
    return df

def write_exclusion_report(exclusion_counts: Dict[str, int], dropped_indices: List[int] = None):
    """
    Write the exclusion count and details to artifacts/reports/exclusion_report.json.
    """
    EXCLUSION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "total_excluded": sum(exclusion_counts.values()),
        "exclusion_counts_by_feature": exclusion_counts,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    if dropped_indices:
        report["dropped_indices_sample"] = dropped_indices[:100]  # Limit sample size
        report["total_dropped_indices"] = len(dropped_indices)
    
    with open(EXCLUSION_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Exclusion report written to {EXCLUSION_REPORT_PATH}")

def save_cleaned_data(df: pd.DataFrame):
    """Save the cleaned dataset to parquet."""
    CLEANED_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEANED_DATASET_PATH, index=False)
    logger.info(f"Cleaned dataset saved to {CLEANED_DATASET_PATH} ({len(df)} records).")

def main():
    """Main entry point for the preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline (T011)...")
    
    try:
        # 1. Load parsed data
        df = load_parsed_data()
        
        # 2. Validate features and get exclusion counts
        cleaned_df, exclusion_counts = validate_features(df)
        
        # 3. Tag metadata features
        cleaned_df = tag_metadata_features(cleaned_df)
        
        # 4. Apply sampling if needed
        cleaned_df = apply_sampling(cleaned_df)
        
        # 5. Enforce minimum record count
        cleaned_df = enforce_minimum_records(cleaned_df)
        
        # 6. Write exclusion report
        # Note: We need to reconstruct dropped_indices for the report if we want to include them
        # For now, we pass the counts
        write_exclusion_report(exclusion_counts)
        
        # 7. Save cleaned data
        save_cleaned_data(cleaned_df)
        
        logger.info("Preprocessing pipeline completed successfully.")
        return 0
        
    except DataInsufficiencyError as e:
        logger.error(f"Data insufficiency error: {e}")
        exit_on_insufficiency(str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())