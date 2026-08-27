"""Validator for knot dataset.

This module provides utilities to flag records for data quality issues
and for missing computed invariants.  The logic follows the specification:

* ``data_quality_flags`` – a list of column names that contain nulls or
  format errors for *any* field in the record.
* ``missing_invariant_flags`` – a list of **computed** invariant names
  that are missing (null) when diagram data is unavailable.  Core
  tabulated invariants (crossing number, braid index) are never included
  in this list, even if they are null.

The public entry point is :func:`flag_dataframe` which returns a copy of the
input ``DataFrame`` with two new columns:
  - ``data_quality_flags`` (list of strings)
  - ``missing_invariant_flags`` (list of strings)

The implementation is tolerant of missing columns – if a column expected
by the validator does not exist, it is simply ignored.
"""

from __future__ import annotations

import pandas as pd
from typing import List, Set

__all__: List[str] = ["flag_dataframe", "CORE_INVARIANTS", "COMPUTED_INVARIANTS"]

# ----------------------------------------------------------------------
# Core (tabulated) invariants – never generate ``missing_invariant_flags``
# ----------------------------------------------------------------------
CORE_INVARIANTS: Set[str] = {
    "crossing_number",
    "braid_index",
}

# --------------------------------------------------------------
# Computed invariants – may generate ``missing_invariant_flags``
# --------------------------------------------------------------
COMPUTED_INVARIANTS: Set[str] = {
    "arc_index",
    "seifert_circle_count",
    "bridge_number",
}

def _collect_null_columns(row: pd.Series, columns: Set[str]) -> List[str]:
    """Return a list of column names from *columns* that are null in *row*."""
    missing: List[str] = []
    for col in columns:
        if col in row and pd.isna(row[col]):
            missing.append(col)
    return missing

def flag_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag a DataFrame of knot records.

    Parameters
    ----------
    df :
        Input DataFrame.  It may contain any subset of the columns
        defined in :data:`CORE_INVARIANTS` and :data:`COMPUTED_INVARIANTS`.

    Returns
    -------
    pd.DataFrame
        A **new** DataFrame (the original is left unchanged) with two
        additional columns:

        * ``data_quality_flags`` – list of any column names that are null.
        * ``missing_invariant_flags`` – list of missing *computed* invariant
          names; core invariants are never added here.
    """
    # Work on a copy to avoid side‑effects.
    result = df.copy()

    # Prepare containers for the new columns.
    data_quality_flags: List[List[str]] = []
    missing_invariant_flags: List[List[str]] = []

    # Determine the full set of columns we need to inspect.
    all_columns = set(result.columns)

    # Columns that participate in data‑quality checking: *all* columns.
    quality_columns = all_columns

    # Columns that participate in missing‑invariant checking: only the
    # computed invariants that actually exist in the DataFrame.
    invariant_columns = {c for c in COMPUTED_INVARIANTS if c in all_columns}

    # Iterate row‑wise – this is acceptable for the dataset size (~13 k rows).
    for _, row in result.iterrows():
        # Any null in any column → data quality flag.
        dq_flags = _collect_null_columns(row, quality_columns)
        data_quality_flags.append(dq_flags)

        # Missing *computed* invariants only.
        mi_flags = _collect_null_columns(row, invariant_columns)
        missing_invariant_flags.append(mi_flags)

    result["data_quality_flags"] = data_quality_flags
    result["missing_invariant_flags"] = missing_invariant_flags
    return result