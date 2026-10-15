"""Input validation and provenance check for the PPMI microbiome pipeline.

Validates that the researcher‑supplied raw inputs exist and parse:
  - data/raw/ppmi_asv.csv        (sample_id, patient_id, visit_date, taxon columns, preprocessed)
  - data/raw/ppmi_clinical.parquet (patient_id, visit_date, age, sex,
                                    levodopa_eq_dose, MDS_UPDRS_Total)

Behavior (FR‑001, FR‑004 graceful degradation):
  - Missing or malformed input file  -> abort with a clear error (exit non‑zero).
  - Missing MDS_UPDRS_Total column   -> log a warning, exit zero, and record a
    skip flag so downstream slope/correlation/LME steps are skipped.
  - ASV table must contain a column ``preprocessed`` with value ``True`` for every row,
    indicating the data passed the PPMI QC pipeline. Failure aborts with a clear error.
This module NEVER falls back to synthetic or placeholder data.

Runnable as:  python -m code.src.pipeline.ingest
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Primary expected filenames (historical PPMI naming)
ASV_FILENAME_PPMI = "ppmi_asv.csv"
CLINICAL_FILENAME_PPMI = "ppmi_clinical.parquet"

# Alternate open‑dataset filenames (used in quickstart)
ASV_FILENAME_OPEN = "open_asv.csv"
CLINICAL_FILENAME_OPEN = "open_clinical.parquet"

ASV_REQUIRED_COLUMNS = ["sample_id", "patient_id", "visit_date"]
CLINICAL_REQUIRED_COLUMNS = [
    "patient_id",
    "visit_date",
    "age",
    "sex",
    "levodopa_eq_dose",
]
OUTCOME_COLUMN = "MDS_UPDRS_Total"
PREPROCESSED_COLUMN = "preprocessed"


def _fail(message: str) -> None:
    """Abort loudly with a descriptive error. Never substitutes fake data."""
    log.error(message)
    raise FileNotFoundError(message)


def _choose_path(
    primary: str, alternate: str, description: str
) -> Path:
    """
    Resolve a raw data file path.

    Preference order:
      1. User‑supplied explicit path (handled upstream).
      2. ``data/raw/<primary>`` if it exists.
      3. ``data/raw/<alternate>`` if it exists.
    If neither exists, raise a FileNotFoundError with a helpful message.
    """
    primary_path = paths.data("raw", primary)
    alternate_path = paths.data("raw", alternate)

    if primary_path.is_file():
        log.info("%s found at expected PPMI location: %s", description, primary_path)
        return primary_path
    if alternate_path.is_file():
        log.info(
            "%s not found at PPMI name; using alternate open‑dataset name: %s",
            description,
            alternate_path,
        )
        return alternate_path

    _fail(
        f"Required input file not found: neither {primary_path} nor {alternate_path} exist. "
        f"Place the researcher‑supplied {description.lower()} at one of these locations."
    )
    # Unreachable
    return primary_path


def _checksum(path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_asv(path: Path) -> Dict[str, Any]:
    """Validate the ASV count table. Raises on missing/malformed input."""
    if not path.is_file():
        _fail(
            f"Required input file not found: {path}. Place the researcher‑supplied "
            f"ASV table at data/raw/{ASV_FILENAME_PPMI} (or {ASV_FILENAME_OPEN}) "
            f"(columns: {ASV_REQUIRED_COLUMNS + ['<taxon count columns>', PREPROCESSED_COLUMN]}). The pipeline "
            "does not generate synthetic data."
        )
    try:
        asv = pd.read_csv(path)
    except Exception as exc:  # malformed CSV
        _fail(f"Malformed ASV file {path}: could not parse as CSV ({exc}).")
    missing = [c for c in ASV_REQUIRED_COLUMNS if c not in asv.columns]
    if missing:
        _fail(
            f"Malformed ASV file {path}: missing required column(s) {missing}. "
            f"Found columns: {list(asv.columns)}."
        )
    # Verify the provenance flag column
    if PREPROCESSED_COLUMN not in asv.columns:
        _fail(
            f"Malformed ASV file {path}: required provenance column '{PREPROCESSED_COLUMN}' is missing."
        )
    # All rows must have True in the preprocessed flag
    if not asv[PREPROCESSED_COLUMN].astype(bool).all():
        _fail(
            f"Provenance check failed for {path}: column '{PREPROCESSED_COLUMN}' must be True for all rows."
        )
    taxon_columns = [
        c for c in asv.columns if c not in ASV_REQUIRED_COLUMNS + [PREPROCESSED_COLUMN]
    ]
    if not taxon_columns:
        _fail(
            f"Malformed ASV file {path}: no taxon count columns found beyond "
            f"{ASV_REQUIRED_COLUMNS + [PREPROCESSED_COLUMN]}."
        )
    if len(asv) == 0:
        _fail(f"Malformed ASV file {path}: contains zero rows.")
    dates = pd.to_datetime(asv["visit_date"], errors="coerce")
    if dates.isna().all():
        _fail(
            f"Malformed ASV file {path}: 'visit_date' column could not be "
            "parsed as dates."
        )
    log.info(
        "ASV table OK: %d rows, %d columns (%d taxon columns)",
        len(asv), asv.shape[1], len(taxon_columns),
    )
    return {
        "rows": int(len(asv)),
        "columns": int(asv.shape[1]),
        "taxon_columns": int(len(taxon_columns)),
    }


def _validate_clinical(path: Path) -> Dict[str, Any]:
    """Validate the clinical metadata table. Raises on missing/malformed input."""
    if not path.is_file():
        _fail(
            f"Required input file not found: {path}. Place the researcher‑supplied "
            f"clinical metadata at data/raw/{CLINICAL_FILENAME_PPMI} (or {CLINICAL_FILENAME_OPEN}) "
            f"(columns: {CLINICAL_REQUIRED_COLUMNS + [OUTCOME_COLUMN]}). The pipeline "
            "does not generate synthetic data."
        )
    try:
        clinical = pd.read_parquet(path)
    except Exception as exc:
        _fail(
            f"Malformed clinical file {path}: could not parse as Parquet ({exc})."
        )
    missing = [
        c for c in CLINICAL_REQUIRED_COLUMNS if c not in clinical.columns
    ]
    if missing:
        _fail(
            f"Malformed clinical file {path}: missing required column(s) "
            f"{missing}. Found columns: {list(clinical.columns)}."
        )
    if len(clinical) == 0:
        _fail(f"Malformed clinical file {path}: contains zero rows.")
    dates = pd.to_datetime(clinical["visit_date"], errors="coerce")
    if dates.isna().all():
        _fail(
            f"Malformed clinical file {path}: 'visit_date' column could not be "
            "parsed as dates."
        )
    outcome_present = OUTCOME_COLUMN in clinical.columns
    if outcome_present:
        log.info(
            "Clinical table OK: %d rows, %d columns; outcome column "
            "'%s' IS present.",
            len(clinical), clinical.shape[1], OUTCOME_COLUMN,
        )
    else:
        log.warning(
            "Clinical table parsed (%d rows, %d columns) but the outcome column "
            "'%s' is ABSENT. Per FR-004 graceful degradation the slope, "
            "correlation, and mixed‑effects steps will be SKIPPED with a "
            "warning. The pipeline does not abort.",
            len(clinical), clinical.shape[1], OUTCOME_COLUMN,
        )
    return {
        "rows": int(len(clinical)),
        "columns": int(clinical.shape[1]),
        "outcome_column_present": outcome_present,
    }


def validate_inputs(
    asv_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Validate both raw inputs and return a report dict.

    Raises FileNotFoundError if any input file is missing or malformed.
    The returned dict carries row/column counts, whether the
    MDS_UPDRS_Total outcome column is present, and downstream skip flags.
    """
    # Resolve default locations if caller did not supply explicit paths
    if asv_path is None:
        asv_path = _choose_path(
            ASV_FILENAME_PPMI, ASV_FILENAME_OPEN, "ASV table"
        )
    if clinical_path is None:
        clinical_path = _choose_path(
            CLINICAL_FILENAME_PPMI, CLINICAL_FILENAME_OPEN, "clinical metadata"
        )

    asv_report = _validate_asv(Path(asv_path))
    clinical_report = _validate_clinical(Path(clinical_path))

    outcome_present = clinical_report["outcome_column_present"]
    report = {
        "asv_path": str(asv_path),
        "clinical_path": str(clinical_path),
        "asv": asv_report,
        "clinical": clinical_report,
        "outcome_column": OUTCOME_COLUMN,
        "outcome_column_present": outcome_present,
        "skip_slope_and_correlation": not outcome_present,
        "skip_mixed_effects": not outcome_present,
        "synthetic_fallback_used": False,
        # Checksums for provenance
        "asv_checksum_sha256": _checksum(Path(asv_path)),
        "clinical_checksum_sha256": _checksum(Path(clinical_path)),
    }
    return report


