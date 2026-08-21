"""
T012b: Validate Thresholds & Event Count

Loads data/processed/raw_extract.parquet, applies thresholds from
code/config/detection_thresholds.yaml, computes total event count,
and writes data/logs/threshold_validation.log.

Exits with code 0 if event count >= 500.
Exits with code 1 if event count < 500 (after logging error).
"""
import os
import sys
import argparse
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
THRESHOLD_CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "detection_thresholds.yaml"
INPUT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "raw_extract.parquet"
OUTPUT_LOG_PATH = PROJECT_ROOT / "data" / "logs" / "threshold_validation.log"

def load_thresholds(config_path: Path) -> dict:
    """Load detection thresholds from YAML config."""
    if not config_path.exists():
        raise FileNotFoundError(f"Threshold config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_extracted_data(data_path: Path) -> pd.DataFrame:
    """Load the extracted parquet data."""
    if not data_path.exists():
        raise FileNotFoundError(f"Input data not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded data with {len(df)} rows.")
    return df

def count_events(df: pd.DataFrame, thresholds: dict) -> int:
    """
    Count events based on thresholds.
    
    Events are defined as:
    1. Pause: Sequence of frames where audio_energy < audio_energy_db for 
       at least pause_duration_frames.
    2. Interruption: Frame where latent_delta_magnitude > threshold AND 
       audio_energy >= audio_energy_db (active speech).
    
    Returns total count of detected events (pauses + interruptions).
    """
    audio_energy_threshold = thresholds.get('audio_energy_db', -30.0)
    latent_delta_threshold = thresholds.get('latent_delta_magnitude', 0.5)
    pause_duration = thresholds.get('pause_duration_frames', 10)
    
    if 'audio_energy' not in df.columns or 'latent_delta_magnitude' not in df.columns:
        raise ValueError("Input data missing required columns: 'audio_energy' and/or 'latent_delta_magnitude'")
    
    # Count Interruptions
    # Condition: latent_delta_magnitude > threshold AND audio_energy >= threshold (active speech)
    interruption_mask = (
        (df['latent_delta_magnitude'] > latent_delta_threshold) & 
        (df['audio_energy'] >= audio_energy_threshold)
    )
    interruption_count = interruption_mask.sum()
    logger.info(f"Detected {interruption_count} interruption events.")
    
    # Count Pauses
    # Condition: Consecutive frames where audio_energy < threshold for at least 'pause_duration' frames
    # We mark frames below threshold, then find runs of True values of length >= pause_duration
    silence_mask = df['audio_energy'] < audio_energy_threshold
    
    # Identify runs of silence
    # Change detection to find run boundaries
    silence_change = silence_mask.astype(int).diff().fillna(0)
    start_indices = silence_change[silence_change == 1].index
    end_indices = silence_change[silence_change == -1].index
    
    # Handle edge cases: if silence starts at 0 or ends at end
    if silence_mask.iloc[0]:
        start_indices = pd.concat([pd.Series([0]), start_indices])
    if silence_mask.iloc[-1]:
        end_indices = pd.concat([end_indices, pd.Series([len(df) - 1])])
    
    pause_count = 0
    for start, end in zip(start_indices, end_indices):
        run_length = end - start + 1
        if run_length >= pause_duration:
            pause_count += 1
    
    logger.info(f"Detected {pause_count} pause events.")
    
    total_events = interruption_count + pause_count
    logger.info(f"Total event count: {total_events}")
    
    return total_events

def write_log(log_path: Path, event_count: int, success: bool, error_msg: str = None):
    """Write the validation log file."""
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"Event count: {event_count}\n")
        if error_msg:
            f.write(f"{error_msg}\n")
        f.write(f"Validation status: {'PASS' if success else 'FAIL'}\n")
    
    logger.info(f"Log written to {log_path}")

def main():
    parser = argparse.ArgumentParser(description="Validate thresholds and count events.")
    parser.add_argument(
        "--config", 
        type=str, 
        default=str(THRESHOLD_CONFIG_PATH),
        help="Path to detection thresholds YAML config."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=str(INPUT_DATA_PATH),
        help="Path to input parquet file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(OUTPUT_LOG_PATH),
        help="Path to output log file."
    )
    parser.add_argument(
        "--min-events", 
        type=int, 
        default=500,
        help="Minimum required event count."
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    input_path = Path(args.input)
    output_path = Path(args.output)
    min_events = args.min_events
    
    try:
        # Load thresholds
        logger.info(f"Loading thresholds from {config_path}...")
        thresholds = load_thresholds(config_path)
        
        # Load data
        logger.info(f"Loading data from {input_path}...")
        df = load_extracted_data(input_path)
        
        # Count events
        event_count = count_events(df, thresholds)
        
        # Check against minimum
        if event_count < min_events:
            error_msg = f"ERROR: insufficient events ({event_count})"
            logger.error(error_msg)
            write_log(output_path, event_count, success=False, error_msg=error_msg)
            logger.info("Exiting with code 1 due to insufficient events.")
            sys.exit(1)
        else:
            logger.info(f"Event count ({event_count}) meets minimum requirement ({min_events}).")
            write_log(output_path, event_count, success=True)
            logger.info("Exiting with code 0.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        # Write a failure log even on file missing to be explicit
        write_log(output_path, 0, success=False, error_msg=f"ERROR: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        write_log(output_path, 0, success=False, error_msg=f"ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
