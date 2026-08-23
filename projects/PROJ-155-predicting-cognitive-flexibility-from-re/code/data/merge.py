import os
import logging
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from code.data.paths import get_processed_path, get_raw_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging, log_exclusion

logger = logging.getLogger(__name__)

def load_neuro_features() -> pd.DataFrame:
    """Load neuroimaging features from processed data."""
    processed_path = get_processed_path()
    neuro_features_path = os.path.join(processed_path, "neuro_features.csv")
    
    if not os.path.exists(neuro_features_path):
        raise FileNotFoundError(f"Neuro features file not found: {neuro_features_path}")
    
    df = pd.read_csv(neuro_features_path)
    logger.info(f"Loaded {len(df)} rows from neuro features")
    return df

def load_behavioral_scores() -> pd.DataFrame:
    """Load behavioral scores from raw data."""
    raw_path = get_raw_path()
    behavioral_path = os.path.join(raw_path, "HCP_1200", "behavioral_scores.csv")
    
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral scores file not found: {behavioral_path}")
    
    df = pd.read_csv(behavioral_path)
    logger.info(f"Loaded {len(df)} rows from behavioral scores")
    return df

def merge_datasets(neuro_df: pd.DataFrame, behavioral_df: pd.DataFrame) -> pd.DataFrame:
    """Merge neuroimaging and behavioral datasets on Subject_ID."""
    # Ensure Subject_ID is string for consistent merging
    neuro_df['Subject_ID'] = neuro_df['Subject_ID'].astype(str)
    behavioral_df['Subject_ID'] = behavioral_df['Subject_ID'].astype(str)
    
    merged_df = pd.merge(
        neuro_df,
        behavioral_df,
        on='Subject_ID',
        how='inner'
    )
    
    logger.info(f"Merged dataset has {len(merged_df)} rows")
    return merged_df

def validate_merged_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that merged dataset contains required columns."""
    required_columns = [
        'Subject_ID', 'Mean_FD', 'Age', 'Sex', 'Flexibility_Score', 'Total_Scan_Time'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    is_valid = len(missing_columns) == 0
    
    if not is_valid:
        logger.error(f"Missing required columns: {missing_columns}")
    
    return is_valid, missing_columns

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to snake_case to match Spec's Key Entities.
    Specifically renames 'Total Scan Time' to 'Total_Scan_Time'.
    """
    column_mapping = {
        'Total Scan Time': 'Total_Scan_Time',
        'Mean FD': 'Mean_FD',
        'Flexibility Score': 'Flexibility_Score',
        'Subject ID': 'Subject_ID'
    }
    
    # Only rename columns that exist
    existing_renames = {k: v for k, v in column_mapping.items() if k in df.columns}
    
    if existing_renames:
        logger.info(f"Renaming columns: {existing_renames}")
        df = df.rename(columns=existing_renames)
    else:
        logger.debug("No column renaming needed")
    
    return df

def filter_missing_behavioral_scores(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter out subjects with missing behavioral scores (NaN in Flexibility_Score).
    Logs excluded subjects to the exclusion log.
    
    Args:
        df: Merged dataset containing 'Subject_ID' and 'Flexibility_Score'
        
    Returns:
        Tuple of (filtered DataFrame, list of exclusion records)
    """
    if 'Flexibility_Score' not in df.columns:
        logger.warning("Flexibility_Score column not found in dataframe. Skipping missing score filter.")
        return df, []
    
    # Identify rows with missing scores
    missing_mask = df['Flexibility_Score'].isna()
    missing_count = missing_mask.sum()
    
    if missing_count == 0:
        logger.info("No missing behavioral scores found.")
        return df, []
    
    # Get subjects to exclude
    excluded_subjects = df[missing_mask]['Subject_ID'].tolist()
    exclusion_records = []
    
    for subject_id in excluded_subjects:
        # Get Mean_FD if available for logging, otherwise default to 0.0
        mean_fd = 0.0
        if 'Mean_FD' in df.columns:
            row = df[df['Subject_ID'] == subject_id]
            if not row.empty:
                val = row.iloc[0]['Mean_FD']
                if pd.notna(val):
                    mean_fd = float(val)
        
        record = {
            'Subject_ID': subject_id,
            'Exclusion_Reason': 'Missing_Behavioral_Score',
            'Mean_FD': mean_fd
        }
        exclusion_records.append(record)
    
    # Log exclusions
    for record in exclusion_records:
        log_exclusion(
            subject_id=record['Subject_ID'],
            reason=record['Exclusion_Reason'],
            metadata={'Mean_FD': record['Mean_FD']}
        )
    
    logger.info(f"Filtered out {missing_count} subjects with missing behavioral scores.")
    
    # Filter dataframe
    filtered_df = df[~missing_mask].copy()
    
    return filtered_df, exclusion_records

def run_merge_pipeline() -> Tuple[pd.DataFrame, bool]:
    """Run the full merge pipeline including normalization and validation."""
    init_logging()
    
    try:
        # Load datasets
        logger.info("Loading neuroimaging features...")
        neuro_df = load_neuro_features()
        
        logger.info("Loading behavioral scores...")
        behavioral_df = load_behavioral_scores()
        
        # Merge datasets
        logger.info("Merging datasets...")
        merged_df = merge_datasets(neuro_df, behavioral_df)
        
        # Normalize columns (T014a requirement)
        logger.info("Normalizing column names...")
        merged_df = normalize_columns(merged_df)
        
        # Filter missing behavioral scores (T017 requirement)
        logger.info("Filtering missing behavioral scores...")
        merged_df, _ = filter_missing_behavioral_scores(merged_df)
        
        # Validate schema
        logger.info("Validating merged schema...")
        is_valid, missing_cols = validate_merged_schema(merged_df)
        
        if not is_valid:
            raise ValueError(f"Schema validation failed. Missing columns: {missing_cols}")
        
        # Save merged dataset
        processed_path = get_processed_path()
        output_path = os.path.join(processed_path, "merged_dataset.csv")
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged dataset to {output_path}")
        
        return merged_df, True
        
    except Exception as e:
        log_error("merge_pipeline", str(e))
        raise

def main():
    """Main entry point for merge script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge neuroimaging and behavioral data")
    parser.add_argument('--verify', action='store_true', help="Verify output schema after merge")
    parser.add_argument('--filter', action='store_true', help="Apply missing behavioral score filter and log exclusions")
    args = parser.parse_args()
    
    logger.info("Starting merge pipeline...")
    
    try:
        merged_df, success = run_merge_pipeline()
        
        if args.verify:
            logger.info("Verifying output schema...")
            is_valid, missing_cols = validate_merged_schema(merged_df)
            
            if is_valid:
                logger.info("Verification PASSED: All required columns present.")
                logger.info(f"Columns: {list(merged_df.columns)}")
            else:
                logger.error(f"Verification FAILED: Missing columns {missing_cols}")
                raise ValueError("Schema verification failed")
        
        if args.filter:
            logger.info("Filtering missing behavioral scores...")
            filtered_df, exclusions = filter_missing_behavioral_scores(merged_df)
            
            if exclusions:
                logger.info(f"Excluded {len(exclusions)} subjects due to missing behavioral scores.")
                logger.info(f"Exclusion records logged to {get_processed_path()}/exclusion_log.csv")
            else:
                logger.info("No subjects excluded for missing behavioral scores.")
        
        logger.info("Merge pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Merge pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()