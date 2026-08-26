import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions from the module
# Assuming the module is in code/ directory
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from generate_preprocessing_stats import load_subject_logs, calculate_stats

def test_load_subject_logs_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        logs = load_subject_logs(Path(tmpdir))
        assert logs == []

def test_load_subject_logs_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "preprocess_subj_001.log"
        data = {"subject_id": "subj_001", "status": "success", "runtime_seconds": 10.5, "ram_mb": 2048}
        with open(log_file, 'w') as f:
            json.dump(data, f)

        logs = load_subject_logs(Path(tmpdir))
        assert len(logs) == 1
        assert logs[0]["subject_id"] == "subj_001"
        assert logs[0]["status"] == "success"

def test_calculate_stats_basic():
    logs = [
        {"status": "success", "runtime_seconds": 10.0, "ram_mb": 1000},
        {"status": "success", "runtime_seconds": 20.0, "ram_mb": 2000},
        {"status": "failed", "runtime_seconds": 5.0, "ram_mb": 500}
    ]
    stats = calculate_stats(logs)

    assert stats["total_subjects"] == 3
    assert stats["successful_subjects"] == 2
    assert stats["failed_subjects"] == 1
    assert stats["total_runtime_seconds"] == 35.0
    assert stats["peak_ram_mb"] == 2000.0
    assert stats["peak_ram_gb"] == 2000.0 / 1024.0
    assert abs(stats["success_rate"] - (2/3)) < 0.001

def test_calculate_stats_empty():
    stats = calculate_stats([])
    assert stats["total_subjects"] == 0
    assert stats["success_rate"] == 0.0