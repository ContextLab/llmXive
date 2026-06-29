from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

# Define the expected pipeline steps for logging completeness.
EXPECTED_STEPS: List[str] = [
    "ingest_transcripts",
    "detect_markers",
    "compute_scores",
    "extract_metrics",
    "impute_confounders",
    "merge_datasets",
    "run_regression",
    "validation",
]

def _write_log_entry(log_file: Path, step: str) -> None:
    """
    Append a single JSON‑line entry for *step* to *log_file*.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "status": "completed",
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def main(log_dir: Path) -> Path:
    """
    Generate a dummy pipeline log containing entries for all expected steps.

    Parameters
    ----------
    log_dir: Path
        Directory where the dummy log file will be written.

    Returns
    -------
    Path
        Path to the generated log file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "run_dummy.log"
    # Start with a fresh file
    if log_path.exists():
        log_path.unlink()
    for step in EXPECTED_STEPS:
        _write_log_entry(log_path, step)
    return log_path