def write_validation_report(report: Dict[str, Any], out_path: Optional[Path] = None) -> Path:
    """Persist the validation/skip-flag record next to the raw inputs."""
    if out_path is None:
        out_path = paths.data("raw", "ingest_validation.json")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    log.info("Validation report written to %s", out_path)
    return out_path


def write_provenance(report: Dict[str, Any], out_path: Optional[Path] = None) -> Path:
    """
    Write a simple provenance JSON containing the SHA‑256 hashes of the two
    raw input files. The file is stored under a project‑owned location
    (``data/processed/ingest_provenance.json``) to avoid writing into the
    platform‑owned ``state/`` directory.
    """
    if out_path is None:
        out_path = paths.data("processed", "ingest_provenance.json")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    provenance = {
        "asv_sha256": report.get("asv_checksum_sha256"),
        "clinical_sha256": report.get("clinical_checksum_sha256"),
    }
    out_path.write_text(json.dumps(provenance, indent=2))
    log.info("Provenance file written to %s", out_path)
    return out_path


def _copy_to_default(
    src: Path, default_name: str
) -> None:
    """
    Ensure that downstream pipeline stages that expect the historic
    PPMI filenames can find the data. If the source file is an
    alternate (open_*) name, copy it to the default PPMI location.
    """
    dest = paths.data("raw", default_name)
    if src.resolve() != dest.resolve():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        log.info("Copied %s to default location %s for downstream compatibility.", src, dest)


