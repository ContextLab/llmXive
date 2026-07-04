"""
T009a: Data Acquisition Module for US1.

Fetches raw poll data from FiveThirtyEight and election outcomes from MEDSL.
Explicitly excludes RealClearPolitics (RCP) per project constraints.
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import requests
from tqdm import tqdm

# Import project utilities
# Ensure we can import from src/ even if running from root
if "code" in os.getcwd():
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))
elif os.getcwd().endswith("PROJ-206-statistical-analysis-of-publicly-availab"):
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from utils.config import (
    get_project_root, 
    get_data_root, 
    get_state_root, 
    compute_file_hash,
    ensure_dir
)
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
FIVETHIRTYEIGHT_BASE_URL = "https://projects.fivethirtyeight.com/polls/"
# MEDSL General Election Data URL (CSV format)
# Using the most recent general election data available via MEDSL
MEDSL_URL = "https://electionlab.mit.edu/sites/default/files/2021-09-24_general_election_results.csv"

# Output paths relative to project root
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
STATE_FILE = "state/projects/PROJ-206-statistical-analysis-of-publicly-availab.yaml"

def fetch_fivethirtyeight_polls() -> Optional[pd.DataFrame]:
    """
    Fetches the latest US House/Governor/Senate polls from FiveThirtyEight.
    Returns a DataFrame or None if fetch fails.
    """
    logger.info(f"Fetching FiveThirtyEight polls from {FIVETHIRTYEIGHT_BASE_URL}")
    
    # FiveThirtyEight provides specific CSV endpoints. 
    # For House polls (most common for aggregation), we use the specific CSV.
    # If generic, we might need to parse HTML, but they usually host a direct CSV.
    # URL pattern: https://projects.fivethirtyeight.com/polls/house-polls.csv
    csv_url = f"{FIVETHIRTYEIGHT_BASE_URL}house-polls.csv"
    
    try:
        response = requests.get(csv_url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV from content
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        logger.info(f"Successfully downloaded {len(df)} rows from FiveThirtyEight.")
        return df
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch FiveThirtyEight data: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing FiveThirtyEight data: {e}")
        return None

def fetch_medsl_outcomes() -> Optional[pd.DataFrame]:
    """
    Fetches historical election outcomes from MIT Election Data and Science Lab (MEDSL).
    Returns a DataFrame or None if fetch fails.
    """
    logger.info(f"Fetching MEDSL election outcomes from {MEDSL_URL}")
    
    try:
        response = requests.get(MEDSL_URL, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        logger.info(f"Successfully downloaded {len(df)} rows from MEDSL.")
        return df
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch MEDSL data: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing MEDSL data: {e}")
        return None

def save_raw_data(df: pd.DataFrame, source: str, filename: str) -> str:
    """
    Saves the dataframe to the raw data directory and returns the file path.
    """
    data_root = get_data_root()
    raw_path = data_root / RAW_DIR
    ensure_dir(raw_path)
    
    file_path = raw_path / filename
    df.to_csv(file_path, index=False)
    
    logger.info(f"Saved raw data to {file_path} ({len(df)} rows)")
    return str(file_path)

def update_state_file(file_path: str, source: str):
    """
    Updates the project state file with the hash of the new artifact.
    """
    state_root = get_state_root()
    ensure_dir(state_root)
    
    state_path = state_root / STATE_FILE
    
    # Load existing state or create new
    state_data = {}
    if state_path.exists():
        try:
            import yaml
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}")
            state_data = {}
    
    # Compute hash
    file_hash = compute_file_hash(file_path)
    
    # Update state
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    state_data["artifacts"][source] = {
        "path": file_path,
        "hash": file_hash,
        "updated_at": pd.Timestamp.now().isoformat()
    }
    
    # Write back
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {state_path}")

def main():
    """
    Main entry point for T009a.
    Fetches data, saves to raw/, and updates state.
    """
    logger.info("Starting T009a: Data Acquisition")
    
    # 1. Fetch FiveThirtyEight Polls
    polls_df = fetch_fivethirtyeight_polls()
    if polls_df is None:
        logger.error("Critical: Failed to fetch FiveThirtyEight data. Aborting.")
        sys.exit(1)
    
    # Save raw polls
    polls_path = save_raw_data(polls_df, "five_thirty_eight", "raw_polls.csv")
    update_state_file(polls_path, "raw_polls")
    
    # 2. Fetch MEDSL Outcomes
    outcomes_df = fetch_medsl_outcomes()
    if outcomes_df is None:
        logger.error("Critical: Failed to fetch MEDSL data. Aborting.")
        sys.exit(1)
    
    # Save raw outcomes
    outcomes_path = save_raw_data(outcomes_df, "medsl_outcomes", "raw_outcomes.csv")
    update_state_file(outcomes_path, "raw_outcomes")
    
    logger.info("T009a completed successfully. Data saved to data/raw/.")
    return 0

if __name__ == "__main__":
    main()
