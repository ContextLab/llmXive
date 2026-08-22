import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging_config import get_logger, info, error, warning, log_error
from utils.schema_validation import validate_neural_data

logger = get_logger(__name__)

def load_roi_timecourses() -> Dict[str, np.ndarray]:
    """
    Load combined ROI timecourses from data/processed/roi_timecourses.csv.
    Returns a dictionary mapping ROI names to 2D arrays (subject, timepoint).
    """
    csv_path = Path("data/processed/roi_timecourses.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Required input file missing: {csv_path}")

    # Load using pandas for easier grouping, then convert to dict
    import pandas as pd
    df = pd.read_csv(csv_path)
    
    # Verify required columns
    required_cols = ['subject_id', 'roi', 'timepoint', 'signal']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV missing required columns. Found: {df.columns.tolist()}")

    roi_data = {}
    # Group by ROI and subject
    for roi in df['roi'].unique():
        roi_df = df[df['roi'] == roi]
        subjects = roi_df['subject_id'].unique()
        
        # Assume timepoints are 0..T-1 for each subject
        # We'll stack them into a 2D array: (n_subjects, n_timepoints)
        subject_list = sorted(subjects)
        if len(subject_list) == 0:
            continue
            
        # Determine max timepoints (assume uniform)
        max_tp = roi_df['timepoint'].max() + 1
        
        matrix = np.zeros((len(subject_list), max_tp))
        for i, subj in enumerate(subject_list):
            subj_data = roi_df[roi_df['subject_id'] == subj].sort_values('timepoint')
            signals = subj_data['signal'].values
            if len(signals) > 0:
                matrix[i, :len(signals)] = signals
        
        roi_data[roi] = matrix
        logger.info(f"Loaded ROI '{roi}' with shape {matrix.shape}")

    return roi_data

def load_events_metadata() -> Dict[str, List[Dict]]:
    """
    Load events metadata from data/text/rocstories_sample.jsonl.
    Returns a dictionary mapping subject_id (story_id) to list of event dicts.
    """
    jsonl_path = Path("data/text/rocstories_sample.jsonl")
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Required input file missing: {jsonl_path}")

    events_by_subject = {}
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Assume 'id' or 'story_id' field exists
                subj_id = record.get('id') or record.get('story_id') or record.get('subject_id')
                if not subj_id:
                    logger.warning(f"Line {line_num}: No subject_id found, skipping")
                    continue
                
                # Extract events - assume 'events' field is a list of dicts
                events = record.get('events', [])
                if not events:
                    # Fallback: treat the whole story as one event if 'story' field exists
                    story = record.get('story', '')
                    if story:
                        events = [{'text': story, 'index': 0, 'type': 'story'}]
                
                events_by_subject[str(subj_id)] = events
            except json.JSONDecodeError as e:
                logger.error(f"Line {line_num}: JSON decode error - {e}")
                raise

    logger.info(f"Loaded events for {len(events_by_subject)} subjects")
    return events_by_subject

