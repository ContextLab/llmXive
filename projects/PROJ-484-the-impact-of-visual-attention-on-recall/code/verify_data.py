import os
import sys
import json
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging

# Constants for defaults
DEFAULT_FPS = 60
DEFAULT_DURATION_MS = 100
LOG_FILE_PATH = "artifacts/logs/temporal_load_check.log"

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file {file_path}: {e}")
        return None

def load_yaml_file(file_path):
    """Load a YAML file and return its contents."""
    try:
        import yaml
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        logging.error(f"Error decoding YAML file {file_path}: {e}")
        return None

def find_bids_sidecars(data_root, task_name=None):
    """
    Find BIDS sidecar files (JSON) in the data root.
    Looks for events.tsv sidecars and task-*.json files.
    """
    sidecars = {
        'events': [],
        'task': []
    }
    data_root = Path(data_root)
    if not data_root.exists():
        return sidecars

    # Search for events.tsv.json
    for event_file in data_root.rglob("events.tsv"):
        json_sidecar = event_file.with_suffix('.tsv.json')
        if json_sidecar.exists():
            sidecars['events'].append(json_sidecar)
        
        # Also check for task-specific events if task_name is provided
        if task_name:
            task_event = data_root / task_name / "events.tsv"
            if task_event.exists():
                task_json = task_event.with_suffix('.tsv.json')
                if task_json.exists() and task_json not in sidecars['events']:
                    sidecars['events'].append(task_json)

    # Search for task-*.json (stimulus metadata)
    for json_file in data_root.rglob("task-*.json"):
        sidecars['task'].append(json_file)
        
    return sidecars

def extract_columns_from_sidecar(sidecar_path, target_columns):
    """
    Extract specific columns from a BIDS sidecar JSON.
    Returns a dict of column_name -> found_status (True/False)
    """
    data = load_json_file(sidecar_path)
    if not data:
        return {col: False for col in target_columns}

    found = {col: False for col in target_columns}
    
    # Check top level
    for col in target_columns:
        if col in data:
            found[col] = True
            continue
        
        # Check nested in 'columns' or 'stimuli' or 'custom_columns'
        if 'columns' in data:
            for col_def in data['columns']:
                if isinstance(col_def, dict) and col_def.get('name') == col:
                    found[col] = True
                    break
                elif isinstance(col_def, str) and col_def == col:
                    found[col] = True
                    break
        
        if 'stimuli' in data:
            if col in data['stimuli']:
                found[col] = True

    return found

