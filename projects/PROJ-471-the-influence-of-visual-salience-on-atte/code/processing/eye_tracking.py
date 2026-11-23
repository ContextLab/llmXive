"""
Eye-tracking data parsing and metric extraction for 'Face' ROIs.

This module parses raw eye-tracking files (assumed to be in a standard format
like Tobii Pro Lab export or similar CSV structure), filters fixations for
the "Face" Area of Interest (AOI), and calculates:
- First-Fixation Probability: Probability that the first fixation on an image
  lands within the Face AOI.
- Dwell Time: Total duration (ms) spent fixating within the Face AOI.
- Latency: Time (ms) from stimulus onset to the first fixation within the Face AOI.

Output is written to `data/interim/fixation_metrics.csv`.
"""

import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, load_config
from utils.logging import get_logger, log_error_context
from data_models import FixationTrial

logger = get_logger(__name__)

@dataclass
class EyeTrackingMetrics:
    """Container for calculated eye-tracking metrics per trial."""
    trial_id: str
    stimulus_id: str
    first_fixation_prob: float
    dwell_time_ms: float
    latency_ms: float
    total_fixations: int
    face_fixations: int
    has_face_aoi: bool

def parse_raw_eye_tracking_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parses a raw eye-tracking CSV file.
    
    Expected columns (case-insensitive):
    - TrialID, StimulusID (or ImageID)
    - FixationID
    - FixationStartTime (ms relative to stimulus onset)
    - FixationDuration (ms)
    - AOI_Name (or similar, containing "Face")
    - X, Y coordinates (optional, for validation)

    Returns a list of fixation dictionaries.
    """
    fixations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Normalize keys
            if not reader.fieldnames:
                logger.error(f"Empty or invalid CSV file: {file_path}")
                return []
            
            normalized_fieldnames = [k.strip().lower() for k in reader.fieldnames]
            
            for row in reader:
                # Normalize row keys
                normalized_row = {k.strip().lower(): v for k, v in row.items()}
                
                # Basic validation
                if 'trialid' not in normalized_row or 'fixationstarttime' not in normalized_row:
                    continue
                
                fixations.append(normalized_row)
                
    except FileNotFoundError:
        logger.error(f"Raw eye-tracking file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error parsing eye-tracking file {file_path}: {e}")
        raise

    return fixations

def filter_face_roi(fixations: List[Dict[str, Any]], aoi_column: str = 'aoi_name') -> List[Dict[str, Any]]:
    """
    Filters fixations to only those within the 'Face' AOI.
    Handles case-insensitivity and potential partial matches.
    """
    face_fixations = []
    for fix in fixations:
        aoi_val = fix.get(aoi_column, '')
        if aoi_val and 'face' in aoi_val.lower():
            face_fixations.append(fix)
    return face_fixations

def calculate_metrics(fixations: List[Dict[str, Any]], trial_id: str, stimulus_id: str) -> EyeTrackingMetrics:
    """
    Calculates First-Fixation Probability, Dwell Time, and Latency.
    
    Logic:
    - Group fixations by trial and stimulus.
    - Sort by FixationStartTime.
    - First Fixation Probability: 1.0 if the very first fixation (global start) is in Face, else 0.0.
    - Dwell Time: Sum of durations of all Face fixations.
    - Latency: Start time of the first Face fixation (if any).
    """
    if not fixations:
        return EyeTrackingMetrics(
            trial_id=trial_id,
            stimulus_id=stimulus_id,
            first_fixation_prob=0.0,
            dwell_time_ms=0.0,
            latency_ms=0.0,
            total_fixations=0,
            face_fixations=0,
            has_face_aoi=False
        )

    # Sort by start time
    sorted_fixations = sorted(fixations, key=lambda x: float(x.get('fixationstarttime', 0)))
    
    total_fixations = len(sorted_fixations)
    face_fixations_list = [f for f in sorted_fixations if 'face' in f.get('aoi_name', '').lower()]
    face_count = len(face_fixations_list)
    
    # First Fixation Probability: Is the absolute first fixation in the trial a Face fixation?
    first_fixation_prob = 0.0
    if sorted_fixations:
        first_aoi = sorted_fixations[0].get('aoi_name', '')
        if 'face' in first_aoi.lower():
            first_fixation_prob = 1.0

    # Dwell Time: Sum of durations
    dwell_time_ms = sum(float(f.get('fixationduration', 0)) for f in face_fixations_list)

    # Latency: Time to first Face fixation
    latency_ms = 0.0
    has_face_aoi = False
    if face_fixations_list:
        has_face_aoi = True
        latency_ms = float(face_fixations_list[0].get('fixationstarttime', 0))

    return EyeTrackingMetrics(
        trial_id=trial_id,
        stimulus_id=stimulus_id,
        first_fixation_prob=first_fixation_prob,
        dwell_time_ms=dwell_time_ms,
        latency_ms=latency_ms,
        total_fixations=total_fixations,
        face_fixations=face_count,
        has_face_aoi=has_face_aoi
    )

def process_eye_tracking_data(input_dir: Path, output_path: Path) -> List[EyeTrackingMetrics]:
    """
    Main processing loop.
    Iterates over raw eye-tracking files in input_dir, processes them,
    and writes results to output_path.
    """
    logger.info(f"Starting eye-tracking processing for directory: {input_dir}")
    
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    results = []
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {input_dir}")
        return results

    for csv_file in csv_files:
        try:
            # Parse
            raw_fixations = parse_raw_eye_tracking_file(csv_file)
            if not raw_fixations:
                logger.warning(f"No valid fixations found in {csv_file.name}")
                continue

            # We expect one file per trial or one file containing multiple trials.
            # Assuming one file per trial for simplicity based on typical exports,
            # but handling grouping if multiple trials exist in one file.
            
            # Group by TrialID
            trials_data: Dict[str, List[Dict]] = {}
            for fix in raw_fixations:
                tid = fix.get('trialid', 'unknown')
                sid = fix.get('stimulusid', fix.get('imageid', 'unknown'))
                if tid not in trials_data:
                    trials_data[tid] = {'stimulus_id': sid, 'fixations': []}
                trials_data[tid]['fixations'].append(fix)

            for tid, data in trials_data.items():
                metrics = calculate_metrics(
                    data['fixations'],
                    tid,
                    data['stimulus_id']
                )
                results.append(metrics)
                logger.debug(f"Processed trial {tid}: Face AOI={metrics.has_face_aoi}, Dwell={metrics.dwell_time_ms}ms")

        except Exception as e:
            logger.error(f"Failed to process file {csv_file.name}: {e}", exc_info=True)
            # Continue to next file

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'trial_id', 'stimulus_id', 'first_fixation_prob', 'dwell_time_ms', 
        'latency_ms', 'total_fixations', 'face_fixations', 'has_face_aoi'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(asdict(res))

    logger.info(f"Wrote {len(results)} metrics to {output_path}")
    return results

def main():
    """Entry point for the script."""
    config = load_config()
    paths = get_paths()
    
    # Define input/output paths based on project structure
    # Assuming raw eye-tracking data is in data/raw/eye_tracking/
    input_dir = paths.data_raw / "eye_tracking"
    output_file = paths.data_interim / "fixation_metrics.csv"
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist. Please download data first.")
        sys.exit(1)

    try:
        metrics = process_eye_tracking_data(input_dir, output_file)
        
        # Validation: Verify column exists and is numeric
        if not metrics:
            logger.warning("No metrics generated. Check input data.")
            return

        # Quick check on first result
        first = metrics[0]
        if not isinstance(first.first_fixation_prob, (int, float)):
            raise TypeError(f"first_fixation_prob is not numeric: {type(first.first_fixation_prob)}")
        
        logger.info("Eye-tracking processing completed successfully.")
        
    except Exception as e:
        log_error_context(e, "Eye-tracking processing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()