"""
Data Acquisition Module for Election Poll Aggregation.

This module fetches raw poll data from FiveThirtyEight and election outcomes
from the MIT Election Data and Science Lab (MEDSL).

Constraints:
- RealClearPolitics (RCP) data is explicitly excluded per the 'Verified Accuracy' principle.
- All data is fetched programmatically at runtime.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import requests

# Project internal imports
from src.utils.config import get_project_root, get_raw_data_path, get_data_processed_path
from src.utils.logging import get_logger

# Constants
FIVETHIRYEIGHT_BASE_URL = "https://projects.fivethirtyeight.com/polls/"
# MEDSL provides state-level and national results. We use the state-level dataset for consistency.
# Direct CSV link for state election results (US House/Senate/Governor)
MEDSL_STATE_RESULTS_URL = "https://electionlab.mit.edu/sites/default/files/2021-04-01_state_results.csv"
# Fallback for National results if needed, but state is preferred for granular poll matching
MEDSL_NATIONAL_RESULTS_URL = "https://electionlab.mit.edu/sites/default/files/2021-04-01_national_results.csv"

# Logger setup
logger = get_logger(__name__)


def fetch_url_content(url: str, timeout: int = 60) -> Optional[pd.DataFrame]:
    """
    Fetches a CSV from a URL and returns it as a DataFrame.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        DataFrame if successful, None otherwise.
    """
    try:
        logger.info(f"Fetching data from: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        # FiveThirtyEight and MEDSL usually serve CSVs directly
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        logger.info(f"Successfully fetched {len(df)} rows from {url}")
        return df
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Received empty data from {url}")
        return None


def download_fivethirtyeight_polls() -> Optional[pd.DataFrame]:
    """
    Downloads the latest FiveThirtyEight poll aggregate CSV.
    URL: https://projects.fivethirtyeight.com/polls/poll-data.csv
    """
    # The main poll data file
    url = f"{FIVETHIRYEIGHT_BASE_URL}poll-data.csv"
    return fetch_url_content(url)


def download_election_outcomes() -> Optional[pd.DataFrame]:
    """
    Downloads election outcomes from MEDSL.
    Prefers state-level results to match with state polls, falling back to national if needed.
    """
    # Try state results first (more granular)
    df = fetch_url_content(MEDSL_STATE_RESULTS_URL)
    if df is not None:
        logger.info("Using MEDSL State Results.")
        return df

    # Fallback to national if state fails
    logger.warning("State results failed, trying National results.")
    return fetch_url_content(MEDSL_NATIONAL_RESULTS_URL)


def run_download_pipeline():
    """
    Orchestrates the download of all required raw data sources.
    Saves raw data to data/raw/ directory.
    """
    project_root = get_project_root()
    raw_data_dir = get_raw_data_path()

    # Ensure directory exists
    os.makedirs(raw_data_dir, exist_ok=True)

    logger.info("Starting data acquisition pipeline...")

    # 1. Download FiveThirtyEight Polls
    polls_df = download_fivethirtyeight_polls()
    if polls_df is None:
        logger.critical("Failed to download FiveThirtyEight polls. Aborting pipeline.")
        return False

    # Save raw polls
    raw_polls_path = raw_data_dir / "fivethirtyeight_polls_raw.csv"
    polls_df.to_csv(raw_polls_path, index=False)
    logger.info(f"Saved raw polls to {raw_polls_path}")

    # 2. Download Election Outcomes
    outcomes_df = download_election_outcomes()
    if outcomes_df is None:
        logger.critical("Failed to download election outcomes. Aborting pipeline.")
        return False

    # Save raw outcomes
    raw_outcomes_path = raw_data_dir / "medsl_outcomes_raw.csv"
    outcomes_df.to_csv(raw_outcomes_path, index=False)
    logger.info(f"Saved raw outcomes to {raw_outcomes_path}")

    logger.info("Data acquisition pipeline completed successfully.")
    return True


def main():
    """Entry point for the download script."""
    # Initialize logging
    # Note: init_logging is called in main.py usually, but safe to call again or rely on config
    # We assume logging is configured elsewhere or default to basicConfig if not
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    success = run_download_pipeline()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
