import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests
from src.utils.config import get_project_root, get_interim_data_dir
from src.utils.logging import setup_logger

logger = logging.getLogger(__name__)

def fetch_global_soundscapes_data() -> List[Dict]:
    """
    Fetch noise level data from the Global Soundscapes dataset.
    Since the dataset is large and not directly indexable by simple ID in a single
    HTTP call without the 'datasets' library, we attempt to fetch a sample or
    specific coordinate data if available via an API, or fall back to the local
    cached version if the project has downloaded it.
    
    For this implementation, we assume the 'noise_mapped.csv' contains the 
    coordinates and we need to validate against a reference. 
    
    NOTE: The task requires validation against the 'Global Soundscapes dataset'.
    If the dataset is not locally cached as a reference file, we cannot perform
    a direct row-by-row deviation check without downloading the entire global
    raster or using the 'datasets' library which is already a dependency.
    
    We will attempt to load the 'global_soundscapes_reference.csv' if it exists
    in data/raw, otherwise we try to fetch a sample from a known endpoint 
    (simulated here as a direct fetch of a small subset if coordinates are known).
    
    However, the most robust way given the constraints (and the fact that T015
    already fetched the data) is to assume T015 stored the 'primary' values.
    The validation task (T015c) must distinguish between 'primary' (from Global Soundscapes)
    and 'interpolated' (from T015d).
    
    The 'noise_mapped.csv' produced by T015/T015d should ideally have a column
    indicating the source. If not, we infer based on the presence of an 'interpolated'
    flag or by checking against a local reference file if available.
    
    For this task, we assume the input 'noise_mapped.csv' has a column 'source' 
    or we infer 'interpolated' if the value matches the interpolated records exactly.
    
    To strictly follow the "Validate against Global Soundscapes" requirement:
    We will try to load a reference file `data/raw/global_soundscapes_reference.csv`
    if it exists. If not, we assume the values in 'noise_mapped.csv' marked as
    'primary' are correct by definition of the T015 process, and we only check
    for consistency or if a reference is provided.
    
    Given the constraint to "fail loudly" if no real source, and the lack of
    a direct public API for random coordinate lookup without the full dataset,
    we will implement the logic to:
    1. Load 'noise_mapped.csv'.
    2. Identify records marked as 'INTERPOLATED' (or from T015d).
    3. For others, if a reference file exists, compare. If not, we log 'PASS' 
       assuming the T015 fetch was valid, but we must strictly check deviation
       if a reference is available.
    
    To make this testable and real, we will assume the project has downloaded
    the Global Soundscapes data to `data/raw/global_soundscapes_data.csv` (or similar)
    as part of T015's execution. If T015 did not save a reference, we cannot
    validate deviation. 
    
    RE-INTERPRETATION: The task says "validate the combined noise_mapped.csv against 
    the Global Soundscapes dataset". This implies we have access to the "true" values.
    Since T015 fetched them, the "true" values are the ones T015 fetched. 
    The only way to have a deviation check is if there is a SECOND source or if 
    T015 fetched a value and we are comparing against a cached version? 
    
    Actually, the task likely implies: 
    "For records with primary source values, check deviation <= 2 dB(A) against 
    the ORIGINAL Global Soundscapes value." 
    If T015 fetched the value, that IS the Global Soundscapes value. 
    Perhaps the task implies comparing against a known ground truth or a different 
    version? 
    
    Let's assume the standard research pipeline: 
    1. T015 fetches from Global Soundscapes -> `noise_mapped.csv` (primary).
    2. T015d fetches/interpolates -> `interpolated_records.csv`.
    3. T015 merges them.
    
    Validation (T015c): 
    - If a record is from Primary (Global Soundscapes), we assume it's correct 
      UNLESS we have a way to re-verify. 
    - Maybe the "deviation" check is against a cached local copy if the fetch 
      was from a mirror? 
    
    Given the ambiguity and the need to "fail loudly" without a real source, 
    and the fact that we cannot re-fetch the entire global dataset to compare 
    row-by-row without the `datasets` library (which is installed), we will 
    implement the validation by:
    1. Checking if a reference file `data/raw/global_soundscapes_reference.csv` exists.
    2. If it does, compare `noise_mapped.csv` (primary records) against it.
    3. If it does NOT, we cannot perform the deviation check. We will log a warning
       that validation requires a reference file, but we will mark primary records 
       as 'PASS' assuming the T015 fetch was successful (since we can't verify 
       without a second source).
    
    However, the prompt says "validate ... against the Global Soundscapes dataset".
    If we have the `datasets` library, we can load the dataset again and compare.
    But loading 7GB+ for validation is heavy. 
    
    Let's assume the "Global Soundscapes dataset" is available via the `datasets` 
    library as 'noise-map/global-soundscapes' (as hinted in T015). 
    We will attempt to load a sample of the dataset to validate against.
    If the dataset is not available or too large, we will fail loudly.
    
    Revised Plan for T015c:
    1. Load `data/interim/noise_mapped.csv`.
    2. Separate into 'primary' and 'interpolated' based on a 'source' column 
       (added by T015/T015d) or by checking against `data/interim/interpolated_records.csv`.
    3. For 'primary' records:
       - If `data/raw/global_soundscapes_reference.csv` exists, load it and compare.
       - Else, try to load the dataset via `datasets.load_dataset('noise-map/global-soundscapes')`
         and find the matching rows (requires coordinates). If successful, compare.
       - If neither, log 'WARN: No reference available for deviation check' and mark 'PASS' 
         (assuming fetch was correct) OR fail loudly? 
         The task says "check deviation <= 2 dB(A)". If we can't check, we can't guarantee.
         But failing the whole pipeline because we can't re-fetch 7GB seems wrong.
         Let's assume the T015 fetch is the "truth" and we only validate if a 
         secondary reference is provided. 
         However, the task says "validate ... against the Global Soundscapes dataset".
         This implies we MUST have access to it.
         
         We will try to use the `datasets` library to fetch the specific rows 
         for the coordinates in `noise_mapped.csv`. If that fails (network, auth, size),
         we raise an error.
    4. For 'interpolated' records: Mark as 'INTERPOLATED'.
    
    Given the complexity and potential for failure, we will implement a robust
    check that tries to load the dataset and compare. If it fails, we log the error
    and fail loudly as per constraints.
    """
    # Implementation of fetching/validating against Global Soundscapes
    # Since we cannot guarantee the dataset is available in a way that allows 
    # random access without loading the whole thing (or having an index),
    # and the task requires a deviation check, we will assume the existence
    # of a reference file or a working API.
    
    # For this implementation, we will assume the project has a reference file
    # or we will use the `datasets` library to fetch the specific rows.
    # If the dataset is 'noise-map/global-soundscapes', we try to load it.
    
    try:
        from datasets import load_dataset
        # This might be heavy. We'll try to load in streaming mode if possible
        # or just load the subset if the dataset supports it.
        # However, streaming might not support random access by coordinates easily.
        # Let's assume we have a reference file for now to keep it robust.
        # If not, we will try to fetch.
        
        # Fallback to a reference file if the dataset fetch is too heavy
        ref_path = get_project_root() / "data" / "raw" / "global_soundscapes_reference.csv"
        if ref_path.exists():
            logger.info(f"Using reference file: {ref_path}")
            return load_csv(ref_path)
        else:
            # Try to fetch from the dataset library
            logger.info("Reference file not found. Attempting to load Global Soundscapes dataset...")
            # This is a placeholder for the actual dataset loading logic.
            # In a real scenario, we would load the dataset and filter by coordinates.
            # For now, we raise an error to fail loudly if no reference is found.
            raise FileNotFoundError("No reference file found and dataset fetch is not implemented for validation in this context.")
    except Exception as e:
        logger.error(f"Failed to fetch Global Soundscapes data for validation: {e}")
        raise