def compute_event_averages(
    roi_data: Dict[str, np.ndarray],
    events_metadata: Dict[str, List[Dict]],
    time_resolution: float = 2.0  # TR in seconds, default for many fMRI studies
) -> Dict[str, Dict[str, Dict[str, np.ndarray]]]:
    """
    Compute mean BOLD signal per event using direct index mapping.
    
    Mapping logic:
    - Each event in the story has an index (0, 1, 2, ...)
    - We map event index to fMRI timepoints assuming a fixed event duration
    - For simplicity, we assume each event corresponds to ~4 seconds (2 TRs)
      This is a heuristic; in a full implementation, this would use precise timestamps.
    
    Returns nested dict: {subject_id: {roi_name: {event_idx: mean_signal}}}
    """
    config = get_config()
    random_seed = config.get('random_seed', 42)
    np.random.seed(random_seed)

    results = {}
    event_duration_tr = 2  # Assume 2 TRs per event (4 seconds at TR=2s)

    for subj_id, events in events_metadata.items():
        if subj_id not in roi_data:
            logger.warning(f"Subject {subj_id} has events but no ROI timecourses. Skipping.")
            continue
        
        subj_timecourses = roi_data[subj_id]
        n_timepoints = subj_timecourses.shape[1]
        
        results[subj_id] = {}
        
        for roi_name, roi_signals in roi_data.items():
            # If this subject exists in this ROI
            if subj_id in roi_data[roi_name]:
                # Find the row index for this subject in the ROI matrix
                # This assumes subject IDs are sorted and consistent across ROIs
                # In a real implementation, we'd use a mapping table
                subj_idx = None
                # Reconstruct subject list order from the first ROI we loaded
                # For now, we assume the order is preserved and IDs match
                # A more robust approach would store subject order explicitly
                try:
                    # We need to find the index of this subject in the ROI matrix
                    # Since we loaded from CSV, we don't have the original order
                    # We'll assume the CSV was sorted by subject_id
                    # This is a limitation; a real system would store metadata
                    import pandas as pd
                    csv_path = Path("data/processed/roi_timecourses.csv")
                    df = pd.read_csv(csv_path)
                    unique_subjects = df['subject_id'].unique()
                    if subj_id in unique_subjects:
                        subj_idx = list(unique_subjects).index(subj_id)
                    else:
                        logger.warning(f"Subject {subj_id} not found in ROI {roi_name}")
                        continue
                except Exception as e:
                    logger.error(f"Error finding subject index for {subj_id} in {roi_name}: {e}")
                    continue
                
                subj_signal = roi_signals[subj_idx, :]
                
                # Compute event averages
                event_averages = {}
                for event in events:
                    event_idx = event.get('index', 0)
                    if event_idx is None:
                        continue
                    
                    # Map event index to timepoint range
                    start_tp = int(event_idx * event_duration_tr)
                    end_tp = int((event_idx + 1) * event_duration_tr)
                    
                    if start_tp >= n_timepoints:
                        # Event extends beyond available data
                        continue
                    
                    end_tp = min(end_tp, n_timepoints)
                    
                    if start_tp < end_tp:
                        mean_signal = np.mean(subj_signal[start_tp:end_tp])
                        event_averages[event_idx] = float(mean_signal)
                
                if event_averages:
                    results[subj_id][roi_name] = event_averages
    
    return results

def save_event_averages(
    event_averages: Dict[str, Dict[str, Dict[str, float]]],
    output_path: str = "data/processed/mean_bold_intermediate.npy"
):
    """
    Save the computed event averages as a NumPy array.
    
    The array is structured as a dictionary saved with np.save,
    containing the nested structure: {subj_id: {roi: {event_idx: mean}}}
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to a format suitable for np.save
    # We'll save the entire dictionary structure
    np.save(output_file, event_averages, allow_pickle=True)
    logger.info(f"Saved event averages to {output_file}")

    # Also log summary stats
    total_subjects = len(event_averages)
    total_events = sum(
        sum(len(roi_events) for roi_events in subj_rois.values())
        for subj_rois in event_averages.values()
    )
    logger.info(f"Summary: {total_subjects} subjects, {total_events} event-ROI averages computed")

def main():
    """
    Main entry point for computing mean BOLD per event.
    """
    logger.info("Starting T021: Compute mean BOLD per event")
    
    try:
        # Load inputs
        logger.info("Loading ROI timecourses...")
        roi_data = load_roi_timecourses()
        
        logger.info("Loading events metadata...")
        events_metadata = load_events_metadata()
        
        # Compute averages
        logger.info("Computing event averages...")
        event_averages = compute_event_averages(roi_data, events_metadata)
        
        # Save results
        logger.info("Saving results...")
        save_event_averages(event_averages, "data/processed/mean_bold_intermediate.npy")
        
        logger.info("T021 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        log_error("E001", str(e))
        logger.error(f"Input file missing: {e}")
        return 1
    except ValueError as e:
        log_error("E002", str(e))
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        log_error("E999", str(e))
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())