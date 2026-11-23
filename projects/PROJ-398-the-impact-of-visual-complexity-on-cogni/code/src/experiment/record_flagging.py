"""
src.experiment.record_flagging
--------------------------------
Utility for flagging participant session records that are incomplete,
i.e., missing any NASA‑TLX related fields or the reaction‑time measurement.

The function is deliberately lightweight and does not enforce any specific
TLX schema – it inspects column names at runtime:

* Any column whose name contains ``tlx`` (case‑insensitive) is considered a
  TLX‑related field.
* Columns named exactly ``reaction_time`` or ``rt`` (case‑insensitive) are
  treated as the reaction‑time field.

If any of the identified required columns contain a missing value (NaN or
None) for a given row, that row is marked for exclusion by adding a new
boolean column ``exclude`` set to ``True``.  Rows with complete data have
``exclude`` set to ``False``.

This module is used by the test ``tests/test_experiment.py::test_incomplete_record_flagging``
and can be integrated into the session recording pipeline (e.g., called
inside ``src.experiment.server.record_participant_session``) to ensure that
downstream analyses automatically drop incomplete records.
"""

from __future__ import annotations

import pandas as pd
from typing import List


def _identify_required_columns(df: pd.DataFrame) -> List[str]:
    """
    Determine which columns in ``df`` are required for a complete record.

    TLX columns are detected by the substring ``tlx`` (case‑insensitive).
    Reaction‑time columns are identified by the exact names ``reaction_time``
    or ``rt`` (case‑insensitive).

    Parameters
    ----------
    df: pd.DataFrame
        The DataFrame to inspect.

    Returns
    -------
    List[str]
        A list of column names that are required.
    """
    tlx_cols = [c for c in df.columns if "tlx" in c.lower()]
    rt_cols = [c for c in df.columns if c.lower() in ("reaction_time", "rt")]
    # Preserve order but avoid duplicates
    required = tlx_cols + [c for c in rt_cols if c not in tlx_cols]
    return required


def flag_incomplete_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of ``df`` with an added boolean column ``exclude``.

    ``exclude`` is ``True`` for rows that are missing any required TLX or
    reaction‑time data, and ``False`` otherwise.

    Parameters
    ----------
    df: pd.DataFrame
        Input DataFrame containing participant session data.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with the ``exclude`` column appended.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    required_cols = _identify_required_columns(df)

    # If no TLX or RT columns are present, we consider all rows complete.
    # This mirrors a permissive stance; callers can decide to treat this as
    # an error condition if desired.
    if not required_cols:
        result = df.copy()
        result["exclude"] = False
        return result

    # ``isnull`` correctly handles NaN, None, and pandas NA types.
    missing_mask = df[required_cols].isnull().any(axis=1)

    result = df.copy()
    result["exclude"] = missing_mask
    return result


# ----------------------------------------------------------------------
# Example usage (not executed during import):
#
# >>> import pandas as pd
# >>> from src.experiment.record_flagging import flag_incomplete_records
# >>> df = pd.DataFrame({
# ...     "participant_id": [1, 2],
# ...     "tlx_score": [45.0, None],
# ...     "reaction_time": [350, 400],
# ... })
# >>> flagged = flag_incomplete_records(df)
# >>> flagged["exclude"].tolist()
# [False, True]
#
# The test suite validates the behaviour against a fixture DataFrame.
# ----------------------------------------------------------------------
