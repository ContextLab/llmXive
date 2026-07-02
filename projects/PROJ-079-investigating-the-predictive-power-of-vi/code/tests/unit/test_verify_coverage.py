"""
Unit tests for coverage verification functionality.
"""
import pytest
import json
import tempfile
from pathlib import Path
from tests.verify_coverage import load_coverage_report, calculate_src_coverage, verify_coverage_threshold

class TestLoadCoverageReport:
    def test_load_valid_report(self, tmp_path):
        """Test loading a valid coverage report."""
        report_path = tmp_path / "coverage.json"
        report_data = {
            "files": {
                "src/test.py": {
                    "summary": {
                        "lines": {"total": 10, "covered": 8}
                    }
                }
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        loaded_data = load_coverage_report(report_path)
        assert loaded_data == report_data

    def test_load_missing_report(self, tmp_path):
        """Test loading a missing coverage report raises FileNotFoundError."""
        missing_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_coverage_report(missing_path)

class TestCalculateSrcCoverage:
    def test_calculate_coverage_basic(self):
        """Test basic coverage calculation."""
        coverage_data = {
            "files": {
                "src/module1.py": {
                    "summary": {
                        "lines": {"total": 20, "covered": 18}
                    }
                },
                "src/module2.py": {
                    "summary": {
                        "lines": {"total": 30, "covered": 27}
                    }
                },
                "tests/test_module.py": {
                    "summary": {
                        "lines": {"total": 10, "covered": 10}
                    }
                }
            }
        }
        
        coverage_pct = calculate_src_coverage(coverage_data)
        # Expected: (18+27)/(20+30) = 45/50 = 90%
        assert coverage_pct == 90.0

    def test_calculate_coverage_no_src_files(self):
        """Test coverage calculation with no src files raises ValueError."""
        coverage_data = {
            "files": {
                "tests/test_module.py": {
                    "summary": {
                        "lines": {"total": 10, "covered": 10}
                    }
                }
            }
        }
        
        with pytest.raises(ValueError, match="No files found in coverage report matching 'src'"):
            calculate_src_coverage(coverage_data)

    def test_calculate_coverage_zero_lines(self):
        """Test coverage calculation with zero executable lines raises ValueError."""
        coverage_data = {
            "files": {
                "src/empty.py": {
                    "summary": {
                        "lines": {"total": 0, "covered": 0}
                    }
                }
            }
        }
        
        with pytest.raises(ValueError, match="No executable lines found in src/ modules"):
            calculate_src_coverage(coverage_data)

class TestVerifyCoverageThreshold:
    def test_threshold_met(self):
        """Test threshold verification when coverage meets threshold."""
        assert verify_coverage_threshold(80.0) is True
        assert verify_coverage_threshold(85.5) is True
        assert verify_coverage_threshold(100.0) is True

    def test_threshold_not_met(self):
        """Test threshold verification when coverage is below threshold."""
        assert verify_coverage_threshold(79.9) is False
        assert verify_coverage_threshold(50.0) is False
        assert verify_coverage_threshold(0.0) is False

    def test_custom_threshold(self):
        """Test threshold verification with custom threshold."""
        assert verify_coverage_threshold(90.0, threshold=90.0) is True
        assert verify_coverage_threshold(89.9, threshold=90.0) is False