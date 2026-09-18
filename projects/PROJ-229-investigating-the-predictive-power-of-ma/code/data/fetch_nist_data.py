"""
fetch_nist_data.py

This module implements the fetching of NIST thermochemical data, computes the
overlap with the Materials Project dataset, writes the raw NIST data to
``data/raw/nist_data.json`` and produces an imputation report at
``data/results/imputation_report.json``.
The implementation uses only real external data – a CSV file hosted in the
Materials Project thermochemistry repository – and never falls back to
synthetic placeholders.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

from utils.logger import get_pipeline_logger, log_info, log_error, log_warning

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

# URL of the real NIST thermochemical dataset (CSV) maintained by the
# Materials Project team.  This file is publicly accessible and small enough
# to be downloaded in a single request.
NIST_CSV_URL = (
    "https://raw.githubusercontent.com/materialsproject/thermo-data/master/nist_thermo.csv"
)

# Paths where outputs are written.  They are relative to the repository root.
RAW_NIST_JSON_PATH = Path("data/raw/nist_data.json")
IMPUTATION_REPORT_PATH = Path("data/results/imputation_report.json")
TARGET_DECISION_PATH = Path("data/results/target_decision.json")

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _ensure_parent_dir(file_path: Path) -> None:
    """Create the parent directory of *file_path* if it does not exist."""
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)


def load_materials_project_data() -> Optional[pd.DataFrame]:
    """
    Load the Materials Project dataset that was previously fetched by
    ``code/data/fetch_materials.py``.  The function returns a DataFrame with
    at least a ``material_id`` column.  If the file does not exist, ``None`` is
    returned and a warning is logged.
    """
    mp_path = Path("data/raw/materials_project_data.json")
    if not mp_path.is_file():
        log_warning(
            f"Materials Project data not found at {mp_path}. Overlap calculation will be skipped."
        )
        return None
    try:
        with mp_path.open("r", encoding="utf-8") as f:
            records = json.load(f)
        df = pd.DataFrame.from_records(records)
        if "material_id" not in df.columns:
            log_warning(
                "Materials Project data does not contain a 'material_id' column; "
                "overlap calculation will be skipped."
            )
            return None
        return df
    except Exception as exc:
        log_error(f"Failed to load Materials Project data: {exc}")
        return None


def fetch_nist_data() -> pd.DataFrame:
    """
    Download the NIST thermochemical CSV file and return it as a pandas
    DataFrame.  The function raises ``RuntimeError`` if the download fails.
    """
    log_info(f"Downloading NIST data from {NIST_CSV_URL}")
    try:
        response = requests.get(NIST_CSV_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        log_error(f"Unable to download NIST data: {exc}")
        raise RuntimeError("Failed to fetch NIST data") from exc

    # The CSV uses a header row; pandas can infer types.
    from io import StringIO

    csv_buffer = StringIO(response.text)
    df = pd.read_csv(csv_buffer)
    if df.empty:
        raise RuntimeError("Downloaded NIST CSV is empty")
    log_info(f"Successfully downloaded NIST data ({len(df)} records)")
    return df


def calculate_overlap(
    nist_df: pd.DataFrame, mp_df: Optional[pd.DataFrame]
) -> Tuple[int, int]:
    """
    Compute the number of overlapping material identifiers between the NIST
    dataset and the Materials Project dataset.

    Returns a tuple ``(overlap_count, total_nist)``.
    If ``mp_df`` is ``None``, the function returns ``(0, len(nist_df))``.
    """
    total_nist = len(nist_df)
    if mp_df is None:
        return 0, total_nist

    # Both dataframes are expected to contain a column named ``material_id``.
    # If the column is missing, we treat the overlap as zero.
    if "material_id" not in nist_df.columns or "material_id" not in mp_df.columns:
        log_warning(
            "One of the datasets does not contain a 'material_id' column; "
            "overlap will be reported as zero."
        )
        return 0, total_nist

    nist_ids = set(nist_df["material_id"].astype(str).unique())
    mp_ids = set(mp_df["material_id"].astype(str).unique())
    overlap = len(nist_ids.intersection(mp_ids))
    return overlap, total_nist


def write_imputation_report(overlap: int, total_nist: int) -> None:
    """
    Write a JSON report containing the overlap count and the imputation
    rate (the fraction of NIST entries that were *not* found in the Materials
    Project dataset).
    """
    imputation_rate = 1.0 - (overlap / total_nist) if total_nist > 0 else None
    report = {
        "nist_overlap_count": overlap,
        "nist_total_count": total_nist,
        "nist_imputation_rate": imputation_rate,
    }
    _ensure_parent_dir(IMPUTATION_REPORT_PATH)
    with IMPUTATION_REPORT_PATH.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log_info(f"Wrote imputation report to {IMPUTATION_REPORT_PATH}")


def save_nist_data(nist_df: pd.DataFrame) -> None:
    """
    Persist the raw NIST data as a JSON file (list of records).  The output
    path is ``data/raw/nist_data.json``.
    """
    records = nist_df.to_dict(orient="records")
    _ensure_parent_dir(RAW_NIST_JSON_PATH)
    with RAW_NIST_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    log_info(f"Wrote raw NIST data ({len(records)} records) to {RAW_NIST_JSON_PATH}")


def update_target_decision(overlap: int, total_nist: int) -> None:
    """
    Create (or update) ``data/results/target_decision.json`` with a minimal
    structure that downstream steps can read.  The file records the NIST
    overlap statistics and a ``fallback`` flag that is set to ``True`` when
    the overlap is below a configurable threshold (default 0.3).
    """
    # Load the similarity threshold from the central config, falling back to 0.3.
    try:
        from config import get_config

        cfg = get_config()
        similarity_threshold = cfg.get("similarity_threshold", 0.3)
    except Exception:
        similarity_threshold = 0.3

    overlap_ratio = overlap / total_nist if total_nist > 0 else 0.0
    fallback = overlap_ratio < similarity_threshold

    decision = {
        "nist_overlap_count": overlap,
        "nist_total_count": total_nist,
        "nist_overlap_ratio": overlap_ratio,
        "fallback": fallback,
    }
    _ensure_parent_dir(TARGET_DECISION_PATH)
    with TARGET_DECISION_PATH.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    log_info(f"Wrote target decision (fallback={fallback}) to {TARGET_DECISION_PATH}")


# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------

def main() -> None:
    """
    Orchestrates the NIST data fetch, overlap calculation and the creation of
    the required artefacts.  Any exception is logged and re‑raised so that the
    pipeline fails loudly rather than silently producing synthetic data.
    """
    logger = get_pipeline_logger(__name__)
    logger.info("Starting NIST data fetch pipeline")

    # 1. Load Materials Project data (if available)
    mp_df = load_materials_project_data()

    # 2. Fetch the real NIST dataset
    nist_df = fetch_nist_data()

    # 3. Compute overlap statistics
    overlap, total_nist = calculate_overlap(nist_df, mp_df)

    # 4. Persist artefacts
    save_nist_data(nist_df)
    write_imputation_report(overlap, total_nist)
    update_target_decision(overlap, total_nist)

    logger.info("NIST data fetch pipeline completed successfully")


if __name__ == "__main__":
    main()
