import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from config import get_config
from utils.logging_config import get_logger, info, error, warning, log_error

logger = get_logger(__name__)

def load_roi_timecourses() -> Dict[str, np.ndarray]:
    """
    Loads the combined ROI timecourses from data/processed/roi_timecourses.csv.
    Returns a dictionary keyed by (subject_id, roi) with numpy arrays of signals.
    """
    csv_path = Path("data/processed/roi_timecourses.csv")
    if not csv_path.exists():
        log_error("E001", f"Missing required file: {csv_path}")
        raise FileNotFoundError(f"Missing required file: {csv_path}")

    data = {}
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_id = row['subject_id']
            roi = row['roi']
            timepoint = int(row['timepoint'])
            signal = float(row['signal'])
            
            key = (sub_id, roi)
            if key not in data:
                data[key] = {}
            data[key][timepoint] = signal

    # Convert to numpy arrays, ensuring contiguous timepoints starting from 0
    result = {}
    for key, time_dict in data.items():
        if not time_dict:
            continue
        max_tp = max(time_dict.keys())
        arr = np.zeros(max_tp + 1)
        for tp, val in time_dict.items():
            arr[tp] = val
        result[key] = arr
    
    return result

def load_events_metadata() -> List[Dict[str, Any]]:
    """
    Loads event boundaries from data/text/rocstories_sample_boundaries.jsonl.
    Returns a list of dicts with 'story_id', 'event_id', 'start_timepoint', 'end_timepoint'.
    """
    jsonl_path = Path("data/text/rocstories_sample_boundaries.jsonl")
    if not jsonl_path.exists():
        log_error("E001", f"Missing required file: {jsonl_path}")
        raise FileNotFoundError(f"Missing required file: {jsonl_path}")

    events = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Expected fields: story_id, event_id, start_timepoint, end_timepoint
                if 'story_id' not in record or 'event_id' not in record:
                    warning(f"Skipping malformed event record missing story_id or event_id")
                    continue
                if 'start_timepoint' not in record or 'end_timepoint' not in record:
                    warning(f"Skipping event record missing timepoint bounds for {record.get('story_id')}")
                    continue
                events.append(record)
            except json.JSONDecodeError as e:
                warning(f"Skipping invalid JSON line in events file: {e}")
    
    if not events:
        log_error("E002", "No valid event boundaries found in metadata file.")
        raise ValueError("No valid event boundaries found in metadata file.")
        
    return events

def compute_event_averages(
    timecourses: Dict[Tuple[str, str], np.ndarray],
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Computes mean BOLD signal per event for each subject and ROI.
    
    Aggregation method: 'mean' (averaging timepoints within event boundaries).
    
    Returns a list of dicts: 
    [
      {"subject_id": "...", "event_id": "...", "roi": "...", "mean_signal": float},
      ...
    ]
    """
    results = []
    config = get_config()
    logger.info(f"Computing event averages. Aggregation method: 'mean'.")
    
    # Map story_id to events for faster lookup
    events_by_story = {}
    for ev in events:
        sid = ev['story_id']
        if sid not in events_by_story:
            events_by_story[sid] = []
        events_by_story[sid].append(ev)

    # Iterate over all timecourse keys (subject_id, roi)
    for (sub_id, roi), signal_arr in timecourses.items():
        # Find events associated with this subject (assuming story_id matches subject_id or mapping exists)
        # In this pipeline, story_id in events usually corresponds to the subject_id in fMRI data
        # based on the T019a/T021a flow.
        subject_events = events_by_story.get(sub_id, [])
        
        if not subject_events:
            warning(f"No events found for subject {sub_id}. Skipping.")
            continue

        for ev in subject_events:
            start_tp = int(ev['start_timepoint'])
            end_tp = int(ev['end_timepoint'])
            event_id = ev['event_id']
            
            # Ensure bounds are within signal array
            if start_tp >= len(signal_arr):
                warning(f"Event {event_id} for {sub_id} starts beyond signal length. Skipping.")
                continue
            
            end_idx = min(end_tp + 1, len(signal_arr)) # inclusive start, exclusive end for slicing
            if start_tp >= end_idx:
                warning(f"Event {event_id} for {sub_id} has invalid bounds ({start_tp} >= {end_idx}). Skipping.")
                continue
            
            segment = signal_arr[start_tp:end_idx]
            if segment.size == 0:
                warning(f"Event {event_id} for {sub_id} has empty segment. Skipping.")
                continue
            
            mean_val = float(np.mean(segment))
            
            results.append({
                "subject_id": sub_id,
                "event_id": event_id,
                "roi": roi,
                "mean_signal": mean_val
            })
    
    return results

def save_event_averages(averages: List[Dict[str, Any]], output_path: str):
    """
    Saves the computed event averages to a CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not averages:
        warning("No averages to save.")
        return

    fieldnames = ["subject_id", "event_id", "roi", "mean_signal"]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(averages)
    
    info(f"Saved event averages to {output_path} ({len(averages)} rows).")

def main():
    """
    Main entry point for T021a: Compute mean BOLD per event.
    Requires T017c (roi_timecourses.csv) and T019a (rocstories_sample_boundaries.jsonl).
    Output: data/processed/event_averages_tmp.csv
    """
    info("Starting T021a: Compute mean BOLD per event.")
    
    try:
        # Load dependencies
        timecourses = load_roi_timecourses()
        events = load_events_metadata()
        
        if not timecourses:
            log_error("E002", "No timecourses loaded. Cannot compute averages.")
            sys.exit(1)
        
        # Compute averages
        averages = compute_event_averages(timecourses, events)
        
        # Save intermediate results
        output_path = "data/processed/event_averages_tmp.csv"
        save_event_averages(averages, output_path)
        
        info("T021a completed successfully.")
        
    except FileNotFoundError as e:
        log_error("E001", str(e))
        sys.exit(1)
    except ValueError as e:
        log_error("E002", str(e))
        sys.exit(1)
    except Exception as e:
        log_error("E003", f"Unexpected error in T021a: {e}")
        raise

if __name__ == "__main__":
    main()