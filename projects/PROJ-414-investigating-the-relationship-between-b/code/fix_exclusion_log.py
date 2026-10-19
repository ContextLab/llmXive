"""Fix exclusion_log.csv subject_id format.

The extraction stage historically wrote integer subject identifiers,
while downstream tests expect the identifiers to match the ROI
filenames (e.g., ``01``, ``02``). This helper rewrites the CSV,
converting the ``subject_id`` column to the zero‑padded string form
that matches the ROI file stems.
"""
import csv
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_roi_subject_ids():
    """Return a mapping from integer ID -> zero‑padded string ID."""
    roi_files = sorted(paths.data("derived", "roi_timeseries_*.csv"))
    mapping = {}
    for f in roi_files:
        sid_str = f.stem.replace("roi_timeseries_", "")
        try:
            sid_int = int(sid_str)
        except ValueError:
            # Non‑numeric IDs are kept as‑is.
            mapping[sid_str] = sid_str
            continue
        mapping[sid_int] = sid_str
    return mapping

def main(argv=None):
    log.info("Running fix_exclusion_log stage")
    log_path = paths.data("derived", "exclusion_log.csv")
    if not log_path.is_file():
        log.warning("exclusion_log.csv not found – nothing to fix")
        return 0

    mapping = _load_roi_subject_ids()
    rows = []
    with log_path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                sid_int = int(row["subject_id"])
                row["subject_id"] = mapping.get(sid_int, str(sid_int))
            except (ValueError, KeyError):
                # Keep original if conversion fails.
                pass
            rows.append(row)

    # Write back with the original field order.
    fieldnames = rows[0].keys() if rows else []
    with log_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    log.info("exclusion_log.csv subject IDs fixed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