def load_csv(path: Path) -> List[Dict]:
    """Load a CSV file into a list of dictionaries."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    records = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def save_csv(path: Path, records: List[Dict], fieldnames: List[str]):
    """Save a list of dictionaries to a CSV file."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def validate_osm_proxies(noise_mapped_path: Path, reference_data: List[Dict]) -> List[Dict]:
    """
    Validate noise_mapped.csv against reference data.
    
    Logic:
    1. Identify 'interpolated' records (from T015d). Mark as 'INTERPOLATED'.
    2. For 'primary' records:
       - Find matching record in reference_data (by recording_id or coordinates).
       - Calculate absolute deviation in noise_level_db.
       - If deviation <= 2.0: 'PASS'
       - If deviation > 2.0: 'WARN'
    3. If no match in reference: 'WARN' (or 'FAIL' depending on strictness).
    
    Returns a list of validation records.
    """
    validation_logs = []
    
    # Load noise_mapped.csv
    noise_mapped_records = load_csv(noise_mapped_path)
    
    # Create a lookup for reference data
    # Assuming reference data has 'recording_id' or 'latitude', 'longitude'
    ref_lookup = {}
    for ref in reference_data:
        key = ref.get('recording_id')
        if key:
            ref_lookup[key] = ref
        # If no recording_id, we might need to match by coordinates, but let's assume ID first.
    
    for record in noise_mapped_records:
        rec_id = record.get('recording_id')
        source = record.get('source', 'unknown')
        noise_val = float(record.get('noise_level_db', 0))
        
        log_entry = {
            'recording_id': rec_id,
            'source': source,
            'status': '',
            'deviation': None,
            'noise_level_db': noise_val
        }
        
        if source == 'interpolated':
            log_entry['status'] = 'INTERPOLATED'
            log_entry['deviation'] = None
        else:
            # Primary source
            if rec_id in ref_lookup:
                ref_noise = float(ref_lookup[rec_id].get('noise_level_db', 0))
                deviation = abs(noise_val - ref_noise)
                log_entry['deviation'] = round(deviation, 2)
                if deviation <= 2.0:
                    log_entry['status'] = 'PASS'
                else:
                    log_entry['status'] = 'WARN'
            else:
                # No reference found for this ID
                log_entry['status'] = 'WARN'
                log_entry['deviation'] = None # Could not calculate
        
        validation_logs.append(log_entry)
    
    return validation_logs

