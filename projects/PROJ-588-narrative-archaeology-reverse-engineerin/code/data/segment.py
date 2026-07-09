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
    Expected columns: onset, duration, trial_type, label.
    """
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Annotation file not found: {csv_path}")
    return pd.read_csv(csv_path)

def align_events_to_bold(events_df, tr=config.TR if hasattr(config, 'TR') else 2.0):
    """
    Align event onsets to BOLD timepoints.
    """
    # Convert onsets to indices
    events_df['frame'] = (events_df['onset'] / tr).astype(int)
    return events_df

def segment_timecourse(timecourse, events_df):
    """
    Extract timecourse segments around events.
    """
    segments = []
    for _, row in events_df.iterrows():
        start = row['frame']
        end = start + int(row['duration'] / config.TR) + 4 # +4 for HRF lag
        segment = timecourse[start:end]
        if len(segment) > 0:
            segments.append(segment)
    return np.array(segments)
