import os
import sys
import json
import yaml
import mne
import pandas as pd
from pathlib import Path
import logging
from utils.logging import get_logger

# Ensure lempel-ziv-complexity is available if needed later, though not strictly for download
try:
    import lz
except ImportError:
    pass

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def fetch_sleep_edf(config, logger):
    """
    Fetch Sleep-EDF dataset from PhysioNet using MNE.
    Validates presence of EEG channels and attempts to find any annotations
    that could serve as fatigue proxies (though Sleep-EDF is primarily sleep stages).
    
    Returns:
        tuple: (dataframe_or_None, error_message_or_None)
        If successful, returns a DataFrame with at least:
        ['subject_id', 'eeg_available', 'annotations', 'n_epochs']
    """
    logger.info("Attempting to fetch Sleep-EDF dataset from PhysioNet...")
    try:
        # MNE handles the download and extraction of PhysioNet datasets
        # Sleep-EDF dataset identifier
        dataset_name = "sleep-edf"
        
        # Try to load the dataset using MNE's built-in fetcher
        # This will download to the default mne_data directory or config-specified path
        data_path = mne.datasets.sleep_edf.data_path(download=True)
        
        if not data_path:
            return None, "MNE failed to download Sleep-EDF dataset"
        
        # List available files to verify structure
        # Sleep-EDF contains .edf files with EEG (Fpz-Cz, Pz-Oz) and other signals
        # We check for the presence of EEG channels
        files = Path(data_path).glob("*.edf")
        edf_files = list(files)
        
        if not edf_files:
            return None, "No .edf files found in downloaded Sleep-EDF"
        
        logger.info(f"Found {len(edf_files)} EDF files in Sleep-EDF dataset.")
        
        # Create a summary dataframe of available subjects
        subjects = []
        for f in edf_files[:100]: # Limit scan for performance
            # Extract subject ID from filename (e.g., 'SC401E0.edf')
            subj_id = f.stem.split('E')[0] if 'E' in f.stem else f.stem
            
            # Attempt to read header to confirm EEG channels
            try:
                raw = mne.io.read_raw_edf(str(f), preload=False, verbose=False)
                ch_names = raw.ch_names
                # Check for standard EEG channels in Sleep-EDF
                has_eeg = any(ch in ch_names for ch in ['Fpz-Cz', 'Pz-Oz'])
                
                # Check for annotations (sleep stages, but not fatigue ratings)
                has_annotations = raw.annotations is not None and len(raw.annotations) > 0
                
                # CRITICAL: Sleep-EDF does NOT contain pre/post fatigue ratings.
                # Per FR-001, we need 'paired pre/post fatigue ratings'.
                # We must report this absence accurately.
                subjects.append({
                    'subject_id': subj_id,
                    'file': f.name,
                    'eeg_available': has_eeg,
                    'has_annotations': has_annotations,
                    'has_fatigue_ratings': False, # Known limitation of Sleep-EDF
                    'note': 'Sleep-EDF lacks pre/post fatigue ratings'
                })
            except Exception as e:
                logger.warning(f"Could not read {f.name}: {e}")
                continue
        
        df = pd.DataFrame(subjects)
        
        # Validate: Do we have the required variables?
        # Required: 'pre_fatigue', 'post_fatigue'
        # Sleep-EDF has none.
        if 'has_fatigue_ratings' in df.columns and not df['has_fatigue_ratings'].any():
            return None, "Dataset lacks required pre/post fatigue ratings per FR-001"
        
        return df, None
        
    except Exception as e:
        logger.error(f"Failed to fetch Sleep-EDF: {str(e)}")
        return None, str(e)

