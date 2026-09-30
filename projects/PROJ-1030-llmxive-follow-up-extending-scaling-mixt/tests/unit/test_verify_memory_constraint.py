"""
Unit tests for the memory constraint verification logic (T040).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.verify_memory_constraint import (
    load_memory_log,
    analyze_memory_usage,
    generate_verification_report,
    MEMORY_LIMIT_MB
)

class TestLoadMemoryLog:
    def test_load_valid_log(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"clip_id": "c1", "peak_mb": 1000}], f)
            temp_path = Path(f.name)

        try:
            data = load_memory_log(temp_path)
            assert len(data) == 1
            assert data[0]["clip_id"] == "c1"
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_memory_log(Path("/nonexistent/path/log.json"))

    def test_load_empty_log(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_path = Path(f.name)

        try:
            data = load_memory_log(temp_path)
            assert data == []
        finally:
            os.unlink(temp_path)

class TestAnalyzeMemoryUsage:
    def test_all_within_limit(self):
        entries = [
            {"clip_id": "c1", "peak_mb": 5000, "stage": "start"},
            {"clip_id": "c2", "peak_mb": 6000, "stage": "end"}
        ]
        passed, peak, violations = analyze_memory_usage(entries)
        assert passed is True
        assert peak == 6000
        assert len(violations) == 0

    def test_violation_detected(self):
        # 7GB = 7168 MB
        entries = [
            {"clip_id": "c1", "peak_mb": 5000, "stage": "start"},
            {"clip_id": "c2", "peak_mb": 8000, "stage": "end"} # Violation
        ]
        passed, peak, violations = analyze_memory_usage(entries)
        assert passed is False
        assert peak == 8000
        assert len(violations) == 1
        assert violations[0]["clip_id"] == "c2"
        assert violations[0]["overage_mb"] == 8000 - MEMORY_LIMIT_MB

    def test_empty_log(self):
        passed, peak, violations = analyze_memory_usage([])
        assert passed is False
        assert peak == 0.0
        assert len(violations) == 1 # Reports empty log as a failure condition

class TestGenerateVerificationReport:
    def test_report_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            report = generate_verification_report(
                passed=True,
                global_peak_mb=5000.0,
                violations=[],
                log_path="test.json",
                output_path=str(output_path)
            )

            assert report["status"] == "PASS"
            assert report["global_peak_memory_mb"] == 5000.0
            assert "violations" in report
            assert report["violations_found"] == 0

            # Verify file was written
            assert output_path.exists()
            with open(output_path, 'r') as f:
                written_data = json.load(f)
            assert written_data["status"] == "PASS"