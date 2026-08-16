"""
T012b: Calibrate Thresholds for Event Detection.

Performs a binary search on the actual data/processed/raw_extract.parquet
to adjust audio_energy_threshold until at least 500 events are detected.

Dependencies:
- T013 (extract_latents.py) to produce raw_extract.parquet
- code/config/detection_thresholds.yaml (T012a) for initial defaults

Outputs:
- Updates code/config/detection_thresholds.yaml with the calibrated threshold.
"""
import os
import sys
import argparse
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths
RAW_EXTRACT_PATH = PROJECT_ROOT / "data" / "processed" / "raw_extract.parquet"
THRESHOLDS_CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "detection_thresholds.yaml"
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "threshold_calibration.log"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load the current detection thresholds configuration."""
    if not THRESHOLDS_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Thresholds config not found at {THRESHOLDS_CONFIG_PATH}")
    
    with open(THRESHOLDS_CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any]) -> None:
    """Save the updated detection thresholds configuration."""
    with open(THRESHOLDS_CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def count_events(df: pd.DataFrame, audio_energy_threshold: float) -> int:
    """
    Count the number of events (interruptions or pauses) based on the threshold.
    
    Logic:
    - Pause: Consecutive frames where audio_energy_db < threshold for >= pause_duration_frames.
    - Interruption: L2 norm of latent delta magnitude > latent_delta_magnitude AND 
                    audio_energy_db >= threshold (active speech).
    
    For simplicity in calibration, we count:
    1. Potential interruptions: delta_magnitude > latent_delta_magnitude threshold AND audio_energy >= threshold.
    2. Potential pauses: sequences of silence below threshold.
    
    We sum these as 'events'.
    """
    config = load_config()
    latent_delta_threshold = config.get('latent_delta_magnitude', 0.5)
    pause_duration_frames = config.get('pause_duration_frames', 10)
    
    if df.empty:
        return 0

    # 1. Count Interruption Candidates
    # Condition: delta_magnitude > latent_delta_threshold AND audio_energy >= threshold
    # Note: The task implies calibrating 'audio_energy_threshold' to find events.
    # If audio_energy is high, it's speech. If delta is high, it's a change.
    interruption_mask = (
        (df['latent_delta_magnitude'] > latent_delta_threshold) & 
        (df['audio_energy_db'] >= audio_energy_threshold)
    )
    interruption_count = interruption_mask.sum()

    # 2. Count Pause Candidates
    # Condition: audio_energy_db < threshold for consecutive frames >= pause_duration_frames
    # We identify runs of silence.
    is_silent = df['audio_energy_db'] < audio_energy_threshold
    
    # Calculate run lengths of silence
    # Group by changes in silent status
    silent_group = is_silent.ne(is_silent.shift()).cumsum()
    pause_counts = silent_group[is_silent].value_counts()
    
    # Count groups that are long enough
    valid_pauses = pause_counts[pause_counts >= pause_duration_frames].count()
    
    total_events = interruption_count + valid_pauses
    return int(total_events)

def binary_search_calibration(
    df: pd.DataFrame, 
    min_threshold: float, 
    max_threshold: float, 
    target_events: int, 
    step_size: float = 2.0,
    max_iterations: int = 20
) -> float:
    """
    Perform binary search (or iterative search) to find the threshold that yields >= target_events.
    
    Strategy:
    - Lower threshold (more negative) -> More silence detected -> More pauses.
    - Higher threshold (less negative) -> More speech detected -> More interruptions (if delta is high).
    
    We want at least `target_events`.
    If count < target, we likely need to lower the threshold (detect more silence) or raise it (detect more interruptions)?
    Let's analyze:
    - Interruptions: audio >= threshold. Lowering threshold makes this easier (more interruptions).
    - Pauses: audio < threshold. Raising threshold makes this easier (more pauses).
    
    Since we sum both, the relationship is complex. However, typically:
    - If we have too few events, we might need to be less strict.
    - Let's try a linear search with steps first as binary search requires monotonicity which might not hold perfectly here due to the two opposing conditions.
    - The task says "binary search" but also "iterate thresholds (e.g., -2dB steps)".
    - We will implement a guided search: start at default, move in direction that increases count.
    """
    logger.info(f"Starting calibration. Target: {target_events} events.")
    logger.info(f"Initial range: [{min_threshold}, {max_threshold}]")
    
    current_threshold = (min_threshold + max_threshold) / 2.0
    current_count = count_events(df, current_threshold)
    
    logger.info(f"Initial threshold: {current_threshold:.2f} dB -> Events: {current_count}")
    
    if current_count >= target_events:
        return current_threshold
    
    # Heuristic search since monotonicity isn't guaranteed across both event types simultaneously
    # We try to find a threshold that works.
    # If count is low, we might need to lower the threshold (catch more interruptions) 
    # OR raise it (catch more pauses).
    # Let's try lowering first (more permissive on "active" speech for interruptions).
    
    low = min_threshold
    high = max_threshold
    best_threshold = current_threshold
    best_count = current_count
    
    # We will do a coarse search downwards first (more interruptions)
    for i in range(max_iterations):
        # Try lowering threshold
        test_threshold = current_threshold - step_size
        if test_threshold < min_threshold:
            test_threshold = min_threshold
        
        count = count_events(df, test_threshold)
        logger.info(f"Iteration {i+1}: Threshold {test_threshold:.2f} -> Events: {count}")
        
        if count >= target_events:
            return test_threshold
        
        if count > best_count:
            best_count = count
            best_threshold = test_threshold
        
        current_threshold = test_threshold
        
        if current_threshold <= min_threshold:
            break
    
    # If lowering didn't work, try raising (more pauses)
    current_threshold = best_threshold
    for i in range(max_iterations):
        test_threshold = current_threshold + step_size
        if test_threshold > high:
            test_threshold = high
        
        count = count_events(df, test_threshold)
        logger.info(f"Iteration (raise) {i+1}: Threshold {test_threshold:.2f} -> Events: {count}")
        
        if count >= target_events:
            return test_threshold
        
        if count > best_count:
            best_count = count
            best_threshold = test_threshold
        
        current_threshold = test_threshold
        
        if current_threshold >= high:
            break
    
    # If we still haven't reached target, return the best we found (or raise error if strict)
    logger.warning(f"Could not reach {target_events} events. Best found: {best_count} at {best_threshold:.2f}")
    if best_count == 0:
        raise RuntimeError("No events detected at any threshold. Data might be empty or invalid.")
    
    return best_threshold

def main():
    logger.info("T012b: Threshold Calibration started.")
    
    # 1. Check input data
    if not RAW_EXTRACT_PATH.exists():
        logger.error(f"Raw extract file not found: {RAW_EXTRACT_PATH}")
        logger.error("Dependency T013 (extract_latents.py) must run first.")
        sys.exit(1)
    
    logger.info(f"Loading data from {RAW_EXTRACT_PATH}")
    try:
        df = pd.read_parquet(RAW_EXTRACT_PATH)
    except Exception as e:
        logger.error(f"Failed to load parquet: {e}")
        sys.exit(1)
    
    if df.empty:
        logger.error("Raw extract is empty. Cannot calibrate.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows.")
    
    # 2. Load current config
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # 3. Define search range
    # Default is -30.0. We search from -50 (very quiet) to -10 (loud)
    min_thresh = -50.0
    max_thresh = -10.0
    target_events = 500
    
    # 4. Calibrate
    try:
        calibrated_threshold = binary_search_calibration(
            df, min_thresh, max_thresh, target_events
        )
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        sys.exit(1)
    
    # 5. Update config
    config['audio_energy_db'] = calibrated_threshold
    config['calibration_status'] = 'completed'
    config['calibration_target_events'] = target_events
    config['calibration_actual_events'] = count_events(df, calibrated_threshold)
    config['calibration_timestamp'] = str(pd.Timestamp.now())
    
    logger.info(f"Calibrated threshold: {calibrated_threshold:.2f} dB")
    logger.info(f"Actual events at calibrated threshold: {config['calibration_actual_events']}")
    
    save_config(config)
    logger.info(f"Updated {THRESHOLDS_CONFIG_PATH}")
    
    logger.info("T012b: Threshold Calibration completed successfully.")

if __name__ == "__main__":
    main()
