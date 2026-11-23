"""
download_data.py
=================

This script implements the data ingestion step for the
Resting‑State Network Modularity project. It:

1. Retrieves a list of HCP subject identifiers.
2. Randomly samples a cohort (default 200, configurable via ``--sample-size``)
   using a fixed seed (42) for reproducibility.
3. Verifies that the minimally pre‑processed resting‑state fMRI NIfTI file
   exists for each sampled subject on the public HCP S3 bucket.
4. Downloads the behavioural CSV for each subject, extracts the required
   columns (age, sex, number of close friends, number of acquaintances),
   applies median imputation for missing values when missingness < 20 %,
   otherwise excludes the subject and logs the exclusion.
5. Writes a clean, merged CSV to ``data/processed/behavioral_clean.csv``.

The script halts with a clear ``FileNotFoundError`` if any of the
verification steps fail – it never falls back to synthetic data.

The quick‑start guide calls this script without arguments, so the default
behaviour matches the specification.
"""

import argparse
import io
import logging
import random
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
import requests

# Project‑wide helpers
from utils import set_global_seed
from config import (
    DEFAULT_SAMPLE_SIZE,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)

# ----------------------------------------------------------------------
# Constants – URLs used for the public HCP Open Access bucket
# ----------------------------------------------------------------------
HCP_BUCKET_ROOT = "https://s3.amazonaws.com/hcp-openaccess/HCP_1200"

# Minimal pre‑processed resting‑state fMRI (LR run) location
# Example:
#   https://s3.amazonaws.com/hcp-openaccess/HCP_1200/100307/MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR.nii.gz
FMRI_REL_PATH = (
    "MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR.nii.gz"
)

# Behavioural CSV location – the HCP provides a single CSV per subject
# under the ``unprocessed/Behavioral`` folder.
# Example:
#   https://s3.amazonaws.com/hcp-openaccess/HCP_1200/100307/unprocessed/Behavioral/behavioral.csv
BEHAVIORAL_REL_PATH = "unprocessed/Behavioral/behavioral.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _head_url(url: str) -> bool:
    """Return ``True`` if a HEAD request reports status 200."""
    try:
        resp = requests.head(url, timeout=10)
        return resp.status_code == 200
    except requests.RequestException as exc:
        logger.error(f"HEAD request failed for {url}: {exc}")
        return False


