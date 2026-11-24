"""
Helper for computing lagged competitive pressure.
The public API matches the unit‑tests in ``tests/test_pressure.py``.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

_log = logging.getLogger(__name__)

def _parse_date(value: Any) -> datetime:
    """
    Convert a date string or ``datetime`` to a ``datetime`` object.
    Accepts ISO‑8601 strings (with or without timezone) and ``datetime`` objects.
    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Strip trailing Z (UTC) if present
        value = value.rstrip("Z")
        try:
            # Try full ISO format first
            return datetime.fromisoformat(value)
        except ValueError:
            # Fallback: try common date‑only format
            return datetime.strptime(value, "%Y-%m-%d")
    raise TypeError(f"Unsupported date type: {type(value)}")

def calculate_lagged_pressure(
    run_records: List[Dict[str, Any]],
    window_days: int = 30,
) -> List[Dict[str, Any]]:
    """
    Compute lagged competitive pressure for a list of run records.

    The function expects ``run_records`` to be a list of dictionaries,
    each containing at least ``'submission_date'`` and ``'runner_id'``.
    It returns a **new list** (the original list is not mutated) where each
    record has an additional integer field ``'lagged_competitive_pressure'``
    indicating the number of *other* runs whose ``submission_date`` falls
    within ``window_days`` days **before** the current record's date.

    Parameters
    ----------
    run_records : list[dict]
        List of run dictionaries.
    window_days : int, optional
        Size of the look‑back window in days (default: 30).

    Returns
    -------
    list[dict]
        New list with the pressure column added.

    Raises
    ------
    ValueError
        If any record is missing required keys.
    """
    # Validate input
    required_keys = {"submission_date", "runner_id"}
    for rec in run_records:
        if not required_keys.issubset(rec):
            missing = required_keys - rec.keys()
            raise ValueError(f"Record missing required fields: {missing}")

    # Sort records chronologically (oldest first) to make the sliding window easy
    sorted_records = sorted(
        run_records,
        key=lambda r: _parse_date(r["submission_date"]),
    )

    # List to accumulate results
    enriched: List[Dict[str, Any]] = []

    # We'll keep a sliding window of previous dates (as datetime objects)
    # and simply count how many fall inside the window for each record.
    prior_dates: List[datetime] = []

    for rec in sorted_records:
        cur_date = _parse_date(rec["submission_date"])

        # Remove dates that are older than the window
        cutoff = cur_date - timedelta(days=window_days)
        prior_dates = [d for d in prior_dates if d > cutoff]

        # The pressure is the number of prior dates still in the window
        pressure = len(prior_dates)

        # Append current date to the window for future records
        prior_dates.append(cur_date)

        # Copy record and add the new field
        new_rec = dict(rec)  # shallow copy is fine
        new_rec["lagged_competitive_pressure"] = pressure
        enriched.append(new_rec)

    return enriched