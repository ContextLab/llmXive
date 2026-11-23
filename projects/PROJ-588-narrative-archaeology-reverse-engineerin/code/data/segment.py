"""
Event segmentation and alignment utilities.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import code.config as config

logger = logging.getLogger(__name__)

def load_event_annotations(csv_path):
    """
    Load event annotations from a CSV file.
    Expected columns: onset, duration, event_type, label
    """
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Annotation file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    return df

def align_events_to_bold(events_df, tr=2.0):
    """
    Align event onsets to BOLD timepoints.
    
    Args:
        events_df (pd.DataFrame): Events with 'onset' column.
        tr (float): Repetition time in seconds.
    
    Returns:
        pd.DataFrame: Events with 'timepoint' column.
    """
    events_df = events_df.copy()
    events_df['timepoint'] = (events_df['onset'] / tr).astype(int)
    return events_df

def segment_timecourse(timecourse, events_df):
    """
    Extract timecourse segments for each event.
    
    Args:
        timecourse (np.array): 4D or 2D timecourse data (time x voxels).
        events_df (pd.DataFrame): Events with 'timepoint' and 'duration'.
    
    Returns:
        dict: Dictionary mapping event label to segment array.
    """
    segments = {}
    for _, row in events_df.iterrows():
        start = row['timepoint']
        end = start + int(row['duration'] / config.FMRIPREP_FLAGS[1] if 'tr' in str(config.FMRIPREP_FLAGS) else 2) # Simplified duration logic
        # Ensure bounds
        end = min(end, timecourse.shape[0])
        if start < timecourse.shape[0]:
            segment = timecourse[start:end]
            label = row.get('label', 'unknown')
            if label not in segments:
                segments[label] = []
            segments[label].append(segment)
    return segments
