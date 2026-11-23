"""
Real‑data ingestion script for the “Impact of Musical Training on Functional Connectivity” project.

This script reads the environment variable ``REAL_DATA_SOURCE`` (must be set to ``OPENNEURO``)
and attempts to download a minimal but real subset of the OpenNeuro dataset *ds001734*.
If the environment variable is missing, set to an unsupported value, or the download fails,
the script **does not abort with an error code**. Instead it prints a clear
“Data source unavailable” message, writes a JSON status file indicating unavailability,
and exits with status 0 – satisfying the task requirement of no synthetic fallback.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
import requests

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
SUPPORTED_SOURCES = {"OPENNEURO"}  # only OpenNeuro is currently supported

OPENNEURO_DATASET_ID = "ds001734"
PARTICIPANTS_URL = (
    f"https://openneuro.org/crn/datasets/{OPENNEURO_DATASET_ID}"
    f"/snapshots/latest/files/participants.tsv?download"
)

# Output locations (created via llmxive_toolkit helpers)
SUBJECTS_PARQUET_PATH = paths.processed("subjects.parquet")
LOG_PATH = paths.logs("real_ingest.log")
STATUS_JSON_PATH = paths.logs("real_ingest_status.json")

def _write_status(success: bool, message: str) -> None:
    """Write a JSON status file indicating success or failure."""
    status = {
        "status": "available" if success else "unavailable",
        "message": message,
        "timestamp": pd.Timestamp.utcnow().isoformat(),
    }
    STATUS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STATUS_JSON_PATH.open("w") as f:
        json.dump(status, f, indent=2)
    log.info(f"Status JSON written to {STATUS_JSON_PATH}")

def _download_file(url: str, dest_path: Path) -> None:
    """Stream‑download a file from ``url`` to ``dest_path``."""
    log.info(f"Starting download from {url}")
    response = requests.get(url, stream=True, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download file. HTTP status: {response.status_code}"
        )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    with dest_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            f.write(chunk)
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    log.info(f"Download completed. SHA‑256: {checksum}")

def _load_participants_tsv(tsv_path: Path) -> pd.DataFrame:
    """Load the OpenNeuro participants.tsv file into a DataFrame."""
    try:
        df = pd.read_csv(tsv_path, sep="\t")
        log.info(f"Loaded participants TSV with {len(df)} rows")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to parse participants TSV: {e}")

def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert raw OpenNeuro columns into the canonical schema required downstream."""
    def _col(name):
        return df[name] if name in df.columns else pd.Series([pd.NA] * len(df))

    # 1. subject_id – derived from ``participant_id`` (e.g., sub-01 → 01)
    subject_id = _col("participant_id").astype(str).str.replace("^sub-", "", regex=True)

    # 2. years_of_training – look for plausible columns
    if "music_training" in df.columns:
        years = pd.to_numeric(_col("music_training"), errors="coerce")
    elif "music_years" in df.columns:
        years = pd.to_numeric(_col("music_years"), errors="coerce")
    else:
        years = pd.Series([pd.NA] * len(df))
        log.warning("No 'music_training' column found; years_of_training will be NaN.")

    # 3. group – musician if years >= 1
    group = pd.Series(["non_musician"] * len(df))
    group[years >= 1] = "musician"

    # 4. age – ensure numeric
    age = pd.to_numeric(_col("age"), errors="coerce")

    # 5. sex – standardise to M/F
    sex_raw = _col("sex").astype(str).str.lower()
    sex = pd.Series(["U"] * len(df))  # Unknown default
    sex[sex_raw.isin(["m", "male"])] = "M"
    sex[sex_raw.isin(["f", "female"])] = "F"

    # 6. motion_score – use ``mean_fd`` if present
    if "mean_fd" in df.columns:
        motion = pd.to_numeric(_col("mean_fd"), errors="coerce").fillna(0.0)
    else:
        motion = pd.Series([0.0] * len(df))
        log.warning("No 'mean_fd' column found; motion_score set to 0.0 for all subjects.")

    # 7. ses_score – use ``ses`` if present
    if "ses" in df.columns:
        ses = pd.to_numeric(_col("ses"), errors="coerce").fillna(0.0)
    else:
        ses = pd.Series([0.0] * len(df))
        log.warning("No 'ses' column found; ses_score set to 0.0 for all subjects.")

    out_df = pd.DataFrame({
        "subject_id": subject_id,
        "group": group,
        "years_of_training": years,
        "age": age,
        "sex": sex,
        "motion_score": motion,
        "ses_score": ses,
    })
    out_df.dropna(subset=["subject_id"], inplace=True)
    return out_df

def _write_subjects_parquet(df: pd.DataFrame) -> None:
    """Write the canonical subject table to the expected parquet location."""
    SUBJECTS_PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SUBJECTS_PARQUET_PATH, index=False)
    log.info(f"Wrote subjects parquet to {SUBJECTS_PARQUET_PATH}")

def main() -> int:
    """
    Entry‑point for the real‑data ingestion script.
    Always exits with status 0, printing a clear message and writing a status JSON.
    """
    # ------------------------------------------------------------------
    # 1️⃣ Environment validation
    # ------------------------------------------------------------------
    data_source = os.getenv("REAL_DATA_SOURCE")
    if not data_source:
        msg = "Data source unavailable: REAL_DATA_SOURCE environment variable not set."
        print(msg, file=sys.stderr)
        log.error(msg)
        _write_status(False, msg)
        # According to the task requirements we exit with 0 even when unavailable
        return 0

    data_source = data_source.strip().upper()
    if data_source not in SUPPORTED_SOURCES:
        msg = (
            f"Data source unavailable: unsupported source '{data_source}'. "
            f"Supported sources: {', '.join(SUPPORTED_SOURCES)}."
        )
        print(msg, file=sys.stderr)
        log.error(msg)
        _write_status(False, msg)
        return 0

    # ------------------------------------------------------------------
    # 2️⃣ Attempt to download participants metadata
    # ------------------------------------------------------------------
    try:
        tmp_dir = Path("data/tmp_real_ingest")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        participants_path = tmp_dir / "participants.tsv"
        _download_file(PARTICIPANTS_URL, participants_path)
    except Exception as e:
        msg = f"Data source unavailable: failed to download participants file – {e}"
        print(msg, file=sys.stderr)
        log.error(msg)
        _write_status(False, msg)
        return 0

    # ------------------------------------------------------------------
    # 3️⃣ Load and standardise the table
    # ------------------------------------------------------------------
    try:
        raw_df = _load_participants_tsv(participants_path)
        subjects_df = _standardise_columns(raw_df)

        if len(subjects_df) < 100:
            msg = f"Data source unavailable: insufficient subjects ({len(subjects_df)})."
            print(msg, file=sys.stderr)
            log.error(msg)
            _write_status(False, msg)
            return 0
    except Exception as e:
        msg = f"Data source unavailable: error processing TSV – {e}"
        print(msg, file=sys.stderr)
        log.error(msg)
        _write_status(False, msg)
        return 0

    # ------------------------------------------------------------------
    # 4️⃣ Persist results
    # ------------------------------------------------------------------
    try:
        _write_subjects_parquet(subjects_df)
        _write_status(True, "Real data ingestion completed successfully.")
    except Exception as e:
        msg = f"Data source unavailable: failed to write outputs – {e}"
        print(msg, file=sys.stderr)
        log.error(msg)
        _write_status(False, msg)
        return 0

    # Cleanup temporary files (non‑critical)
    try:
        participants_path.unlink()
        tmp_dir.rmdir()
    except Exception:
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
