"""
Compute mean BOLD signal per event for each ROI.

Reads:
  - data/neural/processed/roi_timecourses.csv (columns: subject_id, roi, timepoint, signal)
  - data/neural/events/events_metadata.json (columns: subject_id, event_id, roi, onset, duration)

Writes:
  - data/neural/processed/event_averages.csv (columns: subject_id, event_id, roi, mean_signal)
"""
import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from config import get_config
from utils.logging_config import get_logger, info, error, warning

logger = get_logger(__name__)
cfg = get_config()

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROI_TIMECOURSES_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "roi_timecourses.csv"
EVENTS_METADATA_PATH = PROJECT_ROOT / "data" / "neural" / "events" / "events_metadata.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "event_averages.csv"

def load_roi_timecourses(path: Path) -> Dict[Tuple[str, str], np.ndarray]:
    """
    Load ROI timecourses from CSV into a dictionary keyed by (subject_id, roi).
    Values are 1D numpy arrays of signal values ordered by timepoint.
    """
    if not path.exists():
        error(f"ROI timecourses file not found: {path}")
        raise FileNotFoundError(f"ROI timecourses file not found: {path}")
    
    data: Dict[Tuple[str, str], List[float]] = {}
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Validate required columns
        if not {"subject_id", "roi", "timepoint", "signal"}.issubset(set(reader.fieldnames or [])):
            error(f"ROI timecourses CSV missing required columns. Found: {reader.fieldnames}")
            raise ValueError("ROI timecourses CSV missing required columns")
        
        for row in reader:
            subj = row["subject_id"]
            roi = row["roi"]
            try:
                tpoint = int(row["timepoint"])
                signal = float(row["signal"])
            except (ValueError, TypeError) as e:
                error(f"Invalid numeric value in row: {row} - {e}")
                raise e
            
            key = (subj, roi)
            if key not in data:
                data[key] = []
            data[key].append((tpoint, signal))
    
    # Sort by timepoint and extract signals
    result: Dict[Tuple[str, str], np.ndarray] = {}
    for key, pairs in data.items():
        pairs.sort(key=lambda x: x[0])
        signals = [p[1] for p in pairs]
        result[key] = np.array(signals, dtype=np.float32)
    
    logger.info(f"Loaded {len(result)} subject-ROI timecourses from {path}")
    return result

def load_events_metadata(path: Path) -> List[Dict[str, Any]]:
    """
    Load events metadata from JSON.
    Expected structure: a list of dicts with keys: subject_id, event_id, roi, onset, duration.
    """
    if not path.exists():
        error(f"Events metadata file not found: {path}")
        raise FileNotFoundError(f"Events metadata file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        events = json.load(f)
    
    if not isinstance(events, list):
        error(f"Events metadata must be a list, got {type(events)}")
        raise ValueError("Events metadata must be a list")
    
    required_keys = {"subject_id", "event_id", "roi", "onset", "duration"}
    for i, ev in enumerate(events):
        if not required_keys.issubset(set(ev.keys())):
            error(f"Event at index {i} missing required keys. Found: {ev.keys()}")
            raise ValueError(f"Event at index {i} missing required keys")
    
    logger.info(f"Loaded {len(events)} events from {path}")
    return events

def compute_event_averages(
    timecourses: Dict[Tuple[str, str], np.ndarray],
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Compute mean BOLD signal for each event.
    
    For each event:
      - Identify the timepoints corresponding to [onset, onset + duration)
      - Extract the signal from the timecourse for (subject_id, roi)
      - Compute the mean of those signal values
      - If no valid timepoints exist (e.g., outside range), record NaN
    """
    results = []
    
    # Pre-compute timepoint range for each timecourse to handle offset if needed.
    # We assume timepoints are 0-indexed integers matching the event onset/duration directly.
    
    for ev in events:
        subj = ev["subject_id"]
        event_id = ev["event_id"]
        roi = ev["roi"]
        onset = int(ev["onset"])
        duration = int(ev["duration"])
        
        key = (subj, roi)
        if key not in timecourses:
            warning(f"No timecourse found for {key}, skipping event {event_id}")
            results.append({
                "subject_id": subj,
                "event_id": event_id,
                "roi": roi,
                "mean_signal": np.nan
            })
            continue
        
        signals = timecourses[key]
        total_timepoints = len(signals)
        
        # Define range [onset, onset + duration)
        start_idx = onset
        end_idx = onset + duration
        
        if start_idx >= total_timepoints:
            warning(f"Event {event_id} onset {start_idx} >= total timepoints {total_timepoints}")
            mean_val = np.nan
        elif end_idx > total_timepoints:
            # Clip to available data
            clip_end = total_timepoints
            if start_idx >= clip_end:
                mean_val = np.nan
            else:
                mean_val = float(np.mean(signals[start_idx:clip_end]))
        else:
            mean_val = float(np.mean(signals[start_idx:end_idx]))
        
        results.append({
            "subject_id": subj,
            "event_id": event_id,
            "roi": roi,
            "mean_signal": mean_val
        })
    
    return results

def save_event_averages(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save event averages to CSV.
    Columns: subject_id, event_id, roi, mean_signal
    """
    if output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["subject_id", "event_id", "roi", "mean_signal"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Saved {len(results)} event averages to {output_path}")

def main() -> None:
    """Main entry point for computing event averages."""
    info("Starting event average computation...")
    
    try:
        timecourses = load_roi_timecourses(ROI_TIMECOURSES_PATH)
        events = load_events_metadata(EVENTS_METADATA_PATH)
        
        if not timecourses:
            error("No timecourses loaded. Cannot compute averages.")
            return
        
        if not events:
            error("No events loaded. Cannot compute averages.")
            return
        
        results = compute_event_averages(timecourses, events)
        save_event_averages(results, OUTPUT_PATH)
        
        info("Event average computation completed successfully.")
        
    except FileNotFoundError as e:
        error(f"Data file missing: {e}")
        raise
    except Exception as e:
        error(f"Unexpected error during computation: {e}")
        raise

if __name__ == "__main__":
    main()