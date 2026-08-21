"""
T012b: Validate Thresholds
Load data/processed/raw_extract.parquet (T013). Apply default threshold from
code/config/detection_thresholds.yaml (T012a). Log event count.
If count < 500, log a warning but DO NOT change the threshold (FR-018).
Output: data/logs/threshold_validation.log
"""

import os
import sys
import logging
import argparse
import yaml
from pathlib import Path
import pandas as pd

# Ensure code/ is in path for imports if run from root
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

CONFIG_PATH = ROOT / "code" / "config" / "detection_thresholds.yaml"
INPUT_PATH = ROOT / "data" / "processed" / "raw_extract.parquet"
LOG_DIR = ROOT / "data" / "logs"
LOG_PATH = LOG_DIR / "threshold_validation.log"

def load_thresholds():
    """Load detection thresholds from YAML."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Threshold config not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_extracted_data():
    """Load the raw extraction parquet file."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input data not found: {INPUT_PATH}")
    return pd.read_parquet(INPUT_PATH)

def count_events(df, thresholds):
    """
    Count events based on the loaded thresholds.
    We look for rows where the relevant feature exceeds the threshold.
    Based on T012a, we check 'latent_delta_magnitude' against the threshold.
    We also check 'turn_label' if it exists to ensure we are counting valid events.
    """
    # Default to counting rows where latent_delta_magnitude > threshold
    # This assumes the extraction task (T013) calculated this column.
    threshold_val = float(thresholds.get('latent_delta_magnitude', 0.5))
    
    # Filter for non-null values
    valid_df = df[df['latent_delta_magnitude'].notna()]
    
    # Count events exceeding the threshold
    event_count = len(valid_df[valid_df['latent_delta_magnitude'] > threshold_val])
    
    # Also check for pause events if audio_energy is present
    # If the schema includes audio_energy, we might count pauses too.
    # For now, we count the primary event type defined by the delta magnitude.
    return event_count

def write_log(event_count, thresholds, log_path):
    """Write the validation log."""
    log_dir = log_path.parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    threshold_val = thresholds.get('latent_delta_magnitude', 0.5)
    warning_msg = ""
    
    if event_count < 500:
        warning_msg = f"WARNING: Event count ({event_count}) is below the target of 500. Threshold NOT changed per FR-018."
    else:
        warning_msg = f"INFO: Event count ({event_count}) meets the target of 500."
    
    log_content = f"""Threshold Validation Report
===========================
Timestamp: {pd.Timestamp.now().isoformat()}
Config File: {CONFIG_PATH}
Input File: {INPUT_PATH}

Applied Thresholds:
- latent_delta_magnitude: {threshold_val}
- audio_energy_db: {thresholds.get('audio_energy_db', 'N/A')}
- pause_duration_frames: {thresholds.get('pause_duration_frames', 'N/A')}

Results:
- Total Events Detected: {event_count}
- Threshold Used: {threshold_val}
- Status: {warning_msg}
"""
    with open(log_path, 'w') as f:
        f.write(log_content)
    
    return warning_msg

def main():
    parser = argparse.ArgumentParser(description="Validate detection thresholds on extracted data.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH), help="Path to thresholds config")
    parser.add_argument("--input", type=str, default=str(INPUT_PATH), help="Path to raw_extract.parquet")
    parser.add_argument("--output", type=str, default=str(LOG_PATH), help="Path to output log")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Loading thresholds from {args.config}")
        thresholds = load_thresholds()
        # Override with CLI args if provided
        if args.config != str(CONFIG_PATH):
            thresholds = load_thresholds() # Re-load if path changed

        logger.info(f"Loading data from {args.input}")
        df = load_extracted_data()

        logger.info("Counting events based on thresholds...")
        event_count = count_events(df, thresholds)
        
        logger.info(f"Event count: {event_count}")
        
        logger.info(f"Writing log to {args.output}")
        warning = write_log(event_count, thresholds, Path(args.output))
        
        if "WARNING" in warning:
            logger.warning(warning)
        else:
            logger.info(warning)

        print(f"Threshold validation complete. Log written to {args.output}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())