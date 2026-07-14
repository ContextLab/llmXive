"""
Unit tests for the reproducibility reporting utility (metrics.py).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.metrics import (
    get_git_commit,
    get_file_checksum,
    get_resource_usage,
    generate_report,
    save_report,
    PROJECT_ROOT
)


class TestGetGitCommit:
    def test_git_commit_returns_string(self):
        commit = get_git_commit()
        assert isinstance(commit, str)
        # In a real repo, it's 40 hex chars, but we just ensure it's not empty/exception
        assert len(commit) >= 1 or commit == "unknown"


class TestGetFileChecksum:
    def test_checksum_of_existing_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            checksum = get_file_checksum(tmp_path)
            assert isinstance(checksum, str)
            assert len(checksum) == 32  # MD5 hex length
        finally:
            os.unlink(tmp_path)

    def test_checksum_of_missing_file(self):
        checksum = get_file_checksum(Path("/nonexistent/file.txt"))
        assert checksum == "missing"


class TestGetResourceUsage:
    def test_resource_usage_returns_dict(self):
        usage = get_resource_usage()
        assert isinstance(usage, dict)
        assert "peak_ram_mb" in usage
        assert "current_ram_mb" in usage
        assert "unit" in usage
        assert usage["unit"] == "MB"
        assert isinstance(usage["peak_ram_mb"], float)
        assert usage["peak_ram_mb"] >= 0


class TestGenerateReport:
    def test_report_structure(self):
        report = generate_report()
        
        # Check top-level keys
        assert "report_generated_at" in report
        assert "git_commit" in report
        assert "environment" in report
        assert "execution" in report
        assert "artifacts" in report
        assert "validation_metrics" in report
        assert "metadata" in report

        # Check nested structures
        assert "python_version" in report["environment"]
        assert "packages" in report["environment"]
        assert "wall_clock_start" in report["execution"]
        assert "duration_seconds" in report["execution"]
        assert "checksums" in report["artifacts"]

    def test_report_with_extra_metadata(self):
        extra = {"test_key": "test_value", "number": 123}
        report = generate_report(extra_metadata=extra)
        
        assert report["metadata"]["test_key"] == "test_value"
        assert report["metadata"]["number"] == 123

    def test_report_duration_calculation(self):
        start = 1000.0
        end = 1005.0
        report = generate_report(wall_clock_start=start, wall_clock_end=end)
        assert report["execution"]["duration_seconds"] == 5.0


class TestSaveReport:
    def test_save_report_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            result_path = save_report(output_path=output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            
            with open(output_path, "r") as f:
                data = json.load(f)
            assert "report_generated_at" in data

    def test_save_report_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            deep_path = Path(tmpdir) / "deep" / "nested" / "report.json"
            result_path = save_report(output_path=deep_path)
            
            assert deep_path.exists()
            assert deep_path == result_path

    def test_save_report_serializes_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"
            save_report(output_path=output_path)
            
            with open(output_path, "r") as f:
                # Should not raise JSONDecodeError
                data = json.load(f)
            assert isinstance(data, dict)
