import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/021_save_final_artifacts.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        Path('data/processed'),
        Path('data/raw')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def load_scored_dialogues(input_path: str = 'data/processed/scored_dialogues_temp.parquet') -> pd.DataFrame:
    """
    Load the scored dialogues DataFrame.
    Note: In a real pipeline, this would load from the output of T020.
    For this task, we assume T020 has written to a temp file or the final file
    if T020 was modified to write directly. Here we handle the final save step.
    """
    path = Path(input_path)
    if not path.exists():
        # Fallback: try to load the final expected file if T020 already saved it there
        final_path = Path('data/processed/scored_dialogues.parquet')
        if final_path.exists():
            logger.warning(f"Input path {input_path} not found, loading from {final_path}")
            return pd.read_parquet(final_path)
        raise FileNotFoundError(f"Scored dialogues file not found at {input_path} or {final_path}")
    
    logger.info(f"Loading scored dialogues from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def load_exclusions_log(log_path: str = 'data/raw/exclusions.log') -> str:
    """
    Load the exclusions log content.
    """
    path = Path(log_path)
    if not path.exists():
        logger.warning(f"Exclusions log not found at {log_path}. Creating an empty log.")
        return "No exclusions logged."
    
    logger.info(f"Loading exclusions log from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def save_final_scored_data(df: pd.DataFrame, output_path: str = 'data/processed/scored_dialogues.parquet'):
    """
    Save the final processed scored dialogues to parquet.
    """
    path = Path(output_path)
    logger.info(f"Saving scored dialogues to {path}")
    df.to_parquet(path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {path}")

def save_final_exclusions_log(content: str, output_path: str = 'data/raw/exclusions.log'):
    """
    Save the final exclusions log.
    """
    path = Path(output_path)
    logger.info(f"Saving exclusions log to {path}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Successfully saved exclusions log to {path}")

def main():
    """
    Main entry point for T021: Save processed data and raw logs.
    """
    logger.info("Starting T021: Save final artifacts")
    
    try:
        # Ensure directories exist
        ensure_directories()

        # Load the scored dialogues (output from T020)
        # We assume T020 produces 'data/processed/scored_dialogues.parquet' directly
        # or a temp file. The task description says T020 produces 'scored_dialogues.parquet'.
        # So we just need to ensure it's finalized if T020 wrote to a temp location.
        # However, to be robust, we try to load the expected output from T020.
        input_path = 'data/processed/scored_dialogues.parquet'
        
        if not Path(input_path).exists():
            # If T020 hasn't run or wrote to a different temp file, this task cannot proceed.
            # We raise an error to fail loudly as per constraints.
            raise FileNotFoundError(
                f"Required input file {input_path} not found. "
                "Ensure T020 (Politeness Scoring) has completed successfully."
            )

        df = load_scored_dialogues(input_path)

        # Load exclusions log (produced by T019/T020)
        log_content = load_exclusions_log('data/raw/exclusions.log')

        # Save final artifacts
        # The task asks to save to 'data/processed/scored_dialogues.parquet'
        # Since T020 likely already did this, we re-save to ensure it's the final committed artifact
        # or if T020 wrote to a temp file, we move it here.
        # For simplicity and idempotency, we just save the loaded DF to the target path.
        save_final_scored_data(df, 'data/processed/scored_dialogues.parquet')

        # Ensure exclusions log is in the correct place
        save_final_exclusions_log(log_content, 'data/raw/exclusions.log')

        logger.info("T021 completed successfully. Artifacts saved.")
        
    except Exception as e:
        logger.error(f"T021 failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()