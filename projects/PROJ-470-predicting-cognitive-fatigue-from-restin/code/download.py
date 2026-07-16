import os
import sys
import json
import yaml
import mne
import pandas as pd
from pathlib import Path
from datetime import datetime
from utils.logging import get_logger

# Attempt to import datasets for HuggingFace Hub access
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    # We will try to import it later if needed, but fail loud if not available
    # and we need to fetch real data.

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def fetch_sleep_edf(logger):
    """
    Fetch the Sleep-EDF dataset from HuggingFace Hub (PhysioNet ID: sleep-edf).
    Returns a tuple (dataset, metadata_df) or (None, None) if failed.
    Validates presence of EEG channels and fatigue ratings if available.
    """
    if not HF_AVAILABLE:
        logger.error("HuggingFace 'datasets' library not installed. Cannot fetch Sleep-EDF.")
        return None, None

    dataset_id = "sleep-edf"
    logger.info(f"Attempting to fetch Sleep-EDF dataset (ID: {dataset_id})...")
    try:
        # Load the dataset. We use streaming=False to load metadata for validation.
        # Note: Sleep-EDF on HF might be split into 'train'/'test' or similar.
        # We attempt to load the full dataset or the first split if necessary.
        ds = load_dataset(dataset_id, split="train", trust_remote_code=True)
        
        # Check if dataset has required columns for fatigue or at least EEG
        # Sleep-EDF typically has 'sleep', 'stages', 'eeg', etc.
        # We need to verify if it has a 'fatigue' or 'rating' column.
        # Based on standard Sleep-EDF, it often lacks explicit 'fatigue' ratings.
        # We check for EEG channels first.
        
        has_eeg = False
        has_fatigue = False
        
        # Check columns
        cols = ds.column_names
        logger.info(f"Sleep-EDF columns: {cols}")
        
        # Look for EEG related columns (e.g., 'eeg', 'eeg_data', 'channel')
        eeg_cols = [c for c in cols if 'eeg' in c.lower() or 'channel' in c.lower()]
        if eeg_cols:
            has_eeg = True
            logger.info(f"Found EEG-related columns: {eeg_cols}")
        
        # Look for fatigue/rating columns
        fatigue_cols = [c for c in cols if 'fatigue' in c.lower() or 'rating' in c.lower() or 'score' in c.lower()]
        if fatigue_cols:
            has_fatigue = True
            logger.info(f"Found fatigue/rating-related columns: {fatigue_cols}")
        
        # Count valid participants (N)
        # We assume each row or group of rows represents a participant.
        # For simplicity, we count unique 'subject' or 'id' if available, else total rows.
        if 'subject' in cols:
            n = ds['subject'].unique().size if hasattr(ds['subject'].unique(), 'size') else len(ds['subject'].unique())
        elif 'id' in cols:
            n = ds['id'].unique().size if hasattr(ds['id'].unique(), 'size') else len(ds['id'].unique())
        else:
            n = len(ds)
        
        logger.info(f"Sleep-EDF participant count (N): {n}")
        
        # Validate: Must have EEG and Fatigue ratings, and N >= 30
        if not has_eeg:
            logger.warning("Sleep-EDF lacks EEG channels.")
            return None, None
        
        if not has_fatigue:
            logger.warning("Sleep-EDF lacks explicit fatigue ratings. This dataset may not meet FR-001.")
            # We return it anyway but mark as missing fatigue, so the caller can decide to fallback.
            # However, the task says: "Validate presence of both resting-state EEG and paired pre/post fatigue ratings"
            # If missing, we should NOT use it as a valid source for this specific study.
            return None, None

        if n < 30:
            logger.warning(f"Sleep-EDF N={n} is less than required 30.")
            return None, None

        # Create a simple metadata dataframe
        # We extract subject IDs and any available fatigue scores
        metadata = pd.DataFrame({
            'subject': ds['subject'] if 'subject' in cols else ds['id'] if 'id' in cols else range(len(ds)),
            'fatigue_pre': ds['fatigue_pre'] if 'fatigue_pre' in cols else None, # Placeholder
            'fatigue_post': ds['fatigue_post'] if 'fatigue_post' in cols else None, # Placeholder
        })
        
        # If fatigue columns exist, populate them
        if 'fatigue_pre' in cols:
            metadata['fatigue_pre'] = ds['fatigue_pre']
        if 'fatigue_post' in cols:
            metadata['fatigue_post'] = ds['fatigue_post']
        
        logger.info("Sleep-EDF validation passed.")
        return ds, metadata

    except Exception as e:
        logger.error(f"Failed to fetch Sleep-EDF: {e}")
        return None, None

