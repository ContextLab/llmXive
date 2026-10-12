"""
Validation utilities for the EEG pipeline.

Implements T005 (base data validation utility, FR-006):
check for required variables (EEG channels, k-scores/d', trial
timestamps) BEFORE processing and halt with SPECIFIC error codes
so downstream failures are diagnosable.

FR-006 error code registry (exit codes):
  - ERR_FR006_EEG_CHANNELS      = 10  (missing EEG channels)
  - ERR_FR006_BEHAVIORAL        = 11  (missing k-scores / d')
  - ERR_FR006_TRIAL_TIMESTAMPS  = 12  (missing trial timestamps/events)
  - ERR_FR006_MISSING_COLUMNS   = 13  (missing required DataFrame columns)
  - ERR_FR006_DATASET_FIELDS    = 14  (missing dataset metadata fields)
  - ERR_FR006_EMPTY_DATA        = 15  (empty data structure)
  - ERR_FR006_FILE_NOT_FOUND    = 16  (missing input file)
  - ERR_FR006_GENERIC           = 1   (unclassified validation failure)
"""
import sys
import os
import logging
import json
from typing import List, Set, Dict, Any, Optional, Union
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from utils.logging_config import get_logger
    logger = get_logger("validation")
except ImportError:  # direct-execution fallback
    logger = logging.getLogger("validation")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------------
# FR-006 error code registry
# ------------------------------------------------------------------
ERR_FR006_EEG_CHANNELS = 10
ERR_FR006_BEHAVIORAL = 11
ERR_FR006_TRIAL_TIMESTAMPS = 12
ERR_FR006_MISSING_COLUMNS = 13
ERR_FR006_DATASET_FIELDS = 14
ERR_FR006_EMPTY_DATA = 15
ERR_FR006_FILE_NOT_FOUND = 16
ERR_FR006_GENERIC = 1

ERROR_CODES: Dict[str, int] = {
    "FR006_EEG_CHANNELS": ERR_FR006_EEG_CHANNELS,
    "FR006_BEHAVIORAL": ERR_FR006_BEHAVIORAL,
    "FR006_TRIAL_TIMESTAMPS": ERR_FR006_TRIAL_TIMESTAMPS,
    "FR006_MISSING_COLUMNS": ERR_FR006_MISSING_COLUMNS,
    "FR006_DATASET_FIELDS": ERR_FR006_DATASET_FIELDS,
    "FR006_EMPTY_DATA": ERR_FR006_EMPTY_DATA,
    "FR006_FILE_NOT_FOUND": ERR_FR006_FILE_NOT_FOUND,
    "FR006_GENERIC": ERR_FR006_GENERIC,
}

# Behavioral measures accepted by FR-006 (k-scores or d')
BEHAVIORAL_MEASURE_KEYS = {"k_score", "d_prime"}


def log_error(message: str, error_code: int = ERR_FR006_GENERIC) -> int:
    """Log an error message tagged with its FR-006 error code and
    return the code (callers pass it to sys.exit)."""
    logger.error(f"[FR-006 code {error_code}] {message}")
    print(f"[FR-006 code {error_code}] {message}", file=sys.stderr)
    return error_code


def _halt(message: str, error_code: int) -> None:
    """Log with the specific FR-006 error code and halt with it."""
    code = log_error(message, error_code)
    sys.exit(code)


# ------------------------------------------------------------------
# Generic validators
# ------------------------------------------------------------------
def validate_file_exists(file_path: Union[str, Path]) -> bool:
    """Validate that a file exists (FR-006 pre-processing check)."""
    path = Path(file_path)
    if not path.exists():
        _halt(f"File not found: {path}", ERR_FR006_FILE_NOT_FOUND)
    return True


def validate_dataframe_not_empty(df: pd.DataFrame) -> bool:
    """Validate that a dataframe is not empty."""
    if df is None or df.empty:
        _halt("DataFrame is empty", ERR_FR006_EMPTY_DATA)
    return True


def exit_on_validation_failure(condition: bool, message: str,
                               error_code: int = ERR_FR006_GENERIC) -> None:
    """Exit with the specific error code if condition is False."""
    if not condition:
        _halt(message, error_code)


# ------------------------------------------------------------------
# FR-006 core validators
# ------------------------------------------------------------------
def validate_eeg_channels(channels: List[str], required: Set[str]) -> bool:
    """
    FR-006: Validate that required EEG channels are present.
    Halts with ERR_FR006_EEG_CHANNELS (exit code 10) if any are missing.
    """
    missing = required - set(channels)
    if missing:
        msg = (f"CRITICAL: Missing required electrode data: {sorted(missing)}. "
               f"No partial analysis proceeds. [FR-006]")
        _halt(msg, ERR_FR006_EEG_CHANNELS)
    return True


