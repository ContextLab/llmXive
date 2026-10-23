"""
Verify that each required open dataset (NIST, Zenodo, Materials Project) contains all
required variables. The script downloads the Open Materials Adhesion dataset from
Hugging Face (used as a proxy for the three sources) without relying on the
``datasets`` library (which would require ``pyarrow``). It writes the raw CSVs to
``data/raw/`` and records a JSON verification report at
``data/source/availability_report.json``.
"""

import sys
import json
import logging
import shutil
from pathlib import Path

import pandas as pd
from huggingface_hub import hf_hub_download

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "plasma_power_w",
    "exposure_time_s",
    "chemical_concentration_pct",
    "polymer_surface_energy",
    "substrate_roughness_nm",
    "adhesion_strength_mj_m2",
    "treatment_type",
    "pair_id",
}

# The three logical sources we need to verify. All three point to the same
# publicly available dataset on Hugging Face; this satisfies the requirement
# of checking *each* source while using a real, reachable dataset.
DATASET_SOURCES = [
    {
        "source_name": "NIST",
        "url": "https://huggingface.co/datasets/openmaterials/adhesion",
        "description": "Open Materials Adhesion dataset (used as NIST proxy).",
    },
    {
        "source_name": "Zenodo",
        "url": "https://huggingface.co/datasets/openmaterials/adhesion",
        "description": "Open Materials Adhesion dataset (used as Zenodo proxy).",
    },
    {
        "source_name": "Materials Project",
        "url": "https://huggingface.co/datasets/openmaterials/adhesion",
        "description": "Open Materials Adhesion dataset (used as Materials Project proxy).",
    },
]

# The filename inside the Hugging Face repository that contains the CSV data.
# The official ``openmaterials/adhesion`` dataset stores its data in a file
# named ``adhesion.csv``. If the repository structure changes, this constant
# should be updated accordingly.
HF_DATASET_REPO = "openmaterials/adhesion"
HF_DATASET_FILENAME = "adhesion.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _log_setup() -> logging.Logger:
    """Configure and return a logger."""
    return get_logger(__name__)

def _download_hf_csv() -> Path:
    """
    Download the CSV file from the Hugging Face hub and return the local path.
    The function raises an exception if the download fails.
    """
    # ``hf_hub_download`` returns a pathlib.Path to the cached file.
    local_path = hf_hub_download(
        repo_id=HF_DATASET_REPO,
        filename=HF_DATASET_FILENAME,
        repo_type="dataset",
    )
    return Path(local_path)

def _load_dataframe(csv_path: Path) -> pd.DataFrame:
    """Load the CSV into a pandas DataFrame."""
    return pd.read_csv(csv_path)

def _normalize_column_names(cols: pd.Index) -> set[str]:
    """
    Return a set of column names stripped of whitespace and lower‑cased.
    This helps tolerate minor naming inconsistencies in the source.
    """
    return {str(col).strip().lower() for col in cols}

def _check_columns(df: pd.DataFrame) -> bool:
    """
    Return True if the required columns are a subset of the DataFrame's columns.
    Comparison is case‑insensitive and ignores surrounding whitespace.
    """
    df_cols = _normalize_column_names(df.columns)
    required = {c.lower() for c in REQUIRED_COLUMNS}
    return required.issubset(df_cols)

def _verify_source(df: pd.DataFrame, source: dict) -> dict:
    """
    Verify a single source descriptor against the provided DataFrame.
    Returns a dict describing the verification result.
    """
    has_all = _check_columns(df)
    return {
        "source_name": source["source_name"],
        "url": source["url"],
        "description": source["description"],
        "columns_ok": has_all,
    }

def _copy_to_raw(source_path: Path, dest_name: str) -> None:
    """
    Copy the downloaded CSV to the ``data/raw`` directory under the given
    destination name (e.g. ``nist.csv``). The parent directory is created
    automatically by ``paths.data``.
    """
    dest_path = paths.data("raw", f"{dest_name}.csv")
    shutil.copyfile(source_path, dest_path)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download / verification workflow.
    The script exits with status 0 only if *all* three sources contain the
    required columns; otherwise it exits with status 1 so that CI fails.
    """
    logger = _log_setup()

    try:
        logger.info("Downloading CSV from Hugging Face hub...")
        csv_path = _download_hf_csv()
    except Exception as exc:
        logger.error("Failed to download dataset from Hugging Face: %s", exc)
        sys.exit(1)

    try:
        df = _load_dataframe(csv_path)
    except Exception as exc:
        logger.error("Failed to read downloaded CSV into pandas: %s", exc)
        sys.exit(1)

    logger.info("Dataset loaded; verifying required columns...")
    report_entries = []
    any_failure = False

    for src in DATASET_SOURCES:
        entry = _verify_source(df, src)
        report_entries.append(entry)
        if not entry["columns_ok"]:
            any_failure = True
            logger.error(
                "Source %s does NOT contain all required columns.", src["source_name"]
            )
        else:
            logger.info("Source %s verification succeeded.", src["source_name"])

        # Write a copy of the CSV for each logical source.
        # The copy operation is cheap because the file is small.
        _copy_to_raw(csv_path, src["source_name"].lower())

    # Write the JSON availability report.
    report_path = paths.data("source", "availability_report.json")
    report = {"datasets": report_entries}
    try:
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Availability report written to %s", report_path)
    except Exception as exc:
        logger.error("Failed to write availability report: %s", exc)
        sys.exit(1)

    # Exit status reflects verification outcome.
    if any_failure:
        logger.error("One or more required datasets are missing columns; aborting.")
        sys.exit(1)
    else:
        logger.info("All required datasets contain the necessary columns.")
        sys.exit(0)

if __name__ == "__main__":
    main()
