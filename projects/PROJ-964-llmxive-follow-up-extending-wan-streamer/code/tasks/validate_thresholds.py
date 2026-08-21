"""
T012b: Validate Thresholds & Event Count

Loads `data/processed/raw_extract.parquet` (produced by T013), applies thresholds
from `code/config/detection_thresholds.yaml`, computes the total event count,
and writes `data/logs/threshold_validation.log` containing the line
`Event count: <number>`.

If count < 500, this script invokes the logic from T012c (dynamic threshold
adjustment) to lower the `audio_energy_db` threshold by 2dB steps (min floor 5dB)
and re-runs the event counting until 500 events are found or the floor is hit.
If the floor is hit and count < 500, it logs the failure and exits with code 1.

Verification: Asserts the log file exists, contains the exact count line,
and that the task exits with code 0 only when count >= 500.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import yaml

# Import from sibling modules as per API surface
# We need to access the data processing logic. Since T013 produced the file,
# we assume it exists. We need to count events based on thresholds.
# The task description says "apply thresholds... compute total event count".
# We will implement the counting logic here to ensure we don't rely on
# potentially incomplete external functions for this specific validation step.

# Constants
MIN_EVENTS = 500
MIN_THRESHOLD_DB = 5.0
THRESHOLD_STEP_DB = 2.0
LOG_FILE_PATH = Path("data/logs/threshold_validation.log")
THRESHOLD_CONFIG_PATH = Path("code/config/detection_thresholds.yaml")
INPUT_DATA_PATH = Path("data/processed/raw_extract.parquet")
STATE_YAML_PATH = Path("state.yaml")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_thresholds(config_path: Path) -> Dict[str, Any]:
    """Load detection thresholds from YAML config."""
    if not config_path.exists():
        raise FileNotFoundError(f"Threshold config not found at {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_extracted_data(data_path: Path) -> pd.DataFrame:
    """Load the extracted parquet data."""
    if not data_path.exists():
        raise FileNotFoundError(f"Extracted data not found at {data_path}. "
                                "Please ensure T013 (extract_latents.py) has run successfully.")
    try:
        df = pd.read_parquet(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise


def count_events(df: pd.DataFrame, thresholds: Dict[str, Any]) -> int:
    """
    Count events based on thresholds.
    Logic derived from T012a:
    1. Pause: consecutive frames with audio_energy < audio_energy_db for pause_duration_frames.
    2. Interruption: latent_delta_magnitude > threshold AND audio_energy > audio_energy_db.
    
    Note: The task description focuses on "Event count". We count both pauses and interruptions.
    """
    audio_energy_thresh = thresholds["audio_energy_db"]
    latent_delta_thresh = thresholds["latent_delta_magnitude"]
    pause_duration = thresholds["pause_duration_frames"]

    # Ensure columns exist
    required_cols = ["audio_energy", "latent_delta_magnitude"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")

    count = 0

    # 1. Count Interruptions
    # Condition: latent_delta_magnitude > threshold AND audio_energy > threshold (active speech)
    # Note: The spec says "audio energy indicates active speech (above audio_energy_db)".
    # Since audio_energy_db is negative (e.g., -30), "above" means > -30.
    interruption_mask = (
        (df["latent_delta_magnitude"] > latent_delta_thresh) &
        (df["audio_energy"] > audio_energy_thresh)
    )
    count += interruption_mask.sum()
    logger.debug(f"Interruption events found: {interruption_mask.sum()}")

    # 2. Count Pauses
    # Condition: consecutive frames with audio_energy < audio_energy_db for >= pause_duration_frames
    # We need to find runs of silence.
    silence_mask = df["audio_energy"] < audio_energy_thresh
    silence_series = silence_mask.astype(int)
    
    # Find runs of 1s
    # A run of length L >= pause_duration counts as 1 pause event (or we count the number of such segments)
    # Usually, a "pause event" is the segment itself.
    # Let's count the number of distinct segments that meet the duration criteria.
    if silence_series.sum() > 0:
        # Diff to find start and end of runs
        diff = silence_series.diff().fillna(0)
        starts = (diff == 1).to_numpy()
        ends = (diff == -1).to_numpy()
        
        # Handle edge cases for start/end of array
        if silence_series.iloc[0]:
            starts[0] = True
        if silence_series.iloc[-1]:
            ends[-1] = True

        start_indices = np.where(starts)[0]
        end_indices = np.where(ends)[0]

        # Pair starts and ends
        # If there are more starts than ends (ends at array), adjust
        if len(start_indices) > len(end_indices):
            # Last run goes to end of array
            # This logic is slightly complex for simple counting, let's use a simpler approach
            # Group by cumsum of changes
            import numpy as np
            # Re-implementation using groupby for runs
            silence_series_np = silence_series.to_numpy()
            if len(silence_series_np) == 0:
                pause_count = 0
            else:
                # Create groups of consecutive values
                groups = (silence_series_np[:-1] != silence_series_np[1:]).cumsum()
                groups = np.concatenate([[0], groups]) # align with original length? No, length-1
                # Actually, simpler:
                # Use pandas groupby on change points
                df_temp = pd.DataFrame({"val": silence_series_np})
                df_temp["group"] = (df_temp["val"].diff() != 0).cumsum()
                pause_runs = df_temp[df_temp["val"] == 1].groupby("group").size()
                pause_count = (pause_runs >= pause_duration).sum()
        
        count += pause_count
        logger.debug(f"Pause events found: {pause_count}")

    return int(count)


def adjust_threshold_and_retry(df: pd.DataFrame, initial_thresholds: Dict[str, Any]) -> Tuple[int, Dict[str, Any], bool]:
    """
    T012c Logic: Adjust threshold if count < 500.
    Lower audio_energy_db by 2dB steps (min floor 5dB).
    Returns (final_count, final_thresholds, success).
    """
    current_thresholds = initial_thresholds.copy()
    current_db = current_thresholds["audio_energy_db"]
    current_count = count_events(df, current_thresholds)

    logger.info(f"Initial count with threshold {current_db} dB: {current_count}")

    if current_count >= MIN_EVENTS:
        return current_count, current_thresholds, True

    while current_db > MIN_THRESHOLD_DB:
        current_db -= THRESHOLD_STEP_DB
        if current_db < MIN_THRESHOLD_DB:
            current_db = MIN_THRESHOLD_DB # Floor
        
        current_thresholds["audio_energy_db"] = current_db
        current_count = count_events(df, current_thresholds)
        logger.info(f"Adjusted threshold to {current_db} dB. New count: {current_count}")

        if current_count >= MIN_EVENTS:
            return current_count, current_thresholds, True

    # If we hit the floor and still don't have enough
    logger.warning(f"Reached minimum threshold floor ({MIN_THRESHOLD_DB} dB) but event count ({current_count}) is still below {MIN_EVENTS}.")
    return current_count, current_thresholds, False


def write_log(count: int, threshold_used: float, success: bool, log_path: Path):
    """Write the validation log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"Event count: {count}\n")
        f.write(f"Threshold used: {threshold_used} dB\n")
        f.write(f"Success: {success}\n")
        if not success:
            f.write(f"Reason: Event count below minimum ({MIN_EVENTS}) even with lowest threshold.\n")
    logger.info(f"Log written to {log_path}")


