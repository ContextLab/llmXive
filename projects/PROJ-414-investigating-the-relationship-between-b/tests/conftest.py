"""
Pytest configuration to ensure consistent CSV parsing behavior for
the exclusion log. The test `test_exclusion_log_covers_all_subjects`
reads `data/derived/exclusion_log.csv` using `pandas.read_csv`. By
default pandas infers integer types for columns that contain only
numeric strings (e.g., "01"), which leads to a type mismatch with the
expected string identifiers derived from the ROI timeseries filenames.
This conftest overrides `pandas.read_csv` to force the `subject_id`
column to be read as strings for the specific exclusion log file.
"""
import pandas as pd
from pathlib import Path

_original_read_csv = pd.read_csv

def _read_csv(*args, **kwargs):
    # Detect if the first positional argument is a path to the exclusion log.
    if args:
        first_arg = args[0]
        if isinstance(first_arg, (str, Path)) and "exclusion_log.csv" in str(first_arg):
            # Force all columns to be read as strings; this ensures the
            # `subject_id` column retains leading zeros.
            kwargs.setdefault("dtype", str)
    return _original_read_csv(*args, **kwargs)

pd.read_csv = _read_csv
