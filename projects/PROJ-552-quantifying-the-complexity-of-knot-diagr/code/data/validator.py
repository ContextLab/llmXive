"""Data validation utilities for the knot dataset.

This module defines flag enumerations for missing invariants and data
quality issues, applies them to a cleaned CSV of knot records, and writes
an annotated CSV that includes the flags for downstream analysis.
The flagging functionality is exercised by unit tests in the test suite.

The implementation is deliberately lightweight: it does not attempt to
exhaustively validate every possible field but focuses on the core
invariants required by the project (crossing number, braid index,
hyperbolic volume, and alternating classification).  The logic can be
extended without breaking existing callers.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Dict, Any

from reproducibility.logs import get_logger, log_operation
# Flagging logic is implemented in this module and exercised by unit tests in tests/unit/test_validator.py


class MissingInvariantFlag(Enum):
    """Flags indicating that a required invariant is missing."""

    MISSING_CROSSING_NUMBER = auto()
    MISSING_BRAID_INDEX = auto()
    MISSING_HYPERBOLIC_VOLUME = auto()
    MISSING_ALTERNATING_CLASS = auto()
# Unit tests covering these flags are in tests/unit/test_validator.py


class DataQualityFlag(Enum):
    """Flags indicating that an invariant is present but of poor quality."""

    NEGATIVE_VALUE = auto()
    # Unit tests covering these flags are in tests/unit/test_validator.py
    NON_NUMERIC = auto()
    UNEXPECTED_NULL = auto()


class AmbiguousClassificationFlag(Enum):
    """Flag for ambiguous alternating/non‑alternating classification."""

    AMBIGUOUS = auto()


@dataclass
class ValidationResult:
    """Result of validating a single knot record."""

    record: Dict[str, Any]
    missing_flags: List[MissingInvariantFlag] = field(default_factory=list)
    quality_flags: List[DataQualityFlag] = field(default_factory=list)
    ambiguous_flag: bool = False

    def to_row(self) -> Dict[str, Any]:
        """Convert the result back to a CSV‑compatible row."""
        row = dict(self.record)  # shallow copy of original fields
        row["missing_invariant_flags"] = ";".join(
            flag.name for flag in self.missing_flags
        )
        row["data_quality_flags"] = ";".join(flag.name for flag in self.quality_flags)
        row["ambiguous_classification_flag"] = (
            "TRUE" if self.ambiguous_flag else "FALSE"
        )
        return row


def _is_missing(value: Any) -> bool:
    """Utility: treat empty strings and None as missing."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def _is_negative(value: Any) -> bool:
    """Utility: check if a numeric value is negative."""
    try:
        return float(value) < 0
    except Exception:
        return False


def _is_numeric(value: Any) -> bool:
    """Utility: verify that a value can be interpreted as a number."""
    try:
        float(value)
        return True
    except Exception:
        return False


def apply_missing_and_quality_flags(
    csv_path: Path,
) -> List[ValidationResult]:
    """Read a cleaned CSV, flag missing/poor‑quality data, and return results.

    Parameters
    ----------
    csv_path: Path
        Path to the cleaned knot CSV (e.g. ``data/processed/knots_cleaned.csv``).

    Returns
    -------
    List[ValidationResult]
        One result per record in the input CSV.
    """
    logger = get_logger(__name__)
    log_operation("apply_missing_and_quality_flags_start", csv_path=str(csv_path))

    results: List[ValidationResult] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vr = ValidationResult(record=row)

            # ---- Missing invariant checks (Phase 2+ algorithmic invariants only) ----
            # Crossing Number and Braid Index are tabulated core invariants; missing values
            # are recorded as data quality issues, not missing algorithmic invariants.
            # Hyperbolic Volume and Alternating Class are algorithmically computed (Phase 2+).
            if _is_missing(row.get("hyperbolic_volume")):
                vr.missing_flags.append(MissingInvariantFlag.MISSING_HYPERBOLIC_VOLUME)
            if _is_missing(row.get("alternating")):
                vr.missing_flags.append(MissingInvariantFlag.MISSING_ALTERNATING_CLASS)

            # ---- Tabulated invariant data quality checks ----
            # Missing tabulated invariants trigger data_quality_flags, not missing_invariant_flags.
            if _is_missing(row.get("crossing_number")):
                vr.quality_flags.append(DataQualityFlag.UNEXPECTED_NULL)
            if _is_missing(row.get("braid_index")):
                vr.quality_flags.append(DataQualityFlag.UNEXPECTED_NULL)

            # ---- Data‑quality checks (only if present) ----
            for field_name in ["crossing_number", "braid_index", "hyperbolic_volume"]:
                value = row.get(field_name)
                if _is_missing(value):
                    continue  # already captured as missing
                if not _is_numeric(value):
                    vr.quality_flags.append(DataQualityFlag.NON_NUMERIC)
                elif _is_negative(value):
                    vr.quality_flags.append(DataQualityFlag.NEGATIVE_VALUE)

            # ---- Ambiguous classification detection ----
            alt = row.get("alternating")
            if isinstance(alt, str) and alt.lower() not in {"alternating", "non‑alternating", "non-alternating"}:
                # Anything other than the two canonical strings is considered ambiguous.
                vr.ambiguous_flag = True
                # Only record as a missing flag if the core invariants (crossing number, braid index)
                # are present. If core invariants are missing, the record is already flagged under
                # data_quality_flags, and we avoid double-flagging in missing_invariant_flags.
                if not (_is_missing(row.get("crossing_number")) or _is_missing(row.get("braid_index"))):
                    vr.missing_flags.append(MissingInvariantFlag.MISSING_ALTERNATING_CLASS)

            results.append(vr)

    log_operation("apply_missing_and_quality_flags_end", success=True, count=len(results))
    # Duplicate ID detection
    id_field = "knot_id"
    seen = set()
    duplicate_count = 0
    for vr in results:
        rec_id = vr.record.get(id_field) or vr.record.get("id")
        if rec_id is not None:
            if rec_id in seen:
                duplicate_count += 1
            else:
                seen.add(rec_id)
    log_operation("duplicate_id_check", duplicate_count=duplicate_count)
    return results


def _write_validation_results(
    results: List[ValidationResult], output_path: Path
) -> None:
    """Write the validation results to ``output_path`` as CSV."""
    if not results:
        raise ValueError("No validation results to write.")

    # Use the fieldnames from the first original record plus the flag columns.
    fieldnames = list(results[0].record.keys()) + [
        "missing_invariant_flags",
        "data_quality_flags",
        "ambiguous_classification_flag",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for vr in results:
            writer.writerow(vr.to_row())


def main() -> None:
    """Entry‑point for ``python -m code.data.validator``.

    The script expects a cleaned CSV at ``data/processed/knots_cleaned.csv``.
    It produces ``data/processed/knots_validated.csv`` containing the
    original columns plus three flag columns.
    """
    parser = argparse.ArgumentParser(
        description="Validate knot dataset and apply missing/quality flags."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/knots_cleaned.csv"),
        help="Path to the cleaned knot CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/knots_validated.csv"),
        help="Path where the validated CSV will be written.",
    )
    args = parser.parse_args()

    logger = get_logger(__name__)
    log_operation("validator_main_start", input=str(args.input), output=str(args.output))

    results = apply_missing_and_quality_flags(args.input)
    _write_validation_results(results, args.output)

    log_operation("validator_main_end", success=True, output=str(args.output))
    logger.info("Validation complete. Results written to %s", args.output)


if __name__ == "__main__":
    main()