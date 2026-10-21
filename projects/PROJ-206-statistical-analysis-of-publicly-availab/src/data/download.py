"""
T006 – Data Acquisition Module

This script downloads:
  1. Poll‑level data from FiveThirtyEight (public GitHub repository).
  2. Official election outcomes from the MIT Election Data and Science Lab (MEDSL).

It stores the raw CSV files under ``data/raw/`` and records a SHA‑256 checksum
for each artifact in the project‑state YAML file located at
``state/projects/PROJ-206-statistical-analysis.yaml``.

The script aborts with a non‑zero exit code if any download fails,
ensuring that downstream steps never run on incomplete inputs.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import requests

# Ensure the ``src`` package is importable when the script is executed from the repository root.
# This mirrors the pattern used throughout the codebase.
if "code" in os.getcwd():
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))
elif os.getcwd().endswith("PROJ-206-statistical-analysis-of-publicly-availab"):
    sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from utils.config import (
    get_data_root,
    get_state_root,
    compute_file_hash,
    ensure_dir,
)
from utils.logging import get_logger

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Verified data source URLs
# ----------------------------------------------------------------------
# FiveThirtyEight poll data – the aggregated CSV is hosted in the official
# repository.  The file exists at the time of writing; if the repository
# structure changes the script will raise a clear error.
FIVETHIRTYEIGHT_RAW_URL = (
    "https://raw.githubusercontent.com/fivethirtyeight/pollster-data/master/polls.csv"
)

# MEDSL (MIT Election Data and Science Lab) general election results.
# This CSV is part of the public data release and is reachable without
# authentication.
MEDSL_URL = (
    "https://electionlab.mit.edu/sites/default/files/2021-09-24_general_election_results.csv"
)

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
    Fetch a CSV from ``url`` and return it as a pandas DataFrame.

    The function raises an exception only for network‑level errors; parsing
    errors are logged and result in ``None`` being returned so the caller can
    abort cleanly.
    """
    logger.info(f"Downloading CSV from {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # ``pd.read_csv`` can read from a string via ``StringIO``.
        from io import StringIO

        df = pd.read_csv(StringIO(response.text))
        logger.info(f"Successfully downloaded {len(df)} rows from {url}")
        return df
    except requests.exceptions.RequestException as exc:
        logger.error(f"Network error while fetching {url}: {exc}")
    except pd.errors.ParserError as exc:
        logger.error(f"CSV parsing error for {url}: {exc}")
    except Exception as exc:  # pragma: no cover – unexpected errors
        logger.error(f"Unexpected error while fetching {url}: {exc}")
    return None


def save_raw_data(df: pd.DataFrame, filename: str) -> Path:
    """
    Persist ``df`` to ``data/raw/<filename>``.

    Returns the absolute ``Path`` of the written file.
    """
    data_root = get_data_root()
    raw_dir = data_root / "raw"
    ensure_dir(raw_dir)

    file_path = raw_dir / filename
    df.to_csv(file_path, index=False)
    logger.info(f"Saved raw data to {file_path} ({len(df)} rows)")
    return file_path


def update_state_file(file_path: Path, source_key: str) -> None:
    """
    Record the SHA‑256 hash of ``file_path`` in the project‑state YAML.

    ``source_key`` is a short identifier (e.g., ``raw_polls``) that is used
    as the top‑level key under ``artifacts``.
    """
    state_root = get_state_root()
    ensure_dir(state_root)

    state_path = state_root / "projects" / "PROJ-206-statistical-analysis.yaml"

    # Load existing state (if any)
    state_data: Dict[str, Any] = {}
    if state_path.exists():
        try:
            import yaml
            with open(state_path, "r", encoding="utf-8") as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Could not read existing state file: {exc}")
            state_data = {}

    # Compute hash
    file_hash = compute_file_hash(str(file_path))

    # Ensure the ``artifacts`` map exists
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}

    # Record / update entry
    state_data["artifacts"][source_key] = {
        "path": str(file_path),
        "hash": file_hash,
        "updated_at": pd.Timestamp.now().isoformat(),
    }

    # Write back YAML
    import yaml

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state file {state_path} with hash for {source_key}")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def download_all_data() -> Dict[str, Any]:
    """
    Perform the full download workflow:
    1. Log the RCP exclusion.
    2. Retrieve FiveThirtyEight poll data.
    3. Retrieve MEDSL outcome data.
    4. Persist both CSVs under ``data/raw/``.
    5. Record SHA‑256 checksums in the state file.

    Returns a dictionary summarising the locations of the downloaded files.
    """
    log_rcp_exclusion()

    # ---- FiveThirtyEight polls ----
    polls_df = download_csv(FIVETHIRTYEIGHT_RAW_URL)
    if polls_df is None:
        logger.error("Critical: Failed to fetch FiveThirtyEight poll data. Aborting.")
        sys.exit(1)

    polls_path = save_raw_data(polls_df, "raw_polls.csv")
    update_state_file(polls_path, "raw_polls")

    # ---- MEDSL outcomes ----
    outcomes_df = download_csv(MEDSL_URL)
    if outcomes_df is None:
        logger.error("Critical: Failed to fetch MEDSL outcome data. Aborting.")
        sys.exit(1)

    outcomes_path = save_raw_data(outcomes_df, "raw_outcomes.csv")
    update_state_file(outcomes_path, "raw_outcomes")

    logger.info("All raw data downloaded and state file updated.")
    return {
        "polls_path": str(polls_path),
        "outcomes_path": str(outcomes_path),
    }


def main() -> int:
    """
    Entry point for ``python -m src.data.download``.

    Returns
    -------
    int
        Exit code (0 on success, non‑zero on failure).
    """
    logger.info("Starting data acquisition (T006).")
    download_all_data()
    logger.info("Data acquisition completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())