def fetch_shhs(logger):
    """
    Fetch the SHHS dataset as a fallback.
    SHHS (Sleep Heart Health Study) is large and complex.
    We attempt to load a subset or a specific split if available on HF.
    Returns (dataset, metadata_df) or (None, None).
    """
    if not HF_AVAILABLE:
        logger.error("HuggingFace 'datasets' library not installed. Cannot fetch SHHS.")
        return None, None

    dataset_id = "shhs" # Hypothetical ID, SHHS might be under a different name or require specific access
    # Actual SHHS on HF might be 'physionet/sleep-edf' or similar. 
    # Let's try a common identifier or fallback to a known subset if available.
    # Since SHHS is often restricted, we might not have direct access without credentials.
    # We try a public subset if it exists.
    
    logger.info("Attempting to fetch SHHS dataset as fallback...")
    
    # Try to load a public subset if available
    # Note: SHHS is often not fully public on HF without registration.
    # We will attempt a generic load and catch errors.
    try:
        # Attempting a generic load, might fail if not public
        ds = load_dataset(dataset_id, split="train", trust_remote_code=True)
        
        has_eeg = False
        has_fatigue = False
        cols = ds.column_names
        
        # Check for EEG
        eeg_cols = [c for c in cols if 'eeg' in c.lower() or 'channel' in c.lower()]
        if eeg_cols:
            has_eeg = True
        
        # Check for fatigue
        fatigue_cols = [c for c in cols if 'fatigue' in c.lower() or 'rating' in c.lower() or 'score' in c.lower()]
        if fatigue_cols:
            has_fatigue = True
        
        # Count N
        if 'subject' in cols:
            n = ds['subject'].unique().size if hasattr(ds['subject'].unique(), 'size') else len(ds['subject'].unique())
        elif 'id' in cols:
            n = ds['id'].unique().size if hasattr(ds['id'].unique(), 'size') else len(ds['id'].unique())
        else:
            n = len(ds)
        
        if not has_eeg:
            logger.warning("SHHS lacks EEG channels.")
            return None, None
        
        if not has_fatigue:
            logger.warning("SHHS lacks explicit fatigue ratings.")
            return None, None
        
        if n < 30:
            logger.warning(f"SHHS N={n} is less than required 30.")
            return None, None
        
        metadata = pd.DataFrame({
            'subject': ds['subject'] if 'subject' in cols else ds['id'] if 'id' in cols else range(len(ds)),
            'fatigue_pre': ds['fatigue_pre'] if 'fatigue_pre' in cols else None,
            'fatigue_post': ds['fatigue_post'] if 'fatigue_post' in cols else None,
        })
        
        if 'fatigue_pre' in cols:
            metadata['fatigue_pre'] = ds['fatigue_pre']
        if 'fatigue_post' in cols:
            metadata['fatigue_post'] = ds['fatigue_post']
        
        logger.info("SHHS validation passed.")
        return ds, metadata

    except Exception as e:
        logger.error(f"Failed to fetch SHHS: {e}")
        return None, None

def validate_dataset(dataset, metadata, source_name, logger):
    """
    Validate the dataset and metadata.
    Returns True if valid, False otherwise.
    """
    if dataset is None:
        logger.error(f"{source_name} dataset is None.")
        return False
    
    if metadata is None or metadata.empty:
        logger.error(f"{source_name} metadata is empty.")
        return False
    
    # Check for required columns in metadata
    required_cols = ['subject', 'fatigue_pre', 'fatigue_post']
    missing_cols = [c for c in required_cols if c not in metadata.columns]
    if missing_cols:
        logger.error(f"{source_name} metadata missing required columns: {missing_cols}")
        return False
    
    # Check for non-null fatigue values
    if metadata['fatigue_pre'].isna().all() and metadata['fatigue_post'].isna().all():
        logger.error(f"{source_name} has no valid fatigue ratings.")
        return False
    
    logger.info(f"{source_name} dataset validated successfully.")
    return True

def write_validation_report(report_data, logger):
    """
    Write the validation report to data/processed/validation_report.json.
    """
    output_dir = Path(__file__).parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "validation_report.json"
    
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    logger.info(f"Validation report written to {output_path}")

def main():
    """
    Main entry point for the download and validation pipeline.
    """
    logger = get_logger(__name__)
    logger.info("Starting data retrieval and validation pipeline.")
    
    config = load_config()
    
    # Try primary source: Sleep-EDF
    sleep_edf_ds, sleep_edf_meta = fetch_sleep_edf(logger)
    sleep_edf_valid = False
    if sleep_edf_ds is not None and sleep_edf_meta is not None:
        sleep_edf_valid = validate_dataset(sleep_edf_ds, sleep_edf_meta, "Sleep-EDF", logger)
    
    if sleep_edf_valid:
        logger.info("Sleep-EDF is valid. Proceeding with preprocessing.")
        # Save dataset and metadata to disk for downstream tasks
        # We save the metadata to data/processed/metadata.csv
        output_dir = Path(__file__).parent.parent / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        sleep_edf_meta.to_csv(output_dir / "metadata.csv", index=False)
        
        # Note: The actual EEG data loading will be handled by preprocess.py
        # We assume the dataset object can be reloaded or the path is known.
        # For now, we just signal success.
        logger.info("Data retrieval and validation completed successfully.")
        return 0
    
    # Fallback to SHHS
    shhs_ds, shhs_meta = fetch_shhs(logger)
    shhs_valid = False
    if shhs_ds is not None and shhs_meta is not None:
        shhs_valid = validate_dataset(shhs_ds, shhs_meta, "SHHS", logger)
    
    if shhs_valid:
        logger.info("SHHS is valid. Proceeding with preprocessing.")
        output_dir = Path(__file__).parent.parent / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        shhs_meta.to_csv(output_dir / "metadata.csv", index=False)
        
        logger.info("Data retrieval and validation completed successfully.")
        return 0
    
    # If both fail, write validation report and exit with code 1
    logger.error("Validation failed for all sources.")
    report = {
        "status": "failed",
        "timestamp": datetime.now().isoformat(),
        "sources_checked": {
            "sleep-edf": {
                "available": sleep_edf_ds is not None,
                "valid": sleep_edf_valid,
                "reason": "Missing EEG, fatigue ratings, or N < 30" if sleep_edf_ds else "Fetch failed"
            },
            "shhs": {
                "available": shhs_ds is not None,
                "valid": shhs_valid,
                "reason": "Missing EEG, fatigue ratings, or N < 30" if shhs_ds else "Fetch failed"
            }
        },
        "message": "No dataset with both resting-state EEG and paired fatigue ratings (N>=30) was found."
    }
    write_validation_report(report, logger)
    logger.error("Halting with exit code 1.")
    return 1

if __name__ == "__main__":
    sys.exit(main())