def main():
    """
    Main entry point for T015c.
    Validates noise_mapped.csv against Global Soundscapes data.
    Outputs: data/interim/validation_log.csv
    """
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    noise_mapped_path = interim_dir / "noise_mapped.csv"
    validation_log_path = interim_dir / "validation_log.csv"
    
    if not noise_mapped_path.exists():
        logger.error(f"Input file not found: {noise_mapped_path}")
        return
    
    logger.info("Starting T015c Validation...")
    
    # Fetch reference data (or load from file)
    try:
        # We try to load a reference file first. If not, we attempt to fetch.
        # Since the task requires validation against the dataset, and we don't have
        # a direct API for random access without loading the whole dataset,
        # we rely on a reference file if available.
        ref_path = project_root / "data" / "raw" / "global_soundscapes_reference.csv"
        if ref_path.exists():
            reference_data = load_csv(ref_path)
        else:
            # Try to fetch from the dataset library
            # This is a simplified version; in reality, we'd need to handle the dataset loading carefully.
            # For now, we raise an error to fail loudly if no reference is found.
            logger.warning("Reference file not found. Attempting to load dataset...")
            try:
                from datasets import load_dataset
                # This is a placeholder. We assume the dataset is available and we can filter.
                # But without an index, we can't easily fetch specific rows.
                # We will assume the reference file is the intended way for validation.
                raise FileNotFoundError("Reference file not found and dataset fetch is not fully implemented for random access.")
            except Exception as e:
                logger.error(f"Failed to load reference data: {e}")
                raise
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        # Fail loudly as per constraints
        raise RuntimeError(f"Validation failed due to missing reference data: {e}")
    
    # Perform validation
    validation_logs = validate_osm_proxies(noise_mapped_path, reference_data)
    
    # Save validation log
    fieldnames = ['recording_id', 'source', 'status', 'deviation', 'noise_level_db']
    save_csv(validation_log_path, validation_logs, fieldnames)
    
    logger.info(f"Validation complete. Log saved to: {validation_log_path}")
    
    # Summary
    status_counts = {}
    for log in validation_logs:
        status = log['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    logger.info(f"Validation Summary: {status_counts}")

if __name__ == "__main__":
    setup_logger()
    main()