def update_config_with_calibration(thresholds: Dict[str, Any], config_path: Path):
    """Update the config file with calibration results."""
    import datetime
    thresholds["calibration_status"] = "completed"
    thresholds["calibration_actual_events"] = thresholds.get("calibration_actual_events", 0)
    thresholds["calibration_timestamp"] = datetime.datetime.now().isoformat()
    with open(config_path, "w") as f:
        yaml.dump(thresholds, f, default_flow_style=False)
    logger.info(f"Config updated at {config_path}")


def main():
    parser = argparse.ArgumentParser(description="T012b: Validate Thresholds & Event Count")
    parser.add_argument("--data", type=Path, default=INPUT_DATA_PATH, help="Path to raw_extract.parquet")
    parser.add_argument("--config", type=Path, default=THRESHOLD_CONFIG_PATH, help="Path to thresholds.yaml")
    parser.add_argument("--log", type=Path, default=LOG_FILE_PATH, help="Path to output log")
    args = parser.parse_args()

    try:
        # 1. Load Data
        df = load_extracted_data(args.data)

        # 2. Load Thresholds
        thresholds = load_thresholds(args.config)

        # 3. Count Events and Adjust if necessary
        count, final_thresholds, success = adjust_threshold_and_retry(df, thresholds)

        # 4. Write Log
        write_log(count, final_thresholds["audio_energy_db"], success, args.log)

        # 5. Update Config if successful (or even if failed, to record attempt)
        # We update the config to reflect the threshold that achieved the count (or the floor)
        # and the actual count found.
        final_thresholds["calibration_actual_events"] = count
        update_config_with_calibration(final_thresholds, args.config)

        if not success:
            logger.error(f"Validation failed: Event count {count} < {MIN_EVENTS}")
            sys.exit(1)

        logger.info(f"Validation passed: Event count {count} >= {MIN_EVENTS}")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
