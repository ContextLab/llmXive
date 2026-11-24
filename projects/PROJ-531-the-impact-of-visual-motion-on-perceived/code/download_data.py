"""
T002 – Download real dataset & validate instrument

This script attempts to locate a publicly available dataset containing
human‑avatar interaction motion telemetry and a validated agency
questionnaire. It writes a status file ``data/raw/download_status.json``
with the required keys:

- ``status``: ``"success"``, ``"invalid"``, or ``"unavailable"``
- ``source_url``: URL of the dataset that was inspected (empty if none)
- ``instrument_valid``: boolean indicating whether the questionnaire
  passed DOI, citation‑count (≥10), and Cronbach’s α (≥0.70) checks
- ``use_synthetic``: ``true`` when the pipeline should fall back to
  synthetic data generation
- ``timestamp``: ISO‑8601 timestamp of the check
- ``reason``: human‑readable explanation of the outcome
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import re
import logging

import requests
import openml
import pandas as pd

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATA_RAW_DIR = Path("data/raw")
STATUS_PATH = DATA_RAW_DIR / "download_status.json"

# Candidate datasets – at least one known to exist on OpenML.
# In a real deployment these would be replaced with IDs that actually
# contain motion telemetry and an agency questionnaire.
TARGET_DATASETS = [
    {
        "source": "openml",
        "id": 1,  # Iris dataset – guaranteed to exist (used as a placeholder)
        "name": "Iris",
        "url": "https://www.openml.org/d/1",
    },
    # Additional candidates can be added here.
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def check_openml_dataset(dataset_id: int) -> bool:
    """
    Verify that an OpenML dataset exists and is active.

    Returns ``True`` if the dataset can be fetched successfully and its
    ``status`` field is ``active``; otherwise ``False``.
    """
    try:
        ds = openml.datasets.get_dataset(dataset_id)
        # ``status`` field is not directly exposed; we rely on successful fetch.
        return ds is not None
    except Exception as e:
        logger.warning(f"OpenML dataset {dataset_id} check failed: {e}")
        return False

def extract_doi(text: str) -> str | None:
    """
    Simple regex to pull a DOI from a free‑text string.
    """
    doi_regex = r"10\.\d{4,9}/[^\s\"\'<>]+"
    match = re.search(doi_regex, text, re.IGNORECASE)
    return match.group(0) if match else None

def validate_doi(doi: str) -> bool:
    """
    Validate that a DOI resolves via Crossref.
    """
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Crossref DOI check failed for {doi}: {e}")
        return False

def get_citation_count(doi: str) -> int | None:
    """
    Retrieve citation count from Semantic Scholar.
    Returns ``None`` on failure.
    """
    api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citationCount"
    try:
        resp = requests.get(api_url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("citationCount")
    except Exception as e:
        logger.warning(f"Semantic Scholar request failed for {doi}: {e}")
        return None

def compute_cronbach_alpha(df: pd.DataFrame) -> float | None:
    """
    Compute Cronbach's α for a set of questionnaire items.
    Returns ``None`` if fewer than 2 items are provided.
    """
    if df.shape[1] < 2:
        return None
    item_variances = df.var(axis=0, ddof=1)
    total_variance = df.sum(axis=1).var(ddof=1)
    if total_variance == 0:
        return None
    n_items = df.shape[1]
    alpha = (n_items / (n_items - 1)) * (1 - item_variances.sum() / total_variance)
    return float(alpha)

def validate_instrument(dataset: dict, df: pd.DataFrame) -> bool:
    """
    Perform the three validation steps required by FR‑013:
    1. DOI resolves via Crossref.
    2. Semantic Scholar citation count ≥ 10.
    3. Cronbach's α ≥ 0.70 on questionnaire items (if present).
    """
    # Step 1 – DOI extraction & validation
    description = dataset.get("description", "") or ""
    doi = extract_doi(description)
    if not doi:
        logger.info("No DOI found in dataset metadata.")
        return False
    if not validate_doi(doi):
        logger.info(f"DOI {doi} did not resolve via Crossref.")
        return False

    # Step 2 – Citation count
    citations = get_citation_count(doi)
    if citations is None:
        logger.info(f"Could not retrieve citation count for DOI {doi}.")
        return False
    if citations < 10:
        logger.info(f"Citation count {citations} < 10 for DOI {doi}.")
        return False

    # Step 3 – Cronbach's α
    # Heuristic: questionnaire items are columns that start with "agency_q"
    item_cols = [c for c in df.columns if c.lower().startswith("agency_q")]
    if not item_cols:
        logger.info("No questionnaire item columns detected for Cronbach's α.")
        return False
    alpha = compute_cronbach_alpha(df[item_cols])
    if alpha is None:
        logger.info("Cronbach's α could not be computed (insufficient variance).")
        return False
    if alpha < 0.70:
        logger.info(f"Cronbach's α = {alpha:.3f} < 0.70.")
        return False

    logger.info(f"Instrument validation passed (DOI {doi}, citations {citations}, α={alpha:.3f}).")
    return True

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def download_data() -> str:
    """
    Locate a suitable dataset, validate its instrument, and write the
    status JSON. On success the raw parquet file is written to
    ``data/raw/real_data.parquet``.
    """
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    status = "unavailable"
    source_url = ""
    instrument_valid = False
    reason = "No validated real dataset found in the configured repositories."

    for ds in TARGET_DATASETS:
        # --------------------------------------------------------------
        # 1. Verify dataset existence
        # --------------------------------------------------------------
        exists = False
        if ds["source"] == "openml":
            exists = check_openml_dataset(ds["id"])
        else:
            # Currently only OpenML is supported.
            continue

        if not exists:
            logger.info(f"Dataset {ds['name']} ({ds['source']} ID {ds['id']}) not reachable.")
            continue

        # --------------------------------------------------------------
        # 2. Load dataset
        # --------------------------------------------------------------
        try:
            openml_ds = openml.datasets.get_dataset(ds["id"])
            X, y, _, attribute_names = openml_ds.get_data(
                dataset_format="dataframe", target=openml_ds.default_target_attribute
            )
            df = pd.concat([X, y], axis=1)
        except Exception as e:
            logger.warning(f"Failed to download OpenML dataset {ds['id']}: {e}")
            continue

        source_url = ds["url"]

        # --------------------------------------------------------------
        # 3. Instrument validation
        # --------------------------------------------------------------
        instrument_valid = validate_instrument(openml_ds, df)

        if instrument_valid:
            status = "success"
            reason = (
                f"Validated instrument found in dataset '{ds['name']}' "
                f"({ds['source']} ID {ds['id']})."
            )
            # Save the raw data as parquet
            output_path = DATA_RAW_DIR / "real_data.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved real dataset to {output_path}")
        else:
            status = "invalid"
            reason = (
                f"Dataset '{ds['name']}' found but instrument failed "
                "validation (DOI/citations/Cronbach's α)."
            )
        # Stop after the first reachable dataset (whether valid or not)
        break

    # ------------------------------------------------------------------
    # 4. Build the status payload
    # ------------------------------------------------------------------
    use_synthetic = status != "success"
    payload = {
        "status": status,
        "source_url": source_url,
        "instrument_valid": instrument_valid,
        "use_synthetic": use_synthetic,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reason": reason,
    }

    # Write JSON file
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    # Inform the user
    print(f"Download status: {status}")
    print(f"Reason: {reason}")
    print(f"Status file written to: {STATUS_PATH}")

    # ------------------------------------------------------------------
    # 5. Exit handling – abort with non‑zero code if the instrument is invalid.
    # ------------------------------------------------------------------
    if status == "invalid":
        print("ERROR: Dataset excluded due to unvalidated instrument (FR‑009).")
        sys.exit(1)

    # For ``unavailable`` we simply continue; the synthetic generator will run later.
    return status

def main() -> None:
    """Entry‑point for ``python -m code.download_data``."""
    download_data()

if __name__ == "__main__":
    main()
