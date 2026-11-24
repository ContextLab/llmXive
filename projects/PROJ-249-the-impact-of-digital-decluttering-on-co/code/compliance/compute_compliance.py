"""
Compliance processing pipeline (Task T004).

This script reads all daily compliance log CSV files located under
``data/raw/compliance_logs/`` and computes per‑participant compliance
statistics according to the study rules:

* Social media minutes ≤ 30
* No news consumption (``news_consumption == False``)
* Notifications must be turned off (``notifications_off == True``)

It also validates plausibility of the ``social_media_minutes`` field
(0 ≤ minutes ≤ 1440) and records data‑quality flags:

* ``minutes_out_of_range`` – any minute value outside the allowed range.
* ``zero_all_days`` – participant reported 0 minutes for **all** 7 days.

The results are written to:
  - ``data/processed/aggregated_compliance.csv`` (summary table)
  - ``data/processed/compliance_flags.json`` (per‑participant flags)

The script returns an exit code (0 on success, non‑zero on error) so that
the test suite can invoke ``main()`` directly.
"""

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_compliance_logs(log_dir: Path):
    """
    Load all CSV log files from ``log_dir`` and return a list of row dicts.

    Parameters
    ----------
    log_dir: Path
        Directory containing ``*.csv`` log files.

    Returns
    -------
    List[dict]
        List of rows (each row is a dict with the CSV columns).
    """
    if not log_dir.exists():
        raise FileNotFoundError(f"Compliance log directory not found: {log_dir}")

    rows = []
    csv_files = sorted(log_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV log files found in {log_dir}")

    for csv_path in csv_files:
        log.debug(f"Reading compliance log file: {csv_path}")
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for line_num, row in enumerate(reader, start=2):
                rows.append(row)
    return rows


def _parse_bool(value: str) -> bool:
    """Convert common string representations to ``bool``."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _validate_minutes(minutes_raw, participant_id, day_idx):
    """
    Validate ``minutes`` field; raise ``ValueError`` only for out‑of‑range
    values (the pipeline records a flag instead of aborting).
    """
    try:
        minutes = float(minutes_raw)
    except (TypeError, ValueError):
        raise ValueError(
            f"Participant {participant_id}, day {day_idx}: "
            f"non‑numeric minutes value '{minutes_raw}'"
        )

    if minutes < 0 or minutes > 1440:
        # Out of range – caller will record a flag.
        return minutes, True
    return minutes, False


def _compute_participant_stats(rows):
    """
    Compute compliance statistics and flags for each participant.

    Returns
    -------
    Tuple[dict, dict]
        ``aggregated`` – mapping participant_id → dict with
        ``total_days``, ``compliant_days`` and ``compliance_percentage``.
        ``flags`` – mapping participant_id → list of flag strings.
    """
    # Organise rows per participant
    participant_days = defaultdict(list)  # participant_id → list of row dicts
    for row in rows:
        pid = row.get("participant_id")
        if not pid:
            raise ValueError("Row missing ``participant_id``")
        participant_days[pid].append(row)

    aggregated = {}
    flags = {}

    for pid, day_rows in participant_days.items():
        total_days = len(day_rows)
        compliant_days = 0
        minutes_all = []
        out_of_range_flag = False

        for idx, row in enumerate(day_rows, start=1):
            # Parse fields
            minutes_raw = row.get("social_media_minutes")
            minutes, out_of_range = _validate_minutes(
                minutes_raw, pid, idx
            )
            minutes_all.append(minutes)
            if out_of_range:
                out_of_range_flag = True

            news = _parse_bool(row.get("news_consumption"))
            notif = _parse_bool(row.get("notifications_off"))

            # Apply compliance rule
            if minutes <= 30 and not news and notif:
                compliant_days += 1

        # Compute percentage (rounded to 4 decimal places)
        compliance_pct = (
            round((compliant_days / total_days) * 100, 4)
            if total_days > 0
            else 0.0
        )

        aggregated[pid] = {
            "participant_id": pid,
            "total_days": total_days,
            "compliant_days": compliant_days,
            "compliance_percentage": compliance_pct,
        }

        # Build flags list
        pid_flags = []
        if out_of_range_flag:
            pid_flags.append("minutes_out_of_range")
        if all(m == 0 for m in minutes_all):
            pid_flags.append("zero_all_days")
        flags[pid] = pid_flags

    # Ensure deterministic ordering (sorted by participant_id)
    aggregated = dict(sorted(aggregated.items()))
    flags = dict(sorted(flags.items()))
    return aggregated, flags


def _write_aggregated_csv(aggregated, output_path: Path):
    """Write the aggregated compliance CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "participant_id",
        "total_days",
        "compliant_days",
        "compliance_percentage",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pid, data in aggregated.items():
            writer.writerow(data)


def _write_flags_json(flags, output_path: Path):
    """Write the compliance flags JSON (sorted keys)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(flags, f, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def run_compliance_pipeline(
    raw_logs_dir: Path = None,
    aggregated_csv: Path = None,
    flags_json: Path = None,
) -> dict:
    """
    Execute the full compliance‑log pipeline.

    Parameters
    ----------
    raw_logs_dir: Path, optional
        Directory containing raw ``*.csv`` log files.
        Defaults to ``data/raw/compliance_logs``.
    aggregated_csv: Path, optional
        Destination CSV for aggregated compliance.
        Defaults to ``data/processed/aggregated_compliance.csv``.
    flags_json: Path, optional
        Destination JSON for flags.
        Defaults to ``data/processed/compliance_flags.json``.

    Returns
    -------
    dict
        Dictionary with keys ``aggregated`` and ``flags`` holding the
        in‑memory results.
    """
    if raw_logs_dir is None:
        raw_logs_dir = paths.raw("compliance_logs")
    if aggregated_csv is None:
        aggregated_csv = paths.processed("aggregated_compliance.csv")
    if flags_json is None:
        flags_json = paths.processed("compliance_flags.json")

    log.info(f"Loading compliance logs from {raw_logs_dir}")
    rows = _load_compliance_logs(raw_logs_dir)

    log.info("Computing per‑participant statistics and flags")
    aggregated, flags = _compute_participant_stats(rows)

    log.info(f"Writing aggregated CSV to {aggregated_csv}")
    _write_aggregated_csv(aggregated, aggregated_csv)

    log.info(f"Writing flags JSON to {flags_json}")
    _write_flags_json(flags, flags_json)

    return {"aggregated": aggregated, "flags": flags}


def main() -> int:
    """
    Command‑line entry point.

    Returns
    -------
    int
        Exit status (0 = success, non‑zero = error).
    """
    try:
        run_compliance_pipeline()
        print("\n=== Compliance pipeline completed successfully ===")
        return 0
    except Exception as exc:  # pragma: no cover – any unexpected error is fatal
        log.error(f"Compliance pipeline failed: {exc}", exc_info=True)
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())