def main(
    asv_path: Optional[Path] = None,
    clinical_path: Optional[Path] = None,
    report_path: Optional[Path] = None,
) -> int:
    """Entry point: validate inputs, log a report, write the skip‑flag file.

    Returns exit code 0 on success (including the missing‑outcome‑column
    graceful‑degradation case); raises (non‑zero exit) only when an input
    file is missing or malformed.
    """
    log.info("=== PPMI input validation (FR-001) ===")
    report = validate_inputs(asv_path, clinical_path)
    write_validation_report(report, report_path)

    # Write provenance (hashes) to a project‑owned location.
    write_provenance(report)

    # Make sure downstream stages see the expected filenames.
    # This is a no‑op if the user already placed files using the PPMI names.
    _copy_to_default(Path(report["asv_path"]), ASV_FILENAME_PPMI)
    _copy_to_default(Path(report["clinical_path"]), CLINICAL_FILENAME_PPMI)

    if report["outcome_column_present"]:
        log.info(
            "Outcome column '%s' present: slope, correlation, and LME steps "
            "will run.", OUTCOME_COLUMN,
        )
    else:
        log.warning(
            "SKIP FLAG SET: slope/correlation and mixed‑effects steps are "
            "marked to be skipped because '%s' is absent.", OUTCOME_COLUMN,
        )
    log.info("Input validation completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileNotFoundError as exc:
        log.error("Input validation FAILED: %s", exc)
        sys.exit(1)