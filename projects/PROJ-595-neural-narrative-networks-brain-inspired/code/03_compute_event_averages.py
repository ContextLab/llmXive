"""
Compute mean BOLD signal per event for each ROI.

This script reads the ROI timecourses generated in T013 (or synthetic placeholders
if T013 is pending) and the events metadata from T016, computes the average signal
within each event window, and saves the result to:
    data/neural/processed/event_averages.csv

Output columns: subject_id, event_id, roi, mean_signal
"""
import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from config import get_config
from utils.logging_config import get_logger, info, error, warning

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = get_config()
logger = get_logger(__name__)

DATA_DIR = Path("data")
NEURAL_PROCESSED_DIR = DATA_DIR / "neural" / "processed"
TEXT_DIR = DATA_DIR / "text"

# Ensure output directory exists
NEURAL_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def load_roi_timecourses(subject_id: str) -> Optional[np.ndarray]:
    """
    Load ROI timecourses for a given subject.
    
    Expected file: data/neural/processed/roi_timecourses_{subject_id}.csv
    or .npy if preferred.
    
    Returns:
        numpy array of shape (num_rois, num_timepoints) or None if file missing.
    """
    csv_path = NEURAL_PROCESSED_DIR / f"roi_timecourses_{subject_id}.csv"
    npy_path = NEURAL_PROCESSED_DIR / f"roi_timecourses_{subject_id}.npy"

    if csv_path.exists():
        logger.info(f"Loading ROI timecourses from CSV: {csv_path}")
        # Assume CSV format: roi_name,timepoint_0,timepoint_1,...
        data = []
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # skip header if present
            for row in reader:
                if not row:
                    continue
                # First column is ROI name, rest are floats
                roi_name = row[0]
                values = [float(v) for v in row[1:]]
                data.append(values)
        return np.array(data, dtype=np.float32)
    elif npy_path.exists():
        logger.info(f"Loading ROI timecourses from NPY: {npy_path}")
        return np.load(npy_path)
    else:
        error(f"ROI timecourses file not found for subject {subject_id}: {csv_path} or {npy_path}")
        return None

def load_events_metadata(subject_id: str) -> List[Dict[str, Any]]:
    """
    Load events metadata for a given subject.
    
    Expected file: data/text/events_{subject_id}.json (or similar).
    In the absence of real events, we generate synthetic events for demonstration,
    but this function should be updated when real events are available.
    
    Returns:
        List of dicts with keys: event_id, start_time, end_time, event_type
    """
    # Try to load from a standard location
    events_file = TEXT_DIR / f"events_{subject_id}.json"
    if events_file.exists():
        with open(events_file, "r", encoding="utf-8") as f:
            events = json.load(f)
        return events

    # Fallback: generate synthetic events for testing if none exist
    # In production, this should raise an error or be removed.
    logger.warning(f"No events metadata found for subject {subject_id}. Generating synthetic events.")
    synthetic_events = []
    num_events = 10
    for i in range(num_events):
        event = {
            "event_id": f"{subject_id}_event_{i:03d}",
            "start_time": i * 2.0,
            "end_time": (i + 1) * 2.0,
            "event_type": "stop_signal" if i % 2 == 0 else "go_signal"
        }
        synthetic_events.append(event)
    return synthetic_events

def compute_event_averages(
    timecourses: np.ndarray,
    events: List[Dict[str, Any]],
    subject_id: str,
    roi_names: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Compute mean BOLD signal per event for each ROI.
    
    Args:
        timecourses: numpy array of shape (num_rois, num_timepoints)
        events: list of event dicts with start_time, end_time, event_id
        subject_id: subject identifier
        roi_names: optional list of ROI names matching the rows in timecourses
    
    Returns:
        List of dicts with keys: subject_id, event_id, roi, mean_signal
    """
    if timecourses is None or timecourses.size == 0:
        error(f"No timecourses available for subject {subject_id}")
        return []

    num_rois, num_timepoints = timecourses.shape
    if roi_names is None:
        roi_names = [f"roi_{i}" for i in range(num_rois)]

    results = []
    for event in events:
        start = int(event["start_time"])
        end = int(event["end_time"])
        
        # Clamp indices to valid range
        start = max(0, start)
        end = min(num_timepoints, end)
        
        if start >= end:
            warning(f"Invalid time window for event {event['event_id']}: [{start}, {end})")
            continue

        for roi_idx, roi_name in enumerate(roi_names):
            signal = timecourses[roi_idx, start:end]
            if signal.size == 0:
                mean_signal = np.nan
            else:
                mean_signal = float(np.mean(signal))
            
            results.append({
                "subject_id": subject_id,
                "event_id": event["event_id"],
                "roi": roi_name,
                "mean_signal": mean_signal
            })
    
    return results

def save_event_averages(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save event averages to CSV.
    
    Args:
        results: list of dicts with keys: subject_id, event_id, roi, mean_signal
        output_path: path to output CSV file
    """
    if not results:
        warning("No event averages to save.")
        return

    fieldnames = ["subject_id", "event_id", "roi", "mean_signal"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved event averages to {output_path} ({len(results)} rows)")

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Main entry point: load timecourses and events, compute averages, save results.
    """
    # Define subjects to process
    # In a real pipeline, this would come from a manifest or directory listing
    subjects = ["sub-001", "sub-002", "sub-003"]  # placeholder subjects

    all_results = []

    for subject_id in subjects:
        info(f"Processing subject: {subject_id}")
        
        # Load timecourses
        timecourses = load_roi_timecourses(subject_id)
        if timecourses is None:
            continue

        # Determine ROI names from file or default
        csv_path = NEURAL_PROCESSED_DIR / f"roi_timecourses_{subject_id}.csv"
        roi_names = None
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header and len(header) > 1:
                    roi_names = [header[i] for i in range(1, len(header))]
                    # If header is just indices, use defaults
                    if roi_names and roi_names[0].isdigit():
                        roi_names = None

        # Load events
        events = load_events_metadata(subject_id)
        
        # Compute averages
        results = compute_event_averages(timecourses, events, subject_id, roi_names)
        all_results.extend(results)

    # Save combined results
    output_path = NEURAL_PROCESSED_DIR / "event_averages.csv"
    save_event_averages(all_results, output_path)

    info("Event average computation complete.")

if __name__ == "__main__":
    main()