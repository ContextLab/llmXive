"""
Validator module for knot dataset quality and missing invariant flags.

This module defines:
  - MissingInvariantFlag: flags for missing core invariants.
  - DataQualityFlag: flags for malformed core invariant values.
  - ValidationResult: dataclass aggregating per‑record flags and a summary.
  - apply_missing_and_quality_flags: core function that reads a cleaned CSV,
    annotates each record with the appropriate flags, and writes a JSON report.
  - validate_dataset_data_quality: thin wrapper used by downstream scripts.
  - main: CLI entry point compatible with the historic usage pattern
    ``python -m code.data.validator <input_csv> <output_json>``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict, field
from enum import Enum, auto
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

# ----------------------------------------------------------------------
# Flag enumerations
# ----------------------------------------------------------------------


class MissingInvariantFlag(Enum):
    """Flags indicating a required invariant is missing."""

    MISSING_CROSSING_NUMBER = auto()
    MISSING_BRAID_INDEX = auto()
    MISSING_HYPERBOLIC_VOLUME = auto()

    def __str__(self) -> str:
        return self.name


class DataQualityFlag(Enum):
    """Flags indicating a required invariant cannot be parsed correctly."""

    INVALID_CROSSING_NUMBER = auto()
    INVALID_BRAID_INDEX = auto()
    INVALID_HYPERBOLIC_VOLUME = auto()

    def __str__(self) -> str:
        return self.name


# ----------------------------------------------------------------------
# Result container
# ----------------------------------------------------------------------


@dataclass
class ValidationResult:
    """
    Holds the validation outcome for a dataset.

    Attributes
    ----------
    records : List[Dict[str, Any]]
        Each record is the original CSV row enriched with a ``flags`` key
        (list of flag names as strings).
    summary : Dict[str, int]
        Simple aggregated counts of each flag type across the whole dataset.
    """

    records: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize the validation result to a pretty‑printed JSON string."""
        return json.dumps(
            {"records": self.records, "summary": self.summary}, indent=2, ensure_ascii=False
        )


# ----------------------------------------------------------------------
# Core validation logic
# ----------------------------------------------------------------------


def _detect_missing_flags(row: pd.Series) -> List[MissingInvariantFlag]:
    """Return a list of MissingInvariantFlag for fields that are NaN/empty."""
    flags: List[MissingInvariantFlag] = []
    if pd.isna(row.get("crossing_number")):
        flags.append(MissingInvariantFlag.MISSING_CROSSING_NUMBER)
    if pd.isna(row.get("braid_index")):
        flags.append(MissingInvariantFlag.MISSING_BRAID_INDEX)
    if pd.isna(row.get("volume")):
        flags.append(MissingInvariantFlag.MISSING_HYPERBOLIC_VOLUME)
    return flags


def _detect_quality_flags(row: pd.Series) -> List[DataQualityFlag]:
    """Return a list of DataQualityFlag for fields that cannot be parsed."""
    flags: List[DataQualityFlag] = []
    # crossing_number should be an integer
    cn = row.get("crossing_number")
    if not pd.isna(cn):
        try:
            int(cn)
        except (ValueError, TypeError):
            flags.append(DataQualityFlag.INVALID_CROSSING_NUMBER)

    # braid_index should be an integer
    bi = row.get("braid_index")
    if not pd.isna(bi):
        try:
            int(bi)
        except (ValueError, TypeError):
            flags.append(DataQualityFlag.INVALID_BRAID_INDEX)

    # hyperbolic volume should be a float (if present)
    vol = row.get("volume")
    if not pd.isna(vol):
        try:
            float(vol)
        except (ValueError, TypeError):
            flags.append(DataQualityFlag.INVALID_HYPERBOLIC_VOLUME)

    return flags


def apply_missing_and_quality_flags(
    input_csv: Path, output_json: Path
) -> ValidationResult:
    """
    Apply missing‑invariant and data‑quality flags to a cleaned knots CSV.

    Parameters
    ----------
    input_csv : Path
        Path to ``data/processed/knots_cleaned.csv`` (or any CSV with the
        required columns).
    output_json : Path
        Destination path for the JSON report (e.g. ``data/processed/validation_flags.json``).

    Returns
    -------
    ValidationResult
        Object containing per‑record flags and an aggregated summary.
    """
    # Load the CSV; we use dtype=str to avoid premature conversion.
    df = pd.read_csv(input_csv, dtype=str)

    result = ValidationResult()
    summary_counter: Dict[str, int] = {}

    for _, row in df.iterrows():
        record = row.to_dict()
        # Detect flags
        missing = _detect_missing_flags(row)
        quality = _detect_quality_flags(row)

        # Combine and convert to string representations for JSON friendliness
        all_flags = [str(f) for f in missing + quality]
        record["flags"] = all_flags
        result.records.append(record)

        # Update summary counts
        for f in all_flags:
            summary_counter[f] = summary_counter.get(f, 0) + 1

    result.summary = summary_counter

    # Ensure parent directory exists
    output_json.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    with output_json.open("w", encoding="utf-8") as f:
        f.write(result.to_json())

    return result


# ----------------------------------------------------------------------
# Compatibility wrapper (historical name used by downstream scripts)
# ----------------------------------------------------------------------


def validate_dataset_data_quality(input_csv: Path, output_json: Path) -> ValidationResult:
    """
    Back‑compatible wrapper kept for scripts that imported
    ``validate_dataset_data_quality`` directly.

    It simply forwards to :func:`apply_missing_and_quality_flags`.
    """
    return apply_missing_and_quality_flags(input_csv, output_json)


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate knot dataset for missing invariants and data quality issues."
    )
    parser.add_argument(
        "input_csv",
        nargs="?",
        default=str(Path("data") / "processed" / "knots_cleaned.csv"),
        help="Path to the cleaned knots CSV file.",
    )
    parser.add_argument(
        "output_json",
        nargs="?",
        default=str(
            Path("data") / "processed" / "validation_flags.json"
        ),
        help="Path where the JSON validation report will be written.",
    )
    return parser.parse_args()


def main() -> None:
    """
    Execute the validator from the command line.

    The historic usage pattern accepted two positional arguments.
    For backward compatibility we also support being invoked without arguments,
    in which case the default locations under ``data/processed`` are used.
    """
    args = _parse_cli_args()
    input_path = Path(args.input_csv)
    output_path = Path(args.output_json)

    # Basic sanity checks – raise a clear error if the input does not exist.
    if not input_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    apply_missing_and_quality_flags(input_path, output_path)
    print(f"Validation report written to {output_path}")


if __name__ == "__main__":
    # When invoked via ``python -m code.data.validator`` this block runs.
    main()