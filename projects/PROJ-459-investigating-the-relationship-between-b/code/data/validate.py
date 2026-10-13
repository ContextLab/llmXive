"""
Data validation utilities for the brain‑network‑music‑preference pipeline.

This module provides a collection of helper functions used throughout the
pipeline to ensure that downloaded OpenNeuro BIDS datasets contain the
required files and behavioural variables.  For the contract tests in
``tests/contract/test_data_validation.py`` a new public function
``check_behavioral_variables`` is required.  The implementation below
extends the existing module without removing any previously defined API
surface.

The functions are deliberately lightweight – they perform the checks
required by the contract tests and by the main pipeline, returning clear
``DataValidationError`` exceptions with an attached ``code`` attribute
when a problem is detected.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """
    Custom exception used throughout the validation module.

    Attributes
    ----------
    code : str
        Short error identifier (e.g. ``ERR_DATA_MISSING`` or
        ``ERR_UNDERPOWERED``) that tests can assert against.
    """

    def __init__(self, message: str, code: str = "ERR_GENERIC"):
        super().__init__(message)
        self.code = code


# ----------------------------------------------------------------------
# Existing helpers (kept compatible with earlier pipeline code)
# ----------------------------------------------------------------------

def check_participants_file(data_dir: Path) -> Path:
    """
    Verify that ``participants.tsv`` exists in the supplied BIDS directory.

    Parameters
    ----------
    data_dir : Path
        Path to the root of a downloaded OpenNeuro dataset.

    Returns
    -------
    Path
        Path to the ``participants.tsv`` file.

    Raises
    ------
    DataValidationError
        If the file does not exist.
    """
    participants_path = data_dir / "participants.tsv"
    if not participants_path.is_file():
        raise DataValidationError(
            f"participants.tsv not found in {data_dir}",
            code="ERR_DATA_MISSING",
        )
    return participants_path


def validate_sample_size(participants_df: pd.DataFrame, min_n: int = 85) -> int:
    """
    Ensure that the dataset contains at least ``min_n`` subjects.

    Parameters
    ----------
    participants_df : pd.DataFrame
        DataFrame loaded from ``participants.tsv``.
    min_n : int, optional
        Minimum required number of subjects (default 85).

    Returns
    -------
    int
        The number of subjects found.

    Raises
    ------
    DataValidationError
        If the sample size is below ``min_n``.
    """
    n_subjects = participants_df.shape[0]
    if n_subjects < min_n:
        raise DataValidationError(
            f"Sample size {n_subjects} below required minimum {min_n}",
            code="ERR_UNDERPOWERED",
        )
    return n_subjects


def enforce_min_subjects(data_dir: Path, min_n: int = 85) -> None:
    """
    Hard‑gate enforcement of the minimum subject count required for the
    study (N ≥ 85).  This function loads ``participants.tsv`` and raises a
    ``DataValidationError`` with code ``ERR_UNDERPOWERED`` if the count is
    insufficient.  It is deliberately separate from ``check_data_integrity``
    so that callers can perform the power check early (e.g., before any
    expensive I/O).

    Parameters
    ----------
    data_dir : Path
        Path to the root of the BIDS dataset.
    min_n : int, optional
        Required minimum number of subjects (default 85).

    Raises
    ------
    DataValidationError
        If the dataset contains fewer than ``min_n`` subjects.
    """
    participants_path = check_participants_file(data_dir)
    try:
        df = pd.read_csv(participants_path, sep="\t")
    except Exception as exc:
        raise DataValidationError(
            f"Failed to read participants.tsv for sample‑size check: {exc}",
            code="ERR_DATA_MISSING",
        )
    # Re‑use the existing validation logic to keep behaviour consistent
    validate_sample_size(df, min_n=min_n)


def get_behavioral_variable(
    participants_df: pd.DataFrame,
    primary_var: str = "musical_genre",
    fallback_var: str = "STOMP-R",
) -> str:
    """
    Determine which behavioural column should be used for downstream analysis.

    Parameters
    ----------
    participants_df : pd.DataFrame
        DataFrame loaded from ``participants.tsv``.
    primary_var : str, optional
        Preferred column name (default ``musical_genre``).
    fallback_var : str, optional
        Backup column name if the primary is missing (default ``STOMP-R``).

    Returns
    -------
    str
        The name of the column that will be used.

    Raises
    ------
    DataValidationError
        If neither the primary nor the fallback column is present.
    """
    cols = participants_df.columns.tolist()
    if primary_var in cols:
        return primary_var
    if fallback_var in cols:
        return fallback_var
    raise DataValidationError(
        f"Neither {primary_var} nor {fallback_var} found in participants.tsv",
        code="ERR_DATA_MISSING",
    )


def exclude_subjects_by_missing_data(
    confounds_df: pd.DataFrame, threshold: float = 0.1
) -> List[str]:
    """
    Placeholder implementation – returns an empty exclusion list.

    The full pipeline would inspect the confounds file for corrupted volumes.
    For the purpose of the contract tests only a stub is required.
    """
    return []


def exclude_subjects_by_motion(
    confounds_df: pd.DataFrame, fd_threshold: float = 0.5
) -> List[str]:
    """
    Placeholder implementation – returns an empty exclusion list.

    The full pipeline would compute mean Framewise Displacement per subject.
    """
    return []


def check_data_integrity(
    data_dir: Path,
    min_n: int = 85,
    primary_var: str = "musical_genre",
    fallback_var: str = "STOMP-R",
) -> List[str]:
    """
    Run the full suite of integrity checks on a BIDS dataset.

    Returns a list of subject identifiers that passed all checks.
    """
    participants_path = check_participants_file(data_dir)
    participants_df = pd.read_csv(participants_path, sep="\t")

    # Sample‑size check (may raise ``ERR_UNDERPOWERED``)
    validate_sample_size(participants_df, min_n=min_n)

    # Behavioural variable existence (may raise ``ERR_DATA_MISSING``)
    get_behavioral_variable(participants_df, primary_var, fallback_var)

    # For the contract tests we simply return the participant IDs.
    if "participant_id" not in participants_df.columns:
        raise DataValidationError(
            "participants.tsv missing required 'participant_id' column",
            code="ERR_DATA_MISSING",
        )
    return participants_df["participant_id"].astype(str).tolist()


# ----------------------------------------------------------------------
# New public function required by contract tests (T010)
# ----------------------------------------------------------------------

def check_behavioral_variables(data_dir: Path) -> Dict[str, Any]:
    """
    Validate the behavioural columns present in ``participants.tsv`` and
    return a summary dictionary required by the contract tests.

    The returned dictionary contains:

    - ``available_variables``: list of all column names found.
    - ``has_primary_variable``: ``True`` if ``musical_genre`` is present.
    - ``has_fallback_variable``: ``True`` if ``STOMP-R`` is present.
    - ``sample_size``: number of rows (subjects) in the file.

    The function raises ``DataValidationError`` with appropriate error
    codes when the file is missing, empty, malformed, or when the sample
    size is below the required threshold.
    """
    # Ensure the participants file exists
    participants_path = check_participants_file(data_dir)

    # Load the TSV – any parsing error is treated as a validation failure
    try:
        df = pd.read_csv(participants_path, sep="\t")
    except Exception as exc:
        raise DataValidationError(
            f"Failed to parse participants.tsv: {exc}",
            code="ERR_DATA_MISSING",
        )

    # Empty file handling
    if df.empty:
        raise DataValidationError(
            "participants.tsv is empty",
            code="ERR_DATA_MISSING",
        )

    # Column list
    available_vars = list(df.columns)

    # Determine presence of primary / fallback variables
    has_primary = "musical_genre" in available_vars
    has_fallback = "STOMP-R" in available_vars

    if not has_primary and not has_fallback:
        raise DataValidationError(
            "Neither 'musical_genre' nor 'STOMP-R' present in participants.tsv",
            code="ERR_DATA_MISSING",
        )

    # Sample‑size validation (must be >= 85)
    sample_size = df.shape[0]
    if sample_size < 85:
        raise DataValidationError(
            f"Sample size {sample_size} below required minimum of 85",
            code="ERR_UNDERPOWERED",
        )

    return {
        "available_variables": available_vars,
        "has_primary_variable": has_primary,
        "has_fallback_variable": has_fallback,
        "sample_size": sample_size,
    }


# ----------------------------------------------------------------------
# CLI entry point (kept for backward compatibility)
# ----------------------------------------------------------------------

def main() -> None:
    """
    Minimal CLI that runs ``check_data_integrity`` on a directory supplied
    via the first command‑line argument.  This mirrors the behaviour used
    by ``code/main.py``.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run data validation")
    parser.add_argument(
        "dataset_dir",
        type=Path,
        help="Path to the root of the downloaded OpenNeuro dataset",
    )
    args = parser.parse_args()

    try:
        valid_subjects = check_data_integrity(args.dataset_dir)
        logger.info(f"Validation succeeded – {len(valid_subjects)} subjects ready")
    except DataValidationError as err:
        logger.error(f"Validation failed [{err.code}]: {err}")
        raise


if __name__ == "__main__":
    main()


# Export public names for ``from data.validate import …`` convenience
__all__ = [
    "DataValidationError",
    "check_participants_file",
    "validate_sample_size",
    "enforce_min_subjects",
    "get_behavioral_variable",
    "exclude_subjects_by_missing_data",
    "exclude_subjects_by_motion",
    "check_data_integrity",
    "check_behavioral_variables",
    "main",
]