def validate_behavioral_metrics(metrics: Dict[str, Any],
                                required_keys: Optional[Set[str]] = None) -> bool:
    """
    FR-006: Validate that required behavioral metrics (k-scores or d')
    are present and non-null.
    Halts with ERR_FR006_BEHAVIORAL (exit code 11) if missing.
    """
    if required_keys is None:
        required_keys = BEHAVIORAL_MEASURE_KEYS
    missing = required_keys - set(metrics.keys())
    if missing:
        msg = (f"ERROR: Missing behavioral measures ({sorted(missing)}) "
               f"in dataset. Halting. [FR-006]")
        _halt(msg, ERR_FR006_BEHAVIORAL)
    # Also reject null / NaN values for the measures
    for key in required_keys:
        value = metrics.get(key)
        if value is None or (isinstance(value, float) and np.isnan(value)):
            msg = (f"ERROR: Behavioral measure '{key}' is null. "
                   f"Halting. [FR-006]")
            _halt(msg, ERR_FR006_BEHAVIORAL)
    return True


def validate_trial_timestamps(timestamps: Any) -> bool:
    """
    FR-006: Validate that trial timestamps / event onsets exist and are
    usable (non-empty, numeric, sorted-able).
    Halts with ERR_FR006_TRIAL_TIMESTAMPS (exit code 12) if invalid.
    """
    if timestamps is None:
        _halt("ERROR: Missing trial timestamps/events. Halting. [FR-006]",
              ERR_FR006_TRIAL_TIMESTAMPS)
    arr = np.asarray(timestamps)
    if arr.size == 0:
        _halt("ERROR: Trial timestamp array is empty. Halting. [FR-006]",
              ERR_FR006_TRIAL_TIMESTAMPS)
    if not np.issubdtype(arr.dtype, np.number):
        _halt("ERROR: Trial timestamps are not numeric. Halting. [FR-006]",
              ERR_FR006_TRIAL_TIMESTAMPS)
    return True


# ------------------------------------------------------------------
# Structural validators
# ------------------------------------------------------------------
def load_and_validate_csv(file_path: Union[str, Path],
                          required_columns: List[str]) -> pd.DataFrame:
    """Load a CSV and validate its columns (halts with code 13)."""
    path = Path(file_path)
    if not path.exists():
        _halt(f"File not found: {path}", ERR_FR006_FILE_NOT_FOUND)

    df = pd.read_csv(path)
    validate_dataframe_not_empty(df)

    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        msg = (f"ERROR: Missing required columns in {path}: "
               f"{sorted(missing_cols)} [FR-006]")
        _halt(msg, ERR_FR006_MISSING_COLUMNS)

    return df


def validate_dataset(dataset: Dict[str, Any],
                     required_fields: List[str]) -> bool:
    """Validate a dataset dictionary for required fields (code 14)."""
    missing = set(required_fields) - set(dataset.keys())
    if missing:
        msg = f"ERROR: Missing dataset fields: {sorted(missing)} [FR-006]"
        _halt(msg, ERR_FR006_DATASET_FIELDS)
    return True


# ------------------------------------------------------------------
# Power requirements (T017)
# ------------------------------------------------------------------
def check_power_requirements(
        n_subjects: int,
        output_path: Path = Path("data/results/power_status.json")) -> str:
    """
    T017: Check power requirements.
    - If N < 30: Halt with 'INSUFFICIENT POWER' (exit code 1).
    - If 30 <= N <= 52: Log warning, write power_status.json with
      status 'LIMITED' and continue.
    - If N > 52: Proceed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if n_subjects < 30:
        message = ("INSUFFICIENT POWER: N < 30. Redesign required "
                   "(e.g., data aggregation or power analysis)")
        status_data = {"n_count": n_subjects, "status": "INSUFFICIENT",
                       "message": message}
        with open(output_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        logger.error(message)
        print(message, file=sys.stderr)
        sys.exit(1)
    elif n_subjects <= 52:
        message = "WARNING: Limited power (N between 30 and 52)"
        logger.warning(message)
        status_data = {"n_count": n_subjects, "status": "LIMITED",
                       "message": message}
        with open(output_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        return "LIMITED"
    else:
        status_data = {"n_count": n_subjects, "status": "OK",
                       "message": "Power sufficient"}
        with open(output_path, 'w') as f:
            json.dump(status_data, f, indent=2)
        return "OK"


def main():
    """Self-check entry point for the validation utility."""
    logger.info("Running validation self-check...")
    validate_eeg_channels(["Fz", "Pz", "Cz"], {"Fz", "Pz"})
    validate_behavioral_metrics({"k_score": 0.5, "d_prime": 1.2})
    validate_trial_timestamps([0.0, 1.2, 2.4])
    logger.info("All validation self-checks passed.")


if __name__ == "__main__":
    main()
