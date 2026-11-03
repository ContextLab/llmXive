import csv
import datetime
from pathlib import Path
from llmxive_toolkit import paths

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Log a subject exclusion event to ``data/interim/data_exclusion_log.txt``.

    The log file is a CSV with three columns:
    ``subject_id,reason,timestamp``.
    If the file does not exist, it is created with a header row.

    Parameters
    ----------
    reason : str
        One of the standardized exclusion reason codes
        (e.g., ``MISSING_SCAN``, ``MISSING_SCORE``, ``HIGH_MOTION``).
    subject_id : str
        The identifier of the subject being excluded.
    """
    # Resolve the log file path using the toolkit helper (ensures correct root)
    log_path = Path("data", "interim", "data_exclusion_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine whether we need to write a header
    write_header = not log_path.is_file()

    timestamp = datetime.datetime.utcnow().isoformat()

    with open(log_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(["subject_id", "reason", "timestamp"])
        writer.writerow([subject_id, reason, timestamp])