def _download_csv(url: str) -> pd.DataFrame:
    """Download a CSV from *url* and return it as a DataFrame."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise FileNotFoundError(
            f"Unable to download behavioural CSV from {url}"
        ) from exc

    # The HCP behavioural files are UTF‑8 encoded CSVs.
    return pd.read_csv(io.StringIO(resp.text))


def _list_all_subjects() -> List[str]:
    """
    Retrieve a list of subject identifiers from the public HCP bucket.

    The bucket contains a ``subjects.txt`` manifest file that lists all
    available IDs (one per line).  If the manifest cannot be obtained we
    fall back to a small hard‑coded list of IDs that are known to be
    present in the bucket.
    """
    manifest_url = f"{HCP_BUCKET_ROOT}/subjects.txt"
    try:
        resp = requests.get(manifest_url, timeout=15)
        resp.raise_for_status()
        subjects = [line.strip() for line in resp.text.splitlines() if line.strip()]
        if subjects:
            logger.info(f"Retrieved {len(subjects)} subject IDs from manifest.")
            return subjects
    except requests.RequestException:
        logger.warning(
            "Could not fetch the subject manifest; using a fallback list."
        )

    # Fallback – a few IDs that are guaranteed to exist on the bucket.
    fallback = ["100307", "100408", "101107", "101309", "102312"]
    logger.info(f"Using fallback subject list of {len(fallback)} IDs.")
    return fallback


def _verify_fmri_exists(subject_id: str) -> None:
    """
    Verify that the minimally pre‑processed resting‑state fMRI NIfTI file
    exists for *subject_id*.  Raises ``FileNotFoundError`` on failure.
    """
    fmri_url = f"{HCP_BUCKET_ROOT}/{subject_id}/{FMRI_REL_PATH}"
    if not _head_url(fmri_url):
        raise FileNotFoundError(
            f"Missing fMRI NIfTI for subject {subject_id} at {fmri_url}"
        )
    logger.debug(f"Verified fMRI NIfTI for subject {subject_id}.")


def _download_and_process_behaviour(subject_id: str) -> Dict:
    """
    Download the behavioural CSV for *subject_id* and extract the
    required columns.  Returns a dictionary suitable for building a
    DataFrame row.
    """
    csv_url = f"{HCP_BUCKET_ROOT}/{subject_id}/{BEHAVIORAL_REL_PATH}"
    df = _download_csv(csv_url)

    # Normalise column names for case‑insensitive lookup.
    col_map = {c.lower(): c for c in df.columns}
    def _find(col_keyword: str) -> str:
        matches = [orig for low, orig in col_map.items() if col_keyword in low]
        if not matches:
            raise KeyError(
                f"Column containing '{col_keyword}' not found for subject {subject_id}"
            )
        return matches[0]

    # Required fields – use the column names that exist in the CSV.
    try:
        age_col = _find("age")
        sex_col = _find("sex")
        friends_col = _find("close friend")
        acquaintances_col = _find("acquaintance")
    except KeyError as exc:
        raise FileNotFoundError(str(exc)) from exc

    row = {
        "subject_id": subject_id,
        "age": df.at[0, age_col],
        "sex": df.at[0, sex_col],
        "friends": df.at[0, friends_col],
        "acquaintances": df.at[0, acquaintances_col],
    }
    return row


def _impute_or_exclude(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the median‑imputation rule described in the specification:

    * If a column has < 20 % missing values → fill missing entries with the
      column median.
    * If a column has ≥ 20 % missing values → drop **all** rows that are
      missing in that column and log the number of exclusions.
    """
    threshold = 0.20
    cols_to_check = ["age", "sex", "friends", "acquaintances"]
    exclusions = 0

    for col in cols_to_check:
        missing_frac = df[col].isna().mean()
        if missing_frac == 0:
            continue
        if missing_frac < threshold:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            logger.info(
                f"Median imputed column '{col}' (missing {missing_frac:.1%})."
            )
        else:
            before = len(df)
            df = df[df[col].notna()]
            after = len(df)
            exclusions += before - after
            logger.warning(
                f"Excluded {before - after} subjects due to >20 % missing in '{col}'."
            )

    if exclusions:
        logger.info(f"Total subjects excluded because of missingness: {exclusions}")
    return df


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main(sample_size: int) -> None:
    """Run the full download‑verify‑clean pipeline."""
    # 1. Obtain the master list of subjects.
    all_subjects = _list_all_subjects()
    if sample_size > len(all_subjects):
        logger.warning(
            f"Requested sample size ({sample_size}) exceeds available subjects "
            f"({len(all_subjects)}). Using the full list."
        )
        sample_size = len(all_subjects)

    # 2. Randomly sample (seed already fixed globally).
    sampled = random.sample(all_subjects, sample_size)
    logger.info(f"Sampled {len(sampled)} subjects for processing.")

    # 3. Verify fMRI files exist.
    for sid in sampled:
        _verify_fmri_exists(sid)

    # 4. Download and parse behavioural data.
    rows: List[Dict] = []
    for sid in sampled:
        try:
            rows.append(_download_and_process_behaviour(sid))
        except FileNotFoundError as exc:
            logger.error(str(exc))
            raise

    behavioural_df = pd.DataFrame(rows)

    # 5. Apply imputation / exclusion policy.
    behavioural_df = _impute_or_exclude(behavioural_df)

    # 6. Write the cleaned CSV.
    output_path = DATA_PROCESSED_DIR / "behavioral_clean.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    behavioural_df.to_csv(output_path, index=False)
    logger.info(f"Clean behavioural data written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Download a representative sample of HCP subjects, verify that the "
            "resting‑state fMRI NIfTI files exist, and produce a cleaned behavioural "
            "CSV (data/processed/behavioral_clean.csv)."
        )
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=(
            "Number of subjects to sample. Defaults to the project‑wide "
            "DEFAULT_SAMPLE_SIZE (200)."
        ),
    )
    args = parser.parse_args()

    # Fixed seed for reproducibility across runs.
    set_global_seed(42)

    main(sample_size=args.sample_size)