def extract_geometry_metadata(data_root):
    """
    Extract geometry metadata (screen width, viewing distance, sampling rate)
    from participants.tsv or dataset_description.json.
    Falls back to defaults if missing.
    """
    metadata = {
        'screen_width_mm': 600, # Default
        'viewing_distance_cm': 60, # Default
        'sampling_rate_hz': 60, # Default
        'fps': DEFAULT_FPS
    }
    
    # Try dataset_description.json
    desc_path = Path(data_root) / "dataset_description.json"
    desc = load_json_file(desc_path)
    if desc:
        if 'sampling_rate' in desc:
            metadata['sampling_rate_hz'] = desc['sampling_rate']
            metadata['fps'] = desc['sampling_rate']
        if 'screen_width' in desc:
            metadata['screen_width_mm'] = desc['screen_width']
        if 'viewing_distance' in desc:
            metadata['viewing_distance_cm'] = desc['viewing_distance']

    # Try participants.tsv (usually contains subject info, but might have metadata)
    part_path = Path(data_root) / "participants.tsv"
    if part_path.exists():
        # Simple parsing for TSV without pandas to keep deps low
        with open(part_path, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                headers = lines[0].strip().split('\t')
                # Look for common metadata columns
                for i, h in enumerate(headers):
                    if 'fps' in h.lower() or 'sampling_rate' in h.lower():
                        metadata['sampling_rate_hz'] = float(lines[1].strip().split('\t')[i])
                        metadata['fps'] = metadata['sampling_rate_hz']
    
    return metadata

def calculate_ivt_threshold(metadata):
    """
    Calculate pixel-threshold for I-VT algorithm.
    threshold_pixels_per_frame = (deg/s) * (pixels_per_degree) / (sampling_rate_hz)
    Uses literature default for deg/s (30 deg/s) if not specified.
    """
    deg_per_s = 30.0 # Default literature value
    # pixels_per_degree = (screen_width_mm / 2) / (tan(fov/2) * viewing_distance)
    # Simplified: assuming 40 deg horizontal FOV for calculation
    fov_deg = 40.0
    rad = fov_deg * (3.14159 / 180.0)
    pixels_per_degree = (metadata['screen_width_mm'] / 2) / (math.tan(rad / 2) * metadata['viewing_distance_cm'] * 10)
    
    threshold = (deg_per_s * pixels_per_degree) / metadata['sampling_rate_hz']
    return threshold

def verify_temporal_load(data_root, sidecars):
    """
    Verify stimulus_duration_ms in events.tsv sidecars or task-*.json.
    Fallback strategies:
    1. Infer from frame_count * (1000/fps)
    2. Use ISI if available and != duration
    3. Default 100ms
    
    Returns a dict with verification results.
    """
    results = {
        'status': 'SUCCESS',
        'message': '',
        'duration_ms': None,
        'source': None,
        'warnings': []
    }
    
    duration_found = False
    duration_ms = None
    source = None
    warnings = []

    # 1. Check events.tsv sidecars
    for sidecar in sidecars['events']:
        data = load_json_file(sidecar)
        if not data:
            continue
        
        # Check for stimulus_duration_ms
        if 'stimulus_duration_ms' in data:
            duration_ms = data['stimulus_duration_ms']
            source = sidecar.name
            duration_found = True
            break
        
        # Check in columns
        if 'columns' in data:
            for col in data['columns']:
                if isinstance(col, dict) and col.get('name') == 'stimulus_duration_ms':
                    duration_ms = col.get('duration') # Sometimes duration is in the column def
                    source = sidecar.name
                    duration_found = True
                    break

    # 2. Check task-*.json sidecars if not found
    if not duration_found:
        for sidecar in sidecars['task']:
            data = load_json_file(sidecar)
            if not data:
                continue
            
            if 'stimulus_duration_ms' in data:
                duration_ms = data['stimulus_duration_ms']
                source = sidecar.name
                duration_found = True
                break
            
            # Check for frame_count and fps
            if 'frame_count' in data:
                frame_count = data['frame_count']
                fps = data.get('sampling_rate', DEFAULT_FPS)
                if fps == 0: fps = DEFAULT_FPS
                inferred_duration = frame_count * (1000 / fps)
                if inferred_duration > 0:
                    duration_ms = inferred_duration
                    source = f"{sidecar.name} (inferred)"
                    duration_found = True
                    warnings.append(f"Inferred duration from frame_count ({frame_count}) and fps ({fps})")
                    break

    # 3. Fallback to ISI
    if not duration_found:
        for sidecar in sidecars['events'] + sidecars['task']:
            data = load_json_file(sidecar)
            if not data:
                continue
            
            if 'ISI' in data:
                isi = data['ISI']
                # If ISI is provided and we assume it's the duration (or ISI == duration in some paradigms)
                # The task says: "If only ISI is available and ISI != duration, use default 100ms"
                # This implies if ISI IS the duration, use it. But usually ISI is inter-stimulus.
                # We'll treat ISI as a potential duration indicator if no explicit duration exists.
                # However, strict interpretation: if ISI != duration (meaning we don't know duration), use 100.
                # Since we don't know duration, we use 100.
                pass
        
        # If we are here, we didn't find duration or frame_count.
        # Check if ISI exists and treat as fallback
        for sidecar in sidecars['events'] + sidecars['task']:
            data = load_json_file(sidecar)
            if data and 'ISI' in data:
                # The prompt says: "If only ISI is available and ISI != duration, use a default of 100ms"
                # This implies we use 100ms if we can't determine duration from ISI.
                # So we default to 100ms.
                duration_ms = DEFAULT_DURATION_MS
                source = "Default (ISI fallback)"
                duration_found = True
                warnings.append(f"Using default duration {DEFAULT_DURATION_MS}ms (ISI available but duration unknown)")
                break

    # Final Fallback
    if not duration_found:
        duration_ms = DEFAULT_DURATION_MS
        source = "Default (Hardcoded)"
        warnings.append(f"No duration found. Using default {DEFAULT_DURATION_MS}ms")

    results['duration_ms'] = duration_ms
    results['source'] = source
    results['warnings'] = warnings
    results['status'] = 'SUCCESS' if not warnings else 'SUCCESS_WITH_WARNINGS'
    results['message'] = f"Duration found: {duration_ms}ms from {source}"

    return results

def main():
    """
    Main entry point for T039: Temporal-Load Check.
    Verifies stimulus_duration_ms and logs results.
    """
    parser = argparse.ArgumentParser(description="Verify temporal load (stimulus duration) in BIDS dataset.")
    parser.add_argument("--data_root", type=str, required=True, help="Path to the BIDS dataset root.")
    parser.add_argument("--task", type=str, default=None, help="Specific task name to filter sidecars.")
    args = parser.parse_args()

    # Setup logging
    log_path = Path(LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logging(log_file=log_path, level=logging.INFO)
    logger.info("Starting Temporal-Load Check (T039)...")

    try:
        # Find sidecars
        sidecars = find_bids_sidecars(args.data_root, args.task)
        logger.info(f"Found {len(sidecars['events'])} events sidecars and {len(sidecars['task'])} task sidecars.")

        # Verify temporal load
        result = verify_temporal_load(args.data_root, sidecars)

        # Log results
        logger.info(f"Verification Result: {result['status']}")
        logger.info(f"Message: {result['message']}")
        for warn in result['warnings']:
            logger.warning(warn)

        # Write a summary to the log file (already handled by setup_logging)
        # The log file itself is the deliverable.
        
        logger.info("Temporal-Load Check completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during Temporal-Load Check: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())