def fetch_shhs(config, logger):
    """
    Fetch SHHS (Sleep Heart Health Study) dataset as fallback.
    SHHS is a large sleep study. We check if it contains the required fatigue metrics.
    Note: SHHS is typically accessed via specific repositories or large downloads,
    and standard MNE fetchers might not cover the specific cognitive fatigue subset.
    """
    logger.info("Attempting to fetch SHHS dataset as fallback...")
    try:
        # SHHS is not directly available via a simple MNE fetcher like Sleep-EDF.
        # It usually requires registration with the NHLBI BioLINCC or similar.
        # For this pipeline, we attempt to check availability via a known proxy or 
        # acknowledge the difficulty in programmatic access without credentials.
        
        # We will simulate a check that fails due to lack of direct programmatic access
        # or lack of specific fatigue labels in the public subset.
        # In a real production environment, this would require API keys or manual download.
        
        # Since we cannot programmatically fetch the specific fatigue-rated subset
        # without external credentials not provided in the config, we return failure.
        return None, "SHHS requires external credentials/registration not available in this environment"
        
    except Exception as e:
        logger.error(f"Failed to fetch SHHS: {str(e)}")
        return None, str(e)

def validate_dataset(data, logger):
    """
    Validate presence of resting-state EEG and paired pre/post fatigue ratings.
    """
    if data is None:
        return False, "No data provided"
    
    # Check for required columns if data is a DataFrame
    if isinstance(data, pd.DataFrame):
        # We need a column indicating fatigue ratings exist
        # In our fetch logic, we set 'has_fatigue_ratings'
        if 'has_fatigue_ratings' in data.columns:
            if not data['has_fatigue_ratings'].any():
                return False, "No records with fatigue ratings found"
        else:
            # Fallback check for explicit columns
            required_cols = ['pre_fatigue', 'post_fatigue']
            if not all(col in data.columns for col in required_cols):
                return False, f"Missing required columns: {required_cols}"
            
        return True, "Validation passed"
    
    return False, "Data is not a DataFrame"

def write_validation_report(report_data, output_path, logger):
    """
    Write validation report to JSON.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Validation report written to {output_path}")

def main():
    config = load_config()
    logger = get_logger("download", config)
    
    logger.info("Starting data retrieval and validation pipeline.")
    
    raw_path = Path(config['paths']['raw_data'])
    raw_path.mkdir(parents=True, exist_ok=True)
    
    # Primary attempt: Sleep-EDF
    data, error = fetch_sleep_edf(config, logger)
    source_name = "Sleep-EDF"
    
    if data is None:
        logger.warning(f"Primary source ({source_name}) failed: {error}")
        # Fallback: SHHS
        data, error = fetch_shhs(config, logger)
        source_name = "SHHS"
    
    if data is None:
        report = {
            "status": "failed",
            "reason": error,
            "dataset": source_name,
            "variables_found": [],
            "n_count": 0,
            "message": "No source with both EEG and pre/post fatigue ratings and N>=30 found."
        }
        write_validation_report(report, "data/processed/validation_report.json", logger)
        logger.error("Validation failed for all sources.")
        logger.error("Halting with exit code 1.")
        sys.exit(1)
    
    # If we got here, we have data
    # Validate N count
    n_count = len(data)
    if n_count < 30:
        report = {
            "status": "failed",
            "reason": f"N < 30 (found {n_count})",
            "dataset": source_name,
            "variables_found": list(data.columns),
            "n_count": n_count
        }
        write_validation_report(report, "data/processed/validation_report.json", logger)
        logger.error(f"Validation failed: N < 30. Found {n_count} records.")
        sys.exit(1)
    
    # Save data
    # We save the metadata/summary dataframe to raw_data.csv for downstream use
    # The actual EEG files are in the MNE cache or raw_path if we downloaded them
    # For this pipeline, we assume the 'data' dataframe contains the mapping
    # to the raw files.
    output_file = raw_path / "raw_data.csv"
    data.to_csv(output_file, index=False)
    logger.info(f"Data metadata saved to {output_file}")
    logger.info(f"Data retrieval successful. N={n_count}")
    logger.info("Pipeline proceeding to preprocessing.")

if __name__ == "__main__":
    main()
