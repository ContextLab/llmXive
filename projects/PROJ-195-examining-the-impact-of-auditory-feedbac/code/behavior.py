import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd
import numpy as np
from scipy import stats

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging for the behavior analysis module."""
    logger = logging.getLogger("behavior_analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(file_handler)
    return logger

def load_valid_subjects(subjects_file: Path) -> List[str]:
    """Load the list of valid subjects from the exclusion file."""
    if not subjects_file.exists():
        raise FileNotFoundError(f"Valid subjects file not found: {subjects_file}")
    with open(subjects_file, 'r') as f:
        subjects = [line.strip() for line in f if line.strip()]
    return subjects

def find_event_tsv(subject_dir: Path) -> Path:
    """Locate the events.tsv file for a given subject directory."""
    # Standard BIDS location for events
    events_path = subject_dir / "events.tsv"
    if events_path.exists():
        return events_path
    
    # Check inside func directory
    func_dir = subject_dir / "func"
    if func_dir.exists():
        for f in func_dir.glob("*.events.tsv"):
            return f
        # Fallback to any events.tsv in func
        events_files = list(func_dir.glob("*events*.tsv"))
        if events_files:
            return events_files[0]
    
    raise FileNotFoundError(f"Events file not found in {subject_dir}")

def extract_trial_rts(events_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Extract reaction times (RT) from events dataframe.
    
    Assumes standard motor learning task columns: 'trial_type', 'onset', 'duration', 'response'.
    If 'response' column is missing, attempts to calculate RT as onset + duration - trial_start
    or looks for 'rt' column.
    """
    # Filter for valid trials (exclude misses if 'response' exists and is 0 or NaN)
    df = events_df.copy()
    
    # Ensure we have a trial index
    if 'trial' not in df.columns:
        df['trial'] = range(1, len(df) + 1)
    
    # Handle reaction time extraction
    if 'response' in df.columns:
        # 'response' might be 1 (hit) or 0 (miss) or actual RT
        # Check if response values are small integers (binary) or floats (RT)
        unique_vals = df['response'].unique()
        if all(isinstance(v, (int, float)) and (v == 0 or v == 1) for v in unique_vals if pd.notna(v)):
            # Binary response - need to find actual RT column
            if 'rt' in df.columns:
                df['rt'] = df['rt']
            elif 'response_time' in df.columns:
                df['rt'] = df['response_time']
            else:
                # Cannot extract RT without proper column
                logger.warning("Binary responses found but no RT column. Using onset as proxy.")
                df['rt'] = df['onset']
        else:
            # Response is already RT
            df['rt'] = df['response']
    elif 'rt' in df.columns:
        df['rt'] = df['rt']
    elif 'response_time' in df.columns:
        df['rt'] = df['response_time']
    else:
        # Fallback: use duration or onset
        logger.warning("No RT column found. Using 'duration' as RT proxy.")
        df['rt'] = df['duration'] if 'duration' in df.columns else df['onset']
    
    # Filter out invalid trials (NaN RT, negative RT, or extremely long RT > 5000ms)
    valid_mask = (
        df['rt'].notna() & 
        (df['rt'] >= 0) & 
        (df['rt'] <= 5000)
    )
    df = df[valid_mask].copy()
    
    logger.info(f"Extracted {len(df)} valid trials from {len(events_df)} total events")
    return df

def calculate_learning_rate_slope(rt_df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> Tuple[float, float, Dict[str, Any]]:
    """
    Calculate global learning rate proxy using Ordinary Least Squares (OLS) regression.
    
    Regresses mean RT (ms) against trial index to derive the slope.
    This implements the global learning rate as independent of condition (per T011 amendment).
    
    Args:
        rt_df: DataFrame with 'trial' and 'rt' columns
        logger: Optional logger instance
        
    Returns:
        Tuple of (slope, intercept, stats_dict)
        slope: Learning rate proxy (ms per trial)
        intercept: Initial performance level
        stats_dict: Dictionary with r_value, p_value, std_err, r_squared
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if rt_df.empty:
        raise ValueError("Cannot calculate slope from empty dataframe")
    
    # Sort by trial index to ensure correct order
    df = rt_df.sort_values('trial').reset_index(drop=True)
    
    # Extract trial index (1-based) and RT
    x = df['trial'].values.astype(float)
    y = df['rt'].values.astype(float)
    
    # Perform OLS regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    stats_dict = {
        'r_value': float(r_value),
        'p_value': float(p_value),
        'std_err': float(std_err),
        'r_squared': float(r_value ** 2),
        'n_trials': len(df),
        'mean_rt': float(y.mean()),
        'std_rt': float(y.std())
    }
    
    logger.info(f"Learning rate slope: {slope:.4f} ms/trial (p={p_value:.4f}, R²={r_value**2:.4f})")
    return slope, intercept, stats_dict

def process_subject_behavior(subject_dir: Path, output_csv: Path, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Process behavior data for a single subject.
    
    Args:
        subject_dir: Path to subject's BIDS directory
        output_csv: Path to save the subject's learning rate results
        logger: Logger instance
        
    Returns:
        Dictionary with slope and stats, or None if processing fails
    """
    try:
        # Find and load events
        events_path = find_event_tsv(subject_dir)
        events_df = pd.read_csv(events_path, sep='\t')
        
        # Extract RTs
        rt_df = extract_trial_rts(events_df, logger)
        
        if rt_df.empty:
            logger.warning(f"No valid RT trials found for {subject_dir.name}")
            return None
        
        # Calculate slope
        slope, intercept, stats_dict = calculate_learning_rate_slope(rt_df, logger)
        
        # Prepare result
        result = {
            'subject': subject_dir.name,
            'slope': slope,
            'intercept': intercept,
            **stats_dict
        }
        
        # Save to CSV
        result_df = pd.DataFrame([result])
        result_df.to_csv(output_csv, index=False)
        
        logger.info(f"Saved learning rate for {subject_dir.name}: slope={slope:.4f}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to process behavior for {subject_dir.name}: {e}")
        return None

def main():
    """
    Main entry point for global learning rate calculation.
    
    Processes all valid subjects, calculates OLS regression slope for each,
    and saves results to data/processed/learning_rate_slopes.csv.
    """
    logger = setup_logging()
    logger.info("Starting global learning rate proxy calculation")
    
    # Define paths
    subjects_file = PROJECT_ROOT / "data" / "processed" / "valid_subjects.txt"
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_csv = output_dir / "learning_rate_slopes.csv"
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load valid subjects
    valid_subjects = load_valid_subjects(subjects_file)
    logger.info(f"Found {len(valid_subjects)} valid subjects")
    
    # Process each subject
    all_results = []
    for subj_id in valid_subjects:
        subject_dir = PROJECT_ROOT / "data" / "raw" / "ds000246" / subj_id
        if not subject_dir.exists():
            logger.warning(f"Subject directory not found: {subject_dir}")
            continue
        
        # Temporary file for this subject
        temp_csv = output_dir / f"{subj_id}_slope.csv"
        
        result = process_subject_behavior(subject_dir, temp_csv, logger)
        if result:
            all_results.append(result)
        
        # Clean up temp file
        if temp_csv.exists():
            os.remove(temp_csv)
    
    # Combine all results
    if all_results:
        combined_df = pd.DataFrame(all_results)
        combined_df.to_csv(output_csv, index=False)
        logger.info(f"Saved combined learning rate slopes to {output_csv}")
        logger.info(f"Processed {len(all_results)} subjects successfully")
    else:
        logger.error("No subjects were successfully processed")
        sys.exit(1)
    
    logger.info("Global learning rate calculation complete")

if __name__ == "__main__":
    main()
