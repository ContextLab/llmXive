import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

def ensure_directories():
    """Ensure output directories exist."""
    output_dirs = [
        Path("data/processed"),
        Path("data/raw")
    ]
    for dir_path in output_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured directory exists: {dir_path}")

def load_scored_dialogues():
    """
    Load the scored dialogues from the previous step (T020).
    Expected path: data/processed/scored_dialogues.parquet
    """
    input_path = Path("data/processed/scored_dialogues.parquet")
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T020 (Politeness Scoring) has completed successfully."
        )
    
    logging.info(f"Loading scored dialogues from {input_path}")
    df = pd.read_parquet(input_path)
    logging.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def load_exclusions_log():
    """
    Load the exclusions log generated during filtering (T019).
    Expected path: data/raw/exclusions.log
    Returns a list of log lines or empty list if file doesn't exist.
    """
    log_path = Path("data/raw/exclusions.log")
    if not log_path.exists():
        logging.warning(f"Exclusions log not found at {log_path}. Creating empty log.")
        return []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    logging.info(f"Loaded {len(lines)} lines from exclusions log")
    return lines

def save_final_scored_data(df: pd.DataFrame):
    """
    Save the final processed scored dialogues to the canonical output path.
    Path: data/processed/scored_dialogues.parquet
    """
    output_path = Path("data/processed/scored_dialogues.parquet")
    logging.info(f"Saving final scored dialogues to {output_path}")
    df.to_parquet(output_path, index=False)
    logging.info(f"Successfully saved {len(df)} rows to {output_path}")
    return output_path

def save_final_exclusions_log(log_lines: List[str]):
    """
    Save the final exclusions log to the canonical output path.
    Path: data/raw/exclusions.log
    """
    output_path = Path("data/raw/exclusions.log")
    logging.info(f"Saving final exclusions log to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)
    logging.info(f"Successfully saved {len(log_lines)} lines to {output_path}")
    return output_path

def main():
    """
    Main entry point for T021: Save processed data to data/processed/scored_dialogues.parquet
    and raw logs to data/raw/exclusions.log.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/t021_save_artifacts.log', mode='a')
        ]
    )

    logging.info("Starting T021: Save Final Artifacts")

    try:
        # 1. Ensure directories exist
        ensure_directories()

        # 2. Load scored dialogues (output of T020)
        # Note: T020 already saves to this path, but we reload to ensure
        # we are saving the final artifact in this step as per task definition.
        # If T020 failed to write, this will raise FileNotFoundError.
        df_scored = load_scored_dialogues()

        # 3. Load exclusions log (output of T019)
        log_lines = load_exclusions_log()

        # 4. Save final artifacts
        # Re-save the dataframe to ensure it's the final version
        save_final_scored_data(df_scored)

        # Re-save the log to ensure it's the final version
        save_final_exclusions_log(log_lines)

        logging.info("T021 completed successfully.")
        return 0

    except FileNotFoundError as e:
        logging.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during T021: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
