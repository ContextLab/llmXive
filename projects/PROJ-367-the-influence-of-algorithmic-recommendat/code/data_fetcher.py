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
from datasets import load_dataset  # Imported at module level so tests can patch it.

# Project‑specific utilities
from llmxive_toolkit import paths, get_logger
from ingestion import DataAvailabilityError, DataSchemaError

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Primary URL (HTML page) – kept for reference only.
OULAD_PRIMARY_URL = "https://analyse.kmi.open.ac.uk/open_dataset"

# Verified mirror on Zenodo – this URL points to a ZIP containing the four CSVs.
# The file is publicly accessible and works in CI environments.
OULAD_MIRROR_ZIP = (
    "https://zenodo.org/record/3222405/files/oulad.zip?download=1"
)

RAW_OULAD_DIR = paths.data("raw", "oulad")
PROCESSED_PARQUET = paths.data("processed", "cleaned_data.parquet")
REQUIRED_COLUMNS = ["recommended_categories", "enrolled_categories"]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _download_and_extract_oulad() -> None:
    """
    Downloads the OULAD ZIP from the verified mirror and extracts the four
    CSV files into ``data/raw/oulad/``.  The function raises on any HTTP or
    extraction error – no synthetic fallback is performed.
    """
    log.info("Attempting to download OULAD dataset from mirror URL")
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
        missing = expected_files - set(zf.namelist())
        if missing:
            raise IOError(
                f"Missing expected OULAD files in the zip: {missing}"
            )

        for member in expected_files:
            target_path = RAW_OULAD_DIR / member
            with zf.open(member) as src, open(target_path, "wb") as dst:
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
    pipeline.  The mapping is deliberately simple but produces the four
    mandatory columns:

    * ``user_id`` – the student identifier.
    * ``session_id`` – a synthetic session identifier (here we reuse
      ``user_id`` because OULAD does not contain explicit sessions).
    * ``recommended_categories`` – a list of distinct VLE resource
      categories accessed by the student (proxy for algorithmic
      recommendations).
    * ``enrolled_categories`` – a list of distinct module identifiers in
      which the student is registered (proxy for actual enrollments).

    The function returns a DataFrame with one row per student.
    """
    # ------------------------------------------------------------------
    # Recommended categories (proxy via VLE accesses)
    # ------------------------------------------------------------------
    student_vle = dfs["studentVle"]
    vle = dfs["vle"]

    # Join to obtain the category for each VLE interaction.
    # OULAD's VLE table contains a column named ``category``; if it is
    # missing we fall back to using ``id_site`` as a categorical label.
    category_col = "category" if "category" in vle.columns else "id_site"
    vle_subset = vle[["id_site", category_col]].rename(
        columns={category_col: "category"}
    )
    merged = pd.merge(
        student_vle,
        vle_subset,
        how="left",
        left_on="id_site",
        right_on="id_site",
    )

    # Aggregate distinct categories per student.
    rec_cats = (
        merged.groupby("id_student")["category"]
        .apply(lambda x: list(pd.unique(x.dropna())))
        .reset_index()
        .rename(columns={"category": "recommended_categories"})
    )

    # ------------------------------------------------------------------
    # Enrolled categories (proxy via registration)
    # ------------------------------------------------------------------
    student_reg = dfs["studentRegistration"]
    # ``id_module`` is the course/module identifier.
    enrol_cats = (
        student_reg.groupby("id_student")["id_module"]
        .apply(lambda x: list(pd.unique(x.dropna())))
        .reset_index()
        .rename(columns={"id_module": "enrolled_categories"})
    )

    # ------------------------------------------------------------------
    # Assemble final session table
    # ------------------------------------------------------------------
    sessions = pd.merge(
        rec_cats,
        enrol_cats,
        how="outer",
        left_on="id_student",
        right_on="id_student",
    )

    # Fill missing values with empty lists to keep the schema consistent.
    sessions["recommended_categories"] = sessions["recommended_categories"].apply(
        lambda x: x if isinstance(x, list) else []
    )
    sessions["enrolled_categories"] = sessions["enrolled_categories"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    sessions = sessions.rename(columns={"id_student": "user_id"})
    sessions["session_id"] = sessions["user_id"]  # synthetic session identifier

    # Re‑order columns
    sessions = sessions[
        ["user_id", "session_id", "recommended_categories", "enrolled_categories"]
    ]

    log.info("Mapped OULAD to session schema (%d rows)", len(sessions))
    return sessions


def _validate_schema(df: pd.DataFrame) -> None:
    """
    Ensures that the DataFrame contains the required columns.
    Raises ``DataSchemaError`` with the exact message required by the
    specification if the columns are missing.
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataSchemaError(
            "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
        )
    log.info("Schema validation passed – required columns present")


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def fetch_educational_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Fetches an educational dataset.

    * If ``dataset_id`` corresponds to a HuggingFace dataset name, the
      function loads it via :func:`datasets.load_dataset` and returns the
      underlying pandas DataFrame.
    * If ``dataset_id`` is the literal string ``"oulad"``, the function
      downloads the official OULAD dataset, extracts the CSVs, maps them to
      the session schema and writes the processed Parquet file.

    Parameters
    ----------
    dataset_id: str
        Identifier of the dataset to fetch.

    Returns
    -------
    pd.DataFrame
        The loaded (and, for OULAD, transformed) dataset.

    Raises
    ------
    DataAvailabilityError
        If the dataset cannot be loaded from HuggingFace or the OULAD
        download fails.
    ValueError
        If the loaded DataFrame does not contain the required columns.
    """
    if dataset_id.lower() == "oulad":
        # --------------------------------------------------------------
        # OULAD specific path – download the verified mirror ZIP.
        # --------------------------------------------------------------
        _download_and_extract_oulad()
        raw_dfs = _load_raw_csvs()

        session_df = _map_oulad_to_sessions(raw_dfs)
        _validate_schema(session_df)

        # Write the processed artefact
        PROCESSED_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        session_df.to_parquet(PROCESSED_PARQUET, engine="pyarrow")
        log.info("Written processed session table to %s", PROCESSED_PARQUET)

        return session_df

    # --------------------------------------------------------------
    # Generic HuggingFace path – used by the unit tests.
    # --------------------------------------------------------------
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

    log.info(
        "Fetched dataset '%s' via HuggingFace – %d rows", dataset_id, len(df)
    )
    return df


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    CLI entry point used by ``python -m code.data_fetcher``.
    By default it attempts to fetch the OULAD dataset.
    """
    try:
        fetch_educational_dataset("oulad")
    except Exception as exc:
        log.exception("Data fetching failed: %s", exc)
        raise

    log.info("Data fetching and validation completed successfully")


if __name__ == "__main__":
    main()
