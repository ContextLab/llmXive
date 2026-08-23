import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils import get_logger, write_csv, read_json, write_json, ensure_directories
from src.config import get_processed_data_dir, get_data_root, get_state_root

logger = get_logger(__name__)

# Constants
TARGET_CLIPS = 10000
SECONDS_PER_HOUR = 3600

def load_scaling_profile() -> pd.DataFrame:
    """
    Loads the scaling validation data from state.
    Expected file: state/scaling_validation.json
    Returns a DataFrame with columns: [clip_index, cpu_time_sec]
    """
    state_root = get_state_root()
    profile_path = state_root / "scaling_validation.json"
    
    if not profile_path.exists():
        raise FileNotFoundError(f"Scaling profile not found at {profile_path}. Run T021b first.")
    
    with open(profile_path, 'r') as f:
        data = json.load(f)
    
    # Ensure it's a list of dicts
    if isinstance(data, list):
        df = pd.DataFrame(data)
        # Expecting 'clip_index' and 'cpu_time_sec' based on T021b description
        if 'clip_index' not in df.columns or 'cpu_time_sec' not in df.columns:
            # Fallback if schema is slightly different, try to map common names
            if 'index' in df.columns: df['clip_index'] = df['index']
            if 'time' in df.columns: df['cpu_time_sec'] = df['time']
        
        return df
    else:
        raise ValueError(f"Scaling profile at {profile_path} is not a valid list.")

def calculate_inference_time_projection(sample_size: int, mean_time_per_clip: float) -> float:
    """
    Calculates the projected total hours for N=10,000 clips based on sample data.
    
    Formula: projected_total_hours = (mean_time_per_clip_sec * [sample_size]) / 3600
    Note: The task description formula seems slightly ambiguous regarding 'sample_size'
    vs 'TARGET_CLIPS'. The standard projection is:
    Total_Time = Mean_Time_Per_Clip * Target_Clip_Count
    
    However, adhering strictly to the task text:
    'projected_total_hours = (mean_time_per_clip_sec * [sample_size]) / 3600'
    Usually, [sample_size] in this context implies the target N (10,000) to project TO,
    OR it implies calculating the total time of the sample and scaling.
    
    Re-reading: "project total time for N=10,000 clips... Formula: ... * [sample_size] ..."
    This likely means: Projected Hours = (Mean Time * 10000) / 3600.
    The variable name [sample_size] in the formula description is likely a placeholder for the target N.
    
    Implementation:
    1. Calculate mean_time_per_clip from input.
    2. Multiply by TARGET_CLIPS (10000).
    3. Divide by 3600.
    4. Round to 2 decimal places.
    """
    target_n = TARGET_CLIPS
    total_seconds = mean_time_per_clip * target_n
    total_hours = total_seconds / SECONDS_PER_HOUR
    return round(total_hours, 2)

def generate_timing_profile() -> str:
    """
    Implements T024: Calculate per-clip inference time and project total time.
    Reads scaling profile (T021b), calculates mean time, projects to 10k clips.
    Writes: data/timing_profile.csv
    
    Returns the path to the output file.
    """
    try:
        # 1. Load scaling validation data (output of T021b)
        # T021b validates linearity and produces a JSON with clip_index vs cpu_time_sec
        df_scaling = load_scaling_profile()
        
        if df_scaling.empty:
            raise ValueError("Scaling profile is empty. Cannot calculate mean time.")
        
        # 2. Calculate mean time per clip
        # Ensure the column name is correct
        time_col = 'cpu_time_sec'
        if time_col not in df_scaling.columns:
            # Try to find a time column
            time_candidates = [c for c in df_scaling.columns if 'time' in c.lower() and 'sec' in c.lower()]
            if not time_candidates:
                raise ValueError(f"Could not find time column in scaling profile. Columns: {df_scaling.columns.tolist()}")
            time_col = time_candidates[0]
        
        mean_time_per_clip = df_scaling[time_col].mean()
        
        if pd.isna(mean_time_per_clip) or mean_time_per_clip <= 0:
            raise ValueError(f"Invalid mean time calculated: {mean_time_per_clip}")
        
        # 3. Project total time for N=10,000
        projected_hours = calculate_inference_time_projection(len(df_scaling), mean_time_per_clip)
        
        # 4. Prepare output
        output_dir = get_data_root()
        output_path = output_dir / "timing_profile.csv"
        ensure_directories([output_dir])
        
        data = {
            "mean_time_per_clip_sec": round(mean_time_per_clip, 4),
            "projected_total_hours": projected_hours
        }
        
        df_out = pd.DataFrame([data])
        df_out.to_csv(output_path, index=False)
        
        logger.info(f"Timing profile generated: {output_path}")
        logger.info(f"Mean time per clip: {mean_time_per_clip:.4f}s")
        logger.info(f"Projected time for 10k clips: {projected_hours:.2f} hours")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error generating timing profile: {e}", exc_info=True)
        raise

def main():
    """Entry point for T024 execution."""
    logger.info("Starting T024: Timing Profile Generation")
    try:
        output_path = generate_timing_profile()
        logger.info(f"T024 completed successfully. Output: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"T024 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
