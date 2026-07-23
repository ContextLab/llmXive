"""
Unit tests for T023a: Cognitive Data Gate logic.
Tests the decision logic without relying on real files.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from stats.cognitive_gate import check_cognitive_availability, load_download_report


class TestCognitiveGateLogic:
    """Test the core logic of the cognitive gate."""

    def test_all_missing_cognitive(self):
        """Case where all records are missing cognitive data -> BLOCKED."""
        report = {
            "valid_count": 10,
            "invalid_instrument_count": 0,
            "missing_cognitive_count": 10,
            "total_count": 10
        }
        result = check_cognitive_availability(report)
        assert result["status"] == "BLOCKED"
        assert "No linked cognitive data found" in result["reason"]

    def test_some_cognitive_data(self):
        """Case where some records have cognitive data -> PROCEED."""
        report = {
            "valid_count": 10,
            "invalid_instrument_count": 0,
            "missing_cognitive_count": 5,
            "total_count": 15
        }
        result = check_cognitive_availability(report)
        assert result["status"] == "PROCEED"
        assert "Cognitive data available" in result["reason"]

    def test_empty_corpus(self):
        """Case where total_count is 0 -> BLOCKED."""
        report = {
            "valid_count": 0,
            "invalid_instrument_count": 0,
            "missing_cognitive_count": 0,
            "total_count": 0
        }
        result = check_cognitive_availability(report)
        assert result["status"] == "BLOCKED"
        assert "No records found" in result["reason"]

    def test_no_missing_cognitive(self):
        """Case where no records are missing cognitive data -> PROCEED."""
        report = {
            "valid_count": 20,
            "invalid_instrument_count": 0,
            "missing_cognitive_count": 0,
            "total_count": 20
        }
        result = check_cognitive_availability(report)
        assert result["status"] == "PROCEED"

class TestLoadReport:
    """Test loading the report file."""

    def test_load_valid_report(self):
        """Successfully load a valid report file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "valid_count": 5,
                "invalid_instrument_count": 1,
                "missing_cognitive_count": 2,
                "total_count": 8
            }, f)
            temp_path = f.name

        try:
            # Temporarily override the global path for testing
            import stats.cognitive_gate as cg
            original_path = cg.REPORT_PATH
            cg.REPORT_PATH = Path(temp_path)
            
            try:
                data = load_download_report()
                assert data["total_count"] == 8
                assert data["missing_cognitive_count"] == 2
            finally:
                cg.REPORT_PATH = original_path
        finally:
            os.unlink(temp_path)

    def test_load_invalid_schema(self):
        """Fail when report is missing required keys."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "valid_count": 5,
                "total_count": 5
                # Missing other keys
            }, f)
            temp_path = f.name

        try:
            import stats.cognitive_gate as cg
            original_path = cg.REPORT_PATH
            cg.REPORT_PATH = Path(temp_path)
            
            try:
                with pytest.raises(SystemExit):
                    load_download_report()
            finally:
                cg.REPORT_PATH = original_path
        finally:
            os.unlink(temp_path)
