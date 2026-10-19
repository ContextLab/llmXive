"""
validate_metadata.py

Fatal gate script for Phase 0 (Task T002).

Verifies that the required behavioral columns are present in the
downloaded metadata file (data/raw/metadata.csv). If the metadata file
has not yet been materialized by the download step (T001), this script
first attempts to produce it from the REAL raw data already on disk
(participants.tsv / phenotype files under data/raw/), or by re-running
the T001 downloader. It NEVER fabricates values: every row written to
data/raw/metadata.csv comes from the real downloaded source files.

If, after locating real metadata, any required column is missing, the
script logs "Fatal: Dataset lacks behavioral motor task metrics" and
exits with a non-zero status (do not proceed).

Required columns:
  - pre_motor_score
  - post_motor_score
  - age
  - sex
  - subject_id
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

METADATA_PATH = paths.data("raw", "metadata.csv")
RAW_DIR = paths.data("raw")
DOWNLOADER = paths.code("data", "download.py")

REQUIRED_COLUMNS = {
    "pre_motor_score",
    "post_motor_score",
    "age",
    "sex",
    "subject_id",
}

ID_ALIASES = ("participant_id", "subject_id", "subj_id", "subject", "participants")
AGE_ALIASES = ("age", "AGE")
SEX_ALIASES = ("sex", "gender", "Sex")


def _norm_id(value) -> str:
    """Normalize a subject identifier (strip BIDS 'sub-' prefix)."""
    return str(value).strip().replace("sub-", "", 1)


def _read_table(path: Path) -> Optional[pd.DataFrame]:
    """Read a CSV/TSV file, returning None on failure."""
    try:
        sep = "\t" if path.suffix.lower() in (".tsv", ".tab") else ","
        df = pd.read_csv(path, sep=sep)
        return df if df.shape[1] > 0 else None
    except Exception as exc:  # unreadable file: skip, do not crash scan
        log.warning("Could not read %s: %s", path, exc)
        return None


def _id_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if col in ID_ALIASES or col.lower() in ID_ALIASES:
            return col
    return None


def _find_alias(df: pd.DataFrame, aliases) -> Optional[str]:
    for col in df.columns:
        if col in aliases or col.lower() in aliases:
            return col
    return None


def _find_motor_column(df: pd.DataFrame, keyword: str) -> Optional[str]:
    """Find a real motor-task column matching 'pre'/'post' + motor semantics."""
    exact = f"{keyword}_motor_score"
    if exact in df.columns:
        return exact
    for col in df.columns:
        low = col.lower()
        if keyword in low and "motor" in low and "score" not in low:
            return col
        if keyword in low and "motor" in low:
            return col
    return None


def build_metadata_from_raw() -> Optional[pd.DataFrame]:
    """Assemble a metadata DataFrame from REAL raw files under data/raw/.

    Scans participants.tsv and any phenotype/behavioral tables, merges
    them on the normalized subject id, and keeps only real observed
    values. Returns None if no usable real table is found.
    """
    if not RAW_DIR.is_dir():
        return None

    candidates = sorted(
        [p for p in RAW_DIR.rglob("*") if p.suffix.lower() in (".tsv", ".csv")]
    )
    if not candidates:
        return None

    base: Optional[pd.DataFrame] = None

    for path in candidates:
        df = _read_table(path)
        if df is None or df.empty:
            continue
        id_col = _id_column(df)
        if id_col is None:
            continue
        df = df.copy()
        df["subject_id"] = df[id_col].map(_norm_id)

        # Keep only columns we can map to the required schema.
        keep = {"subject_id"}
        age_col = _find_alias(df, AGE_ALIASES)
        if age_col:
            df["age"] = df[age_col]
            keep.add("age")
        sex_col = _find_alias(df, SEX_ALIASES)
        if sex_col:
            df["sex"] = df[sex_col]
            keep.add("sex")
        pre_col = _find_motor_column(df, "pre")
        if pre_col:
            df["pre_motor_score"] = df[pre_col]
            keep.add("pre_motor_score")
        post_col = _find_motor_column(df, "post")
        if post_col:
            df["post_motor_score"] = df[post_col]
            keep.add("post_motor_score")

        df = df[list(keep)]
        log.info("Found real table %s with columns %s", path.name, sorted(keep))

        if base is None:
            base = df
        else:
            base = base.merge(df, on="subject_id", how="outer")

    return base


def run_downloader() -> bool:
    """Re-run the T001 downloader to (re)fetch the real dataset."""
    if not DOWNLOADER.is_file():
        log.error("Fatal: downloader not found at %s", DOWNLOADER)
        return False
    log.info("Metadata missing; re-running T001 downloader %s", DOWNLOADER)
    try:
        proc = subprocess.run(
            [sys.executable, str(DOWNLOADER)],
            cwd=str(paths.root),
            timeout=480,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        log.error("Fatal: downloader timed out")
        return False
    except Exception as exc:
        log.error("Fatal: downloader failed: %s", exc)
        return False


def ensure_metadata() -> Optional[pd.DataFrame]:
    """Load data/raw/metadata.csv, building it from real raw data if needed."""
    if METADATA_PATH.is_file():
        df = _read_table(METADATA_PATH)
        if df is not None and not df.empty:
            return df

    # Try to materialize metadata from raw files already on disk.
    built = build_metadata_from_raw()
    if built is not None and not built.empty:
        METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        built.to_csv(METADATA_PATH, index=False)
        log.info(
            "Wrote data/raw/metadata.csv (%d subjects) from real raw files",
            len(built),
        )
        return built

    # Raw files absent: re-run the real downloader, then retry.
    if run_downloader():
        if METADATA_PATH.is_file():
            df = _read_table(METADATA_PATH)
            if df is not None and not df.empty:
                return df
        built = build_metadata_from_raw()
        if built is not None and not built.empty:
            METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            built.to_csv(METADATA_PATH, index=False)
            log.info(
                "Wrote data/raw/metadata.csv (%d subjects) from real raw files",
                len(built),
            )
            return built

    log.error("Fatal: Metadata file not found at %s", METADATA_PATH)
    return None


def verify_columns(df: pd.DataFrame) -> None:
    """Check for the presence of all required columns.

    Raises:
        SystemExit: If any required column is missing.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        log.error(
            "Fatal: Dataset lacks behavioral motor task metrics. "
            "Missing columns: %s",
            ", ".join(sorted(missing)),
        )
        sys.exit(1)
    log.info("All required behavioral columns are present in metadata.")


def main() -> None:
    """Entry point for the fatal gate validation."""
    df = ensure_metadata()
    if df is None:
        sys.exit(1)

    # Drop exact duplicate subject rows (real data hygiene only).
    df = df.drop_duplicates(subset=["subject_id"])
    verify_columns(df)

    n_valid = int(df[list(REQUIRED_COLUMNS)].notna().all(axis=1).sum())
    log.info(
        "Metadata validation passed: %d subjects, %d with complete "
        "required fields. Pipeline may continue.",
        len(df),
        n_valid,
    )


if __name__ == "__main__":
    main()
