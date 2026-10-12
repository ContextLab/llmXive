"""
Data Fetcher for the OULAD dataset.

This module provides a single public function ``fetch_educational_dataset`` that
downloads the official Open University Learning Analytics Dataset (OULAD),
extracts the raw CSVs, maps them to the session schema required by the downstream
pipeline, validates the presence of the required columns and finally writes a
Parquet file to ``data/processed/cleaned_data.parquet``.
"""

import io
import zipfile
import logging
from pathlib import Path
from typing import List

import pandas as pd
import requests
from datasets import load_dataset

# Project-specific utilities
from llmxive_toolkit import paths, get_logger
from ingestion import DataAvailabilityError, DataSchemaError

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Primary URL (HTML page)
OULAD_PRIMARY_URL = "https://analyse.kmi.open.ac.uk/open_dataset"

# Verified mirror ZIP as specified in tasks.md
OULAD_MIRROR_ZIP = "https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/9b3hc-8t26.zip"

RAW_OULAD_DIR = paths.data("raw", "oulad")
PROCESSED_PARQUET = paths.data("processed", "cleaned_data.parquet")
REQUIRED_COLUMNS = ["recommended_categories", "enrolled_categories"]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def _download_and_extract_oulad() -> None:
    """
    Downloads the OULAD ZIP from the verified mirror and extracts the four
    CSV files into ``data/raw/oulad/``. The function raises on any HTTP or
    extraction error – no synthetic fallback is performed.
    """
    log.info("Attempting to download OULAD dataset from mirror URL: %s", OULAD_MIRROR_ZIP)
    try:
        response = requests.get(OULAD_MIRROR_ZIP, stream=True, timeout=120)
        response.raise_for_status()
    except Exception as exc:
        raise DataAvailabilityError(
            f"Failed to download OULAD from mirror URL: {exc}"
        ) from exc

    # Ensure the target directory exists
    RAW_OULAD_DIR.mkdir(parents=True, exist_ok=True)

    # Load the zip file into memory and extract
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        expected_files = {
            "studentInfo.csv",
            "studentVle.csv",
            "vle.csv",
            "studentRegistration.csv",
        }
        # The mirror might have different internal paths or naming; 
        # we check if the expected files are present anywhere in the zip.
        actual_files = zf.namelist()
        
        # Map expected names to actual paths in the zip (handling possible subfolders)
        file_map = {}
        for exp in expected_files:
            match = [f for f in actual_files if f.endswith(exp)]
            if match:
                file_map[exp] = match[0]

        missing = expected_files - set(file_map.keys())
        if missing:
            raise IOError(
                f"Missing expected OULAD files in the zip: {missing}. Found: {actual_files}"
            )

        for exp_name, zip_path in file_map.items():
            target_path = RAW_OULAD_DIR / exp_name
            with zf.open(zip_path) as src, open(target_path, "wb") as dst:
                dst.write(src.read())
            log.info("Extracted %s", target_path)

    log.info("OULAD download and extraction completed")

def _load_raw_csvs() -> dict:
    """
    Reads the four raw CSVs into pandas DataFrames and returns a dict.
    """
    files = {
        "studentInfo": RAW_OULAD_DIR / "studentInfo.csv",
        "studentVle": RAW_OULAD_DIR / "studentVle.csv",
        "vle": RAW_OULAD_DIR / "vle.csv",
        "studentRegistration": RAW_OULAD_DIR / "studentRegistration.csv",
    }

    dfs = {}
    for key, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(f"Expected OULAD file not found: {path}")
        dfs[key] = pd.read_csv(path)
        log.info("Loaded %s (%d rows)", key, len(dfs[key]))
    return dfs

def _map_oulad_to_sessions(dfs: dict) -> pd.DataFrame:
    """
    Maps the raw OULAD tables to the session schema required by the
    pipeline.
    """
    # Recommended categories (proxy via VLE accesses)
    student_vle = dfs["studentVle"]
    vle = dfs["vle"]

    category_col = "category" if "category" in vle.columns else "id_site"
    vle_subset = vle[["id_site", category_col]].rename(
        columns={category_col: "category"}
    )
    merged = pd.merge(
        student_vle,
        vle_subset,
        how="left",
        on="id_site",
    )

    rec_cats = (
        merged.groupby("id_student")["category"]
        .apply(lambda x: list(pd.unique(x.dropna())))
        .reset_index()
        .rename(columns={"category": "recommended_categories"})
    )

    # Enrolled categories (proxy via registration)
    student_reg = dfs["studentRegistration"]
    enrol_cats = (
        student_reg.groupby("id_student")["id_module"]
        .apply(lambda x: list(pd.unique(x.dropna())))
        .reset_index()
        .rename(columns={"id_module": "enrolled_categories"})
    )

    # Assemble final session table
    sessions = pd.merge(
        rec_cats,
        enrol_cats,
        how="outer",
        on="id_student",
    )

    sessions["recommended_categories"] = sessions["recommended_categories"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    sessions["enrolled_categories"] = sessions["enrolled_categories"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    sessions = sessions.rename(columns={"id_student": "user_id"})
    sessions["session_id"] = sessions["user_id"]

    sessions = sessions[
        ["user_id", "session_id", "recommended_categories", "enrolled_categories"]
    ]

    log.info("Mapped OULAD to session schema (%d rows)", len(sessions))
    return sessions

def _validate_schema(df: pd.DataFrame) -> None:
    """
    Ensures that the DataFrame contains the required columns.
    Raises DataSchemaError with the exact message required by the spec.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataSchemaError(
            "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
        )
    log.info("Schema validation passed")

def fetch_educational_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Fetches an educational dataset.
    """
    if dataset_id.lower() == "oulad":
        _download_and_extract_oulad()
        raw_dfs = _load_raw_csvs()

        session_df = _map_oulad_to_sessions(raw_dfs)
        _validate_schema(session_df)

        PROCESSED_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        session_df.to_parquet(PROCESSED_PARQUET, engine="pyarrow")
        log.info("Written processed session table to %s", PROCESSED_PARQUET)

        return session_df

    try:
        ds = load_dataset(dataset_id, split="train")
    except Exception as exc:
        raise DataAvailabilityError(
            f"Unable to load dataset '{dataset_id}' from the HuggingFace hub"
        ) from exc

    df = ds.to_pandas()
    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        raise ValueError(
            f"Dataset '{dataset_id}' missing required columns {REQUIRED_COLUMNS}"
        )

    log.info("Fetched dataset '%s' via HuggingFace – %d rows", dataset_id, len(df))
    return df

def main() -> None:
    """
    CLI entry point used by python -m code.data_fetcher.
    """
    try:
        fetch_educational_dataset("oulad")
    except Exception as exc:
        log.exception("Data fetching failed: %s", exc)
        raise

    log.info("Data fetching and validation completed successfully")

if __name__ == "__main__":
    main()
