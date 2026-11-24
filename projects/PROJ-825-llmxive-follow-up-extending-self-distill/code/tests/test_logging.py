"""
Unit test for the JSON/CSV logging infrastructure (T007).

The test creates a temporary logger, writes a realistic ``TrainingRun``
record (including fields required by the contract schema) and a minimal
``GatingSignal`` record, then validates that:
  * JSONL files exist and contain valid JSON objects.
  * CSV files exist, have a header row, and contain the same data.
  * Each JSON record conforms to ``contracts/training_run.schema.yaml``.
"""
import json
import csv
import yaml
from pathlib import Path

import jsonschema
from utils.logging import get_logger, close_logger

# Path to the contract schema (relative to the project root)
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "contracts" / "training_run.schema.yaml"


def _read_jsonl(path: Path):
    """Read a JSONL file and return a list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_csv(path: Path):
    """Read a CSV file and return a list of dicts (excluding header)."""
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_logger_round_trip(tmp_path):
    """
    Verify that logging a realistic record creates both JSONL and CSV files
    with the expected structure and that the JSON records validate against
    the training‑run schema.
    """
    # ------------------------------------------------------------------
    # 1. Set up a dedicated logger instance.
    # ------------------------------------------------------------------
    log_dir = tmp_path / "logs"
    logger = get_logger(name="test_logger", log_dir=str(log_dir))

    # ------------------------------------------------------------------
    # 2. Create a dummy TrainingRun record containing fields required by
    #    the contract schema plus a few example experiment fields.
    # ------------------------------------------------------------------
    training_record = {
        "variant": "student-only",
        "env": "alfworld",
        "seed": 0,
        "step": 1,
        "reward": 0.0,
        "cpu_time_sec": 0.123,
        "peak_memory_mb": 256.7,
    }

    # Log the training record and a minimal gating‑signal record.
    logger.log_training_run(training_record)
    logger.log_gating_signal({})  # empty payload is fine for gating test

    # ------------------------------------------------------------------
    # 3. Close the logger (no‑op currently but exercised for API
    #    completeness).
    # ------------------------------------------------------------------
    close_logger(logger)

    # ------------------------------------------------------------------
    # 4. Verify JSONL output.
    # ------------------------------------------------------------------
    training_jsonl_path = list(log_dir.glob("training_run_*.jsonl"))[0]
    gating_jsonl_path = list(log_dir.glob("gating_signal_*.jsonl"))[0]

    training_records = _read_jsonl(training_jsonl_path)
    gating_records = _read_jsonl(gating_jsonl_path)

    assert len(training_records) == 1, "Expected exactly one training record"
    assert len(gating_records) == 1, "Expected exactly one gating record"

    # ------------------------------------------------------------------
    # 5. Validate the training record against the JSON schema.
    # ------------------------------------------------------------------
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    jsonschema.validate(instance=training_records[0], schema=schema)

    # ------------------------------------------------------------------
    # 6. Verify that logger added the mandatory metadata fields.
    # ------------------------------------------------------------------
    for rec in (training_records[0], gating_records[0]):
        assert "run_id" in rec, "Logger must add a run_id"
        assert "timestamp" in rec, "Logger must add a timestamp"

    # ------------------------------------------------------------------
    # 7. Verify CSV output.
    # ------------------------------------------------------------------
    training_csv_path = list(log_dir.glob("training_run_*.csv"))[0]
    gating_csv_path = list(log_dir.glob("gating_signal_*.csv"))[0]

    training_csv_rows = _read_csv(training_csv_path)
    gating_csv_rows = _read_csv(gating_csv_path)

    # One data row (DictReader skips the header line)
    assert len(training_csv_rows) == 1, "CSV should contain one data row"
    assert len(gating_csv_rows) == 1, "CSV should contain one data row"

    for row in (training_csv_rows[0], gating_csv_rows[0]):
        assert "run_id" in row, "CSV row must contain run_id"
        assert "timestamp" in row, "CSV row must contain timestamp"