"""
Logging infrastructure for training runs and gating signals.

Implements T007 requirements, providing JSONL and CSV logging with
singleton logger management.
"""
import json
import csv
import os
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

# Module‑level cache to ensure a single Logger per name
_LOGGER_CACHE: Dict[str, "Logger"] = {}

class Logger:
    """
    Logger for training runs and gating signals.

    Writes both JSONL (one record per line) and CSV files for each
    artifact type.  Files are created in ``log_dir`` and are scoped to a
    unique ``run_id`` generated at instantiation time.
    """

    def __init__(self, log_dir: str = "data/processed"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Unique identifier for this logger instance / run
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSONL paths
        self.training_log_path = self.log_dir / f"training_run_{self.run_id}.jsonl"
        self.gating_log_path = self.log_dir / f"gating_signal_{self.run_id}.jsonl"

        # CSV paths (optional, for easier tabular inspection)
        self.training_csv_path = self.log_dir / f"training_run_{self.run_id}.csv"
        self.gating_csv_path = self.log_dir / f"gating_signal_{self.run_id}.csv"

        # Initialise empty files
        self._init_file(self.training_log_path)
        self._init_file(self.gating_log_path)
        # CSV files are lazily initialised on first write

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _init_file(self, path: Path) -> None:
        """Create an empty file if it does not exist."""
        path.touch(exist_ok=True)

    def _write_jsonl(self, path: Path, data: Dict) -> None:
        """Append a JSON line to ``path``."""
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def _write_csv(self, path: Path, data: Dict) -> None:
        """
        Append a row to a CSV file.

        If the file is empty, a header row is written first.
        """
        file_exists = path.exists() and path.stat().st_size > 0
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

    # ------------------------------------------------------------------
    # Public logging methods
    # ------------------------------------------------------------------
    def log_training_run(self, data: Dict) -> None:
        """Log a training‑run record to JSONL and CSV."""
        record = dict(data)  # shallow copy to avoid mutating caller data
        record["timestamp"] = datetime.now().isoformat()
        record["run_id"] = self.run_id

        self._write_jsonl(self.training_log_path, record)
        self._write_csv(self.training_csv_path, record)

    def log_gating_signal(self, data: Dict) -> None:
        """Log a gating‑signal record to JSONL and CSV."""
        record = dict(data)
        record["timestamp"] = datetime.now().isoformat()
        record["run_id"] = self.run_id

        self._write_jsonl(self.gating_log_path, record)
        self._write_csv(self.gating_csv_path, record)

    def close(self) -> None:
        """Placeholder for future resource cleanup."""
        # Currently nothing to clean up; method retained for API stability.
        pass

# ----------------------------------------------------------------------
# Public helper functions – these match the original API surface
# ----------------------------------------------------------------------
def get_logger(name: str = "default", log_dir: str = "data/processed") -> Logger:
    """
    Retrieve (or create) a named ``Logger`` instance.

    A module‑level cache ensures that repeated calls with the same
    ``name`` return the same ``Logger`` object, so multiple logging calls
    within a single run write to the same files.
    """
    if name not in _LOGGER_CACHE:
        _LOGGER_CACHE[name] = Logger(log_dir)
    return _LOGGER_CACHE[name]

def log_training_run(data: Dict, log_dir: str = "data/processed") -> None:
    """
    Convenience wrapper that logs a training‑run record using the default
    logger.
    """
    logger = get_logger("default", log_dir)
    logger.log_training_run(data)

def log_gating_signal(data: Dict, log_dir: str = "data/processed") -> None:
    """
    Convenience wrapper that logs a gating‑signal record using the default
    logger.
    """
    logger = get_logger("default", log_dir)
    logger.log_gating_signal(data)

def close_logger(logger: Logger) -> None:
    """Close a ``Logger`` instance."""
    logger.close()
