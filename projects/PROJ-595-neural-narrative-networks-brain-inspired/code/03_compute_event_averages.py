"""
T017: Compute mean BOLD per event and save to data/neural/processed/event_averages.csv.

Reads the ROI timecourses generated in T013 (data/neural/processed/roi_timecourses.csv)
and the event metadata (expected to be in data/neural/processed/events.json or similar),
groups timepoints by event, computes the mean signal per (subject, event, roi),
and writes the result to data/neural/processed/event_averages.csv.

Columns: subject_id, event_id, roi, mean_signal
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_config
from utils.logging_config import get_logger, info, error, warning, debug

logger = get_logger(__name__)
config = get_config()

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROI_TIMECOURSES_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "roi_timecourses.csv"
EVENTS_METADATA_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "events.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "neural" / "processed" / "event_averages.csv"

def load_roi_timecourses() -> pd.DataFrame:
    """
    Load the ROI timecourses CSV.
    Expected columns: subject_id, roi, timepoint, signal (or similar).
    We assume the T013 output format.
    """
    if not ROI_TIMECOURSES_PATH.exists():
        error(f"ROI timecourses file not found: {ROI_TIMECOURSES_PATH}")
        raise FileNotFoundError(f"Missing required input file: {ROI_TIMECOURSES_PATH}")

    logger.info(f"Loading ROI timecourses from {ROI_TIMECOURSES_PATH}")
    df = pd.read_csv(ROI_TIMECOURSES_PATH)

    # Basic validation
    required_cols = {"subject_id", "roi", "timepoint", "signal"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        error(f"ROI timecourses missing required columns: {missing}")
        raise ValueError(f"Invalid ROI timecourses format. Missing: {missing}")

    return df

def load_events_metadata() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load events metadata JSON.
    Expected format: { "subject_id": [ { "event_id": "...", "start": int, "end": int }, ... ] }
    """
    if not EVENTS_METADATA_PATH.exists():
        error(f"Events metadata file not found: {EVENTS_METADATA_PATH}")
        raise FileNotFoundError(f"Missing required input file: {EVENTS_METADATA_PATH}")

    logger.info(f"Loading events metadata from {EVENTS_METADATA_PATH}")
    with open(EVENTS_METADATA_PATH, "r") as f:
        data = json.load(f)

    return data

def compute_event_averages(
    timecourses_df: pd.DataFrame,
    events_data: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Compute mean BOLD signal per event for each ROI.

    Returns a list of dicts: { subject_id, event_id, roi, mean_signal }
    """
    results = []

    # Group timecourses by subject for efficiency
    subjects = timecourses_df["subject_id"].unique()

    for subject_id in subjects:
        subject_data = timecourses_df[timecourses_df["subject_id"] == subject_id]
        
        # Get events for this subject
        if subject_id not in events_data:
            warning(f"No events found for subject {subject_id}, skipping.")
            continue

        subject_events = events_data[subject_id]

        for event in subject_events:
            event_id = event.get("event_id")
            start_timepoint = event.get("start")
            end_timepoint = event.get("end")

            if event_id is None or start_timepoint is None or end_timepoint is None:
                warning(f"Invalid event structure for subject {subject_id}: {event}")
                continue

            # Filter timepoints for this event
            event_mask = (subject_data["timepoint"] >= start_timepoint) & \
                         (subject_data["timepoint"] < end_timepoint)
            event_timepoints = subject_data[event_mask]

            if event_timepoints.empty:
                warning(f"No timepoints found for event {event_id} in subject {subject_id}")
                continue

            # Compute mean per ROI
            rois = event_timepoints["roi"].unique()
            for roi in rois:
                roi_data = event_timepoints[event_timepoints["roi"] == roi]
                mean_signal = roi_data["signal"].mean()

                results.append({
                    "subject_id": subject_id,
                    "event_id": event_id,
                    "roi": roi,
                    "mean_signal": float(mean_signal)
                })

    return results

def save_event_averages(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the computed averages to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving {len(results)} event averages to {output_path}")

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id", "event_id", "roi", "mean_signal"])
        writer.writeheader()
        writer.writerows(results)

    info(f"Successfully wrote event averages to {output_path}")

def main() -> None:
    """
    Main entry point for T017.
    """
    try:
        # Load inputs
        timecourses_df = load_roi_timecourses()
        events_data = load_events_metadata()

        # Compute averages
        results = compute_event_averages(timecourses_df, events_data)

        if not results:
            error("No event averages computed. Check input data.")
            raise RuntimeError("No data processed for event averages.")

        # Save output
        save_event_averages(results, OUTPUT_PATH)

        info("T017 completed successfully.")

    except Exception as e:
        error(f"T017 failed: {e}")
        raise

if __name__ == "__main__":
    main()
