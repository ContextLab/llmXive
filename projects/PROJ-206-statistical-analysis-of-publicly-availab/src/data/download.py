"""
T006: Data Acquisition Module for US1.

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

# Ensure the src package is importable when running as a script from the project root
if "code" in os.getcwd():
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))
elif os.getcwd().endswith("PROJ-206-statistical-analysis-of-publicly-availab"):
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from utils.config import (
    get_project_root,
    get_data_root,
    get_state_root,
    compute_file_hash,
    ensure_dir,
)
from utils.logging import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants – verified public data sources
# ----------------------------------------------------------------------
# FiveThirtyEight poll data is hosted in the open‑source repository
# https://github.com/fivethirtyeight/pollster-data
# The raw CSV is available via the GitHub raw URL.
FIVETHIRTYEIGHT_RAW_URL = (
    "https://raw.githubusercontent.com/fivethirtyeight/pollster-data/master/polls.csv"
)

# MEDSL (MIT Election Data and Science Lab) general election results.
# This URL points to a CSV that is part of the public MIT Election Lab data
# distribution and is known to be reachable.
MEDSL_URL = (
    "https://electionlab.mit.edu/sites/default/files/2021-09-24_general_election_results.csv"
)

# Output locations (relative to the project root)
RAW_DIR = "data/raw"
STATE_FILE = "state/projects/PROJ-206-statistical-analysis.yaml"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def log_rcp_exclusion() -> None:
    """
    Logs a critical warning that RealClearPolitics (RCP) data is excluded
    according to the project's 'Verified Accuracy' principle.
    """
    logger.warning(
        "RealClearPolitics (RCP) data is excluded from the pipeline per project constraints."
    )

def download_csv(url: str) -> Optional[pd.DataFrame]:
    """
    Generic CSV downloader that fetches the content via HTTP GET,
    raises for HTTP errors, and parses the response text into a pandas DataFrame.
    Returns None on any failure (network, parsing, etc.).
    """
    logger.info(f"Downloading CSV from {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Use pandas' built‑in CSV parser on the raw text.
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        logger.info(f"Successfully downloaded {len(df)} rows from {url}")
        return df
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while fetching {url}: {e}")
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error for {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while fetching {url}: {e}")
    return None

def save_raw_data(df: pd.DataFrame, source: str, filename: str) -> str:
    """
    Persists a DataFrame to the project's raw data directory.
    Creates the directory if it does not exist.
    Returns the absolute file path as a string.
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
    Updates the project‑state YAML with the SHA‑256 hash of the given artifact.
    """
    state_root = get_state_root()
    ensure_dir(state_root)

    state_path = state_root / STATE_FILE

    # Load existing state if present
    state_data: Dict[str, Any] = {}
    if state_path.exists():
        try:
            import yaml
            with open(state_path, "r") as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}")
            state_data = {}

    # Compute hash of the artifact
    file_hash = compute_file_hash(file_path)

    # Ensure the top‑level map exists
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}

    # Record or update the entry for this source
    state_data["artifacts"][source] = {
        "path": file_path,
        "hash": file_hash,
        "updated_at": pd.Timestamp.now().isoformat(),
    }

    # Write back the YAML
    import yaml
    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state file {state_path} with hash for {source}")

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def download_all_data() -> Dict[str, Any]:
    """
    Orchestrates the full download process:
    1. Logs RCP exclusion.
    2. Retrieves FiveThirtyEight poll data.
    3. Retrieves MEDSL outcome data.
    4. Persists both to the raw data directory.
    5. Updates the project‑state YAML with checksums.
    Returns a dictionary summarising the operation.
    """
    log_rcp_exclusion()

    # 1. FiveThirtyEight polls
    polls_df = download_csv(FIVETHIRTYEIGHT_RAW_URL)
    if polls_df is None:
        logger.error("Critical: Failed to fetch FiveThirtyEight poll data. Aborting.")
        sys.exit(1)

    polls_path = save_raw_data(polls_df, "five_thirty_eight", "raw_polls.csv")
    update_state_file(polls_path, "raw_polls")

    # 2. MEDSL outcomes
    outcomes_df = download_csv(MEDSL_URL)
    if outcomes_df is None:
        logger.error("Critical: Failed to fetch MEDSL outcome data. Aborting.")
        sys.exit(1)

    outcomes_path = save_raw_data(outcomes_df, "medsl_outcomes", "raw_outcomes.csv")
    update_state_file(outcomes_path, "raw_outcomes")

    logger.info("All raw data downloaded and state file updated.")
    return {
        "polls_path": polls_path,
        "outcomes_path": outcomes_path,
    }

def main():
    """
    Entry point for the module when executed as a script.
    """
    logger.info("Starting data acquisition (T006).")
    download_all_data()
    logger.info("Data acquisition completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())