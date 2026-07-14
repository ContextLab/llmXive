"""
src/analysis/filter.py
-----------------------

Utility for splitting the unified trial CSV into modality‑specific files.
The script is also executable so that the quick‑start run‑book can call it
directly if needed.
"""

import json
import logging
import os
import sys
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# Logging helpers
# ----------------------------------------------------------------------
def _setup_logging() -> None:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

def log_info(message: str) -> None:
    _setup_logging()
    logging.getLogger(__name__).info(message)

def log_error(message: str) -> None:
    _setup_logging()
    logging.getLogger(__name__).error(message)

# ----------------------------------------------------------------------
# Core functionality
# ----------------------------------------------------------------------
def setup_directories(project_root: Path) -> dict:
    """Ensure required directories exist and return their paths."""
    raw_dir = project_root / "data" / "raw"
    derived_dir = project_root / "data" / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    return {"raw": raw_dir, "derived": derived_dir}

def load_trial_data(csv_path: Path) -> list:
    """Load a CSV of trials and return a list of dicts."""
    df = pd.read_csv(csv_path)
    return df.to_dict(orient="records")

def filter_by_modality(trial_rows: list, modality: str) -> list:
    """Return only rows where ``stimulus_modality`` matches ``modality``."""
    return [row for row in trial_rows if row.get("stimulus_modality") == modality]

def write_output(trial_rows: list, output_path: Path) -> None:
    """Write a list of trial dictionaries to ``output_path`` as CSV."""
    if not trial_rows:
        log_error(f"No data to write for {output_path}")
        return
    df = pd.DataFrame(trial_rows)
    df.to_csv(output_path, index=False)
    log_info(f"Wrote {len(trial_rows)} rows to {output_path}")

def run_filter_analysis() -> None:
    """Convenient CLI entry point used by quick‑start."""
    project_root = Path(__file__).resolve().parents[3]
    dirs = setup_directories(project_root)

    # Load the unified trial file.
    trial_path = dirs["derived"] / "trial_data.csv"
    if not trial_path.is_file():
        log_error(f"Unified trial file not found: {trial_path}")
        sys.exit(1)

    trial_rows = load_trial_data(trial_path)

    for modality in ("visual", "auditory"):
        filtered = filter_by_modality(trial_rows, modality)
        out_path = dirs["derived"] / f"{modality}_trials.csv"
        write_output(filtered, out_path)

    sys.exit(0)

if __name__ == "__main__":
    run_filter_analysis()
