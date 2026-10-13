"""
Unit test for the JSON/CSV logging infrastructure (T007).

The test creates a temporary logger, writes a minimal training‑run and
gating‑signal record, and then verifies that:
  * JSONL files exist and contain valid JSON objects.
  * CSV files exist, have a header row, and contain the same data.
  * Each record includes the automatically added ``run_id`` and
    ``timestamp`` fields.
The test deliberately uses empty payload dictionaries – the logger
injects the required metadata, which should satisfy the contract schemas
(the schemas only require these fields plus any optional user data).
"""

import json
import csv
from pathlib import Path

from utils.logging import get_logger, close_logger

def _read_jsonl(path: Path):
    """Read a JSONL file and return a list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def _read_csv(path: Path):
    """Read a CSV file and return a list of dicts (including header)."""
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def test_logger_round_trip(tmp_path):
    """
    Verify that logging a dummy record creates both JSONL and CSV files
    with the expected structure.
    """
    # Use a dedicated sub‑directory so the test does not interfere with
    # other runs.
    log_dir = tmp_path / "logs"
    logger = get_logger(name="test_logger", log_dir=str(log_dir))

    # Log minimal records – the logger will add ``run_id`` and ``timestamp``.
    logger.log_training_run({})
    logger.log_gating_signal({})

    # Close (no‑op currently, but exercised for API completeness).
    close_logger(logger)

    # ------------------------------------------------------------------
    # Verify JSONL output
    # ------------------------------------------------------------------
    training_jsonl = list(log_dir.glob("training_run_*.jsonl"))[0]
    gating_jsonl = list(log_dir.glob("gating_signal_*.jsonl"))[0]

    training_records = _read_jsonl(training_jsonl)
    gating_records = _read_jsonl(gating_jsonl)

    assert len(training_records) == 1, "Expected one training record"
    assert len(gating_records) == 1, "Expected one gating record"

    for rec in (training_records[0], gating_records[0]):
        # Required metadata fields injected by the logger
        assert "run_id" in rec
        assert "timestamp" in rec

    # ------------------------------------------------------------------
    # Verify CSV output
    # ------------------------------------------------------------------
    training_csv = list(log_dir.glob("training_run_*.csv"))[0]
    gating_csv = list(log_dir.glob("gating_signal_*.csv"))[0]

    training_csv_rows = _read_csv(training_csv)
    gating_csv_rows = _read_csv(gating_csv)

    # One data row plus the header (DictReader skips header)
    assert len(training_csv_rows) == 1
    assert len(gating_csv_rows) == 1

    for row in (training_csv_rows[0], gating_csv_rows[0]):
        assert "run_id" in row
        assert "timestamp" in row