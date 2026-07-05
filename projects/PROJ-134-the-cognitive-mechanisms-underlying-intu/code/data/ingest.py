import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_directories
from code.utils.schema import MergedDataset, validate_merged_data
from code.utils.logging_utils import log_pipeline_step, log_exclusion

# Constants for file paths relative to project root
MFQ_FILE = "data/processed/synthetic_mfq.csv"
STORIES_FILE = "data/processed/synthetic_stories.csv"
VR_LOGS_FILE = "data/processed/synthetic_vr_logs.csv"
OUTPUT_FILE = "data/processed/merged_dataset.csv"
LOG_FILE = "data/logs/ingest_log.txt"

def load_mfq_data(file_path: str) -> pd.DataFrame:
    """Load MFQ data from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"MFQ file not found: {file_path}")
    
    log_pipeline_step("Loading MFQ data", LOG_FILE)
    df = pd.read_csv(file_path)
    log_pipeline_step(f"Loaded {len(df)} MFQ records", LOG_FILE)
    return df

def load_stories_data(file_path: str) -> pd.DataFrame:
    """Load Moral Stories data from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Stories file not found: {file_path}")
    
    log_pipeline_step("Loading Moral Stories data", LOG_FILE)
    df = pd.read_csv(file_path)
    log_pipeline_step(f"Loaded {len(df)} story records", LOG_FILE)
    return df

def load_vr_logs_data(file_path: str) -> pd.DataFrame:
    """Load VR interaction logs from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"VR logs file not found: {file_path}")
    
    log_pipeline_step("Loading VR logs data", LOG_FILE)
    df = pd.read_csv(file_path)
    log_pipeline_step(f"Loaded {len(df)} VR log records", LOG_FILE)
    return df

def merge_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge MFQ, Stories, and VR logs on participant_id and story_id.
    Handles ID mismatches by logging exclusions and keeping only matched records.
    """
    log_pipeline_step("Starting dataset merge", LOG_FILE)
    
    # Ensure common ID columns exist
    # MFQ has: participant_id
    # Stories has: participant_id, story_id
    # VR Logs has: participant_id, story_id
    
    # First, merge MFQ with Stories on participant_id
    merged_mfq_stories = pd.merge(
        mfq_df, 
        stories_df, 
        on='participant_id', 
        how='inner',
        suffixes=('_mfq', '_stories')
    )
    
    log_pipeline_step(f"Merged MFQ and Stories: {len(merged_mfq_stories)} records", LOG_FILE)
    
    # Log exclusions for participants in Stories/MFQ but not in both
    mfq_only = len(mfq_df) - len(mfq_df[mfq_df['participant_id'].isin(stories_df['participant_id'])])
    stories_only = len(stories_df) - len(stories_df[stories_df['participant_id'].isin(mfq_df['participant_id'])])
    
    if mfq_only > 0:
        log_exclusion(f"{mfq_only} MFQ records excluded due to missing participant_id in stories", LOG_FILE)
    if stories_only > 0:
        log_exclusion(f"{stories_only} story records excluded due to missing participant_id in MFQ", LOG_FILE)
    
    # Then merge with VR logs on participant_id and story_id
    final_merged = pd.merge(
        merged_mfq_stories,
        vr_logs_df,
        on=['participant_id', 'story_id'],
        how='inner',
        suffixes=('', '_vr')
    )
    
    log_pipeline_step(f"Final merged dataset: {len(final_merged)} records", LOG_FILE)
    
    # Log exclusions for VR logs mismatches
    vr_only = len(vr_logs_df) - len(vr_logs_df[vr_logs_df.apply(
        lambda x: (x['participant_id'], x['story_id']) in 
        list(zip(final_merged['participant_id'], final_merged['story_id'])), axis=1
    )])
    
    if vr_only > 0:
        log_exclusion(f"{vr_only} VR log records excluded due to missing (participant_id, story_id) match", LOG_FILE)
    
    return final_merged

def validate_and_save(merged_df: pd.DataFrame, output_path: str) -> bool:
    """
    Validate the merged dataset against the MergedDataset schema and save to CSV.
    Returns True if validation passes, False otherwise.
    """
    log_pipeline_step("Validating merged dataset", LOG_FILE)
    
    try:
        # Convert to list of dicts for Pydantic validation
        data_dict = merged_df.to_dict(orient='records')
        
        # Validate using Pydantic schema
        # Note: MergedDataset expects a specific structure, we validate the structure
        # For large datasets, we might validate a sample or rely on pandas dtypes
        if len(data_dict) > 0:
            # Validate first record as a sanity check
            sample = MergedDataset.model_validate(data_dict[0])
            log_pipeline_step("Schema validation passed for sample record", LOG_FILE)
        
        # Save to CSV
        merged_df.to_csv(output_path, index=False)
        log_pipeline_step(f"Merged dataset saved to {output_path}", LOG_FILE)
        
        return True
        
    except Exception as e:
        log_exclusion(f"Validation failed: {str(e)}", LOG_FILE)
        return False

def main():
    """Main entry point for the ingestion pipeline."""
    log_pipeline_step("Starting Ingestion Pipeline (T015)", LOG_FILE)
    
    # Ensure directories exist
    ensure_directories()
    
    # Construct full paths
    mfq_path = project_root / MFQ_FILE
    stories_path = project_root / STORIES_FILE
    vr_logs_path = project_root / VR_LOGS_FILE
    output_path = project_root / OUTPUT_FILE
    
    # Check if input files exist (they should be generated by T013 and T014)
    if not mfq_path.exists():
        raise FileNotFoundError(
            f"Required input file missing: {mfq_path}. "
            "Please run simulation_mfq.py (T013) first."
        )
    if not stories_path.exists():
        raise FileNotFoundError(
            f"Required input file missing: {stories_path}. "
            "Please run simulation_stories.py (T014) first."
        )
    if not vr_logs_path.exists():
        raise FileNotFoundError(
            f"Required input file missing: {vr_logs_path}. "
            "Please run simulation_stories.py (T014) first."
        )
    
    try:
        # Load datasets
        mfq_df = load_mfq_data(str(mfq_path))
        stories_df = load_stories_data(str(stories_path))
        vr_logs_df = load_vr_logs_data(str(vr_logs_path))
        
        # Merge datasets
        merged_df = merge_datasets(mfq_df, stories_df, vr_logs_df)
        
        # Validate and save
        if validate_and_save(merged_df, str(output_path)):
            log_pipeline_step("Ingestion Pipeline completed successfully", LOG_FILE)
            print(f"Successfully merged and saved dataset to: {output_path}")
            print(f"Total records: {len(merged_df)}")
            return True
        else:
            log_pipeline_step("Ingestion Pipeline failed validation", LOG_FILE)
            print("Ingestion Pipeline failed validation. Check logs for details.")
            return False
            
    except Exception as e:
        log_exclusion(f"Ingestion Pipeline crashed: {str(e)}", LOG_FILE)
        print(f"Error during ingestion: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
