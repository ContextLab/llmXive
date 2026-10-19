import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def _parse_date(value: Any) -> datetime:
    """Convert a date string or datetime to a datetime object."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Accept ISO‑8601 strings, with or without a trailing 'Z'
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid date string: {value}") from exc
    raise TypeError(f"Unsupported date type: {type(value)}")

def calculate_lagged_pressure(
    run_records: List[Dict[str, Any]],
    runner_id_map: Optional[Dict[Any, Any]] = None,
    window_days: int = 30,
) -> List[Dict[str, Any]]:
    """
    Calculate lagged competitive pressure for each run.

    For a given run, the pressure is defined as the count of **unique**
    runners who submitted a run in the *window* ``[run_date - window_days,
    run_date - 1]`` (i.e. the `window_days` days preceding the run).

    Parameters
    ----------
    run_records : list[dict]
        Each dict must contain at least ``submission_date`` and ``runner_id``.
    runner_id_map : dict | None
        Legacy mapping from original runner IDs to hashed IDs.
        If provided, the mapping is used; otherwise the original IDs are
        used directly.
    window_days : int, default 30
        Size of the look‑back window in days.

    Returns
    -------
    list[dict]
        The input records, each augmented with a new key
        ``lagged_competitive_pressure`` containing the integer count.

    Raises
    ------
    ValueError
        If any record is missing ``submission_date`` or ``runner_id``.
    """
    if not run_records:
        return []

    # Validate required fields early so tests expecting ValueError see it.
    for rec in run_records:
        if "submission_date" not in rec or "runner_id" not in rec:
            raise ValueError("Each record must contain 'submission_date' and 'runner_id'.")

    # Normalise runner IDs (hash map if supplied)
    def _norm_id(rid):
        if runner_id_map and rid in runner_id_map:
            return runner_id_map[rid]
        return rid

    # Organise runs by date for efficient window queries
    runs_by_date: Dict[datetime.date, List[Dict[str, Any]]] = {}
    for rec in run_records:
        run_date = _parse_date(rec["submission_date"]).date()
        runs_by_date.setdefault(run_date, []).append(rec)

    sorted_dates = sorted(runs_by_date.keys())

    # Pre‑compute cumulative sets of unique runners up to each date
    cumulative_runners: Dict[datetime.date, set] = {}
    current_set: set = set()
    for d in sorted_dates:
        for r in runs_by_date[d]:
            current_set.add(_norm_id(r["runner_id"]))
        cumulative_runners[d] = current_set.copy()

    # Compute pressure for each record
    for rec in run_records:
        run_date = _parse_date(rec["submission_date"]).date()
        start = run_date - timedelta(days=window_days)
        end = run_date - timedelta(days=1)

        # Gather unique runners in the window
        unique_runners = set()
        for d in sorted_dates:
            if start <= d <= end:
                for r in runs_by_date[d]:
                    unique_runners.add(_norm_id(r["runner_id"]))

        rec["lagged_competitive_pressure"] = len(unique_runners)

    return run_records
