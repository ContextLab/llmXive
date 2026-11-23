import os
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.config import Config
from code.data.ingest import main as ingest_main
from code.data.preprocessing import main as preprocess_main
from code.state.checksums import verify_and_record_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def load_preprocessed_trials() -> List[Dict[str, Any]]:
    """
    Load the preprocessed trial data from the ingestion step.
    This expects the raw trial data to have been ingested and cleaned.
    """
    # The ingestion step should have produced a raw trial CSV in data/raw or data/processed
    # We look for the most recent trial data file or a specific one defined in config
    raw_dir = Config.DATA_RAW
    processed_dir = Config.DATA_PROCESSED

    # Check for a merged trial file or the raw ingestion output
    # Based on T013/T014, we expect trial data to be available.
    # We will look for 'trials_raw.csv' or similar in processed if it exists,
    # otherwise we assume the ingestion pipeline puts it in a specific location.
    # For robustness, we check common locations.
    potential_files = [
        processed_dir / 'trials_cleaned.csv',
        processed_dir / 'linked_trials_raw.csv', # Intermediate from T014
        raw_dir / 'trials.csv'
    ]

    trial_data = []
    source_file = None

    for p in potential_files:
        if p.exists():
            source_file = p
            break

    if not source_file:
        # If no file exists, we might need to run the ingestion first,
        # but this function assumes prerequisites (T013, T014) are done.
        # We raise an error if the data is missing.
        raise FileNotFoundError(
            f"Preprocessed trial data not found. Expected one of: {potential_files}. "
            "Ensure T013 (Ingest) and T014 (Metadata) have completed successfully."
        )

    logger.info(f"Loading trial data from: {source_file}")
    with open(source_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trial_data.append(row)

    return trial_data

def load_stimulus_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Load stimulus metadata (valence, ambiguity, image paths) from T021/T022.
    Expected file: data/processed/stimulus_metadata.csv
    """
    metadata_file = Config.DATA_PROCESSED / 'stimulus_metadata.csv'
    
    if not metadata_file.exists():
        raise FileNotFoundError(
            f"Stimulus metadata not found at {metadata_file}. "
            "Ensure T021 (VAD) and T022 (Ambiguity) have completed successfully."
        )

    metadata = {}
    with open(metadata_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assume 'stimulus_id' is the key
            if 'stimulus_id' in row:
                metadata[row['stimulus_id']] = row
            else:
                # Fallback if column name differs
                first_key = next(iter(row))
                metadata[row[first_key]] = row

    return metadata

def ensure_linkage(trials: List[Dict[str, Any]], metadata: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure every trial has a valid linkage to stimulus metadata.
    Filter out trials where the stimulus_id is missing or not in metadata.
    """
    linked_trials = []
    missing_count = 0

    for trial in trials:
        stimulus_id = trial.get('stimulus_id')
        
        if not stimulus_id:
            missing_count += 1
            continue

        if stimulus_id not in metadata:
            missing_count += 1
            continue

        # Merge metadata into trial
        trial_with_meta = {**trial, **metadata[stimulus_id]}
        linked_trials.append(trial_with_meta)

    if missing_count > 0:
        logger.warning(f"Excluded {missing_count} trials due to missing linkage.")

    return linked_trials

def normalize_columns(linked_trials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Select and normalize columns to match the required schema:
    trial_id, response_time, stimulus_id, prime_condition, participant_id
    """
    required_columns = [
        'trial_id', 
        'response_time', 
        'stimulus_id', 
        'prime_condition', 
        'participant_id'
    ]
    
    normalized = []
    for trial in linked_trials:
        new_trial = {}
        for col in required_columns:
            # Handle potential key variations (e.g., 'response_time' vs 'rt')
            if col in trial:
                new_trial[col] = trial[col]
            else:
                # Try common aliases
                if col == 'response_time' and 'rt' in trial:
                    new_trial[col] = trial['rt']
                elif col == 'trial_id' and 'id' in trial:
                    new_trial[col] = trial['id']
                else:
                    new_trial[col] = '' # Default to empty string if missing
        
        # Ensure numeric types for response_time if possible
        try:
            if new_trial['response_time']:
                new_trial['response_time'] = float(new_trial['response_time'])
        except ValueError:
            new_trial['response_time'] = 0.0 # Handle invalid numeric data

        normalized.append(new_trial)
    
    return normalized

def write_linked_trials(linked_trials: List[Dict[str, Any]], output_path: Path):
    """
    Write the final linked trials CSV to disk.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['trial_id', 'response_time', 'stimulus_id', 'prime_condition', 'participant_id']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(linked_trials)
    
    logger.info(f"Successfully wrote {len(linked_trials)} rows to {output_path}")

def verify_metadata_percentage(linked_trials: List[Dict[str, Any]], total_trials: int):
    """
    Verify that the linked metadata percentage meets the threshold (T016 gate).
    """
    if total_trials == 0:
        logger.warning("Total trials is 0, skipping percentage verification.")
        return

    percentage = (len(linked_trials) / total_trials) * 100
    logger.info(f"SC-001 Check: Linked Metadata = {percentage:.2f}% (Target: 'The vast majority' per SC-001)")
    
    # The gate (T016) should have already ensured this is > 90%, but we log it here for T018a consistency.
    if percentage < 90.0:
        logger.warning(f"Linked metadata percentage ({percentage:.2f}%) is below 90% threshold.")

def main():
    """
    Main entry point for T017: Generate linked_trials.csv.
    """
    logger.info("Starting T017: Generate linked_trials.csv")

    try:
        # 1. Load preprocessed trials (from T013/T014)
        trials = load_preprocessed_trials()
        total_trials = len(trials)
        logger.info(f"Loaded {total_trials} raw trials.")

        # 2. Load stimulus metadata (from T021/T022)
        metadata = load_stimulus_metadata()
        logger.info(f"Loaded metadata for {len(metadata)} stimuli.")

        # 3. Ensure linkage (filter missing)
        linked_trials = ensure_linkage(trials, metadata)
        logger.info(f"Successfully linked {len(linked_trials)} trials.")

        # 4. Verify percentage (log only, T016 should have blocked if < 90%)
        verify_metadata_percentage(linked_trials, total_trials)

        # 5. Normalize columns
        normalized_trials = normalize_columns(linked_trials)

        # 6. Write output
        output_path = Config.DATA_PROCESSED / 'linked_trials.csv'
        write_linked_trials(normalized_trials, output_path)

        logger.info("T017 completed successfully.")

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T017: {e}")
        raise

if __name__ == "__main__":
    main()
