"""Skeleton tests for T001: help exits 0 and the pipeline writes artifacts."""

import csv
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_COLUMNS = [
    "query_id",
    "source_type",
    "complexity_level",
    "latency_ms",
    "timestamp",
    "translation_error",
    "success_flag",
    "timeout_flag",
    "synthetic_flag",
    "throttling_mode",
]


def test_main_help_exits_zero():
    result = subprocess.run(
        [sys.executable, "-m", "code.main", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr


def test_execution_log_csv_exists_with_columns():
    csv_path = PROJECT_ROOT / "data" / "processed" / "execution_logs.csv"
    assert csv_path.is_file(), "run `python -m code.main` first"
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == EXPECTED_COLUMNS


def test_run_manifest_exists():
    manifest_path = PROJECT_ROOT / "data" / "results" / "pipeline_manifest.json"
    assert manifest_path.is_file(), "run `python -m code.main` first"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["num_queries"] > 0
    assert len(manifest["execution_log_sha256"]) == 64