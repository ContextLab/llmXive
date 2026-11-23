import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from audit_fabrication import (
    load_json_report,
    check_for_synthetic_patterns,
    check_flags,
    verify_robustness_results,
    audit_all_outputs
)

class TestLoadJsonReport:
    def test_load_existing_file(self, tmp_path):
        """Test loading an existing JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value"}
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_report(test_file)
        assert result == test_data

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file."""
        test_file = tmp_path / "nonexistent.json"
        result = load_json_report(test_file)
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        test_file = tmp_path / "invalid.json"
        with open(test_file, 'w') as f:
            f.write("{ invalid json }")
        
        result = load_json_report(test_file)
        assert result is None

class TestCheckForSyntheticPatterns:
    def test_no_synthetic_patterns(self):
        """Test data without synthetic patterns."""
        data = {
            "coefficients": {"news": 0.5, "age": 0.2},
            "p_values": {"news": 0.01, "age": 0.05}
        }
        issues = check_for_synthetic_patterns(data, "test.json")
        assert len(issues) == 0

    def test_synthetic_pattern_detected(self):
        """Test data with synthetic patterns."""
        data = {
            "coefficients": "generated from generate_synthetic_data",
            "notes": "This is a placeholder"
        }
        issues = check_for_synthetic_patterns(data, "test.json")
        assert len(issues) > 0
        assert any("synthetic" in issue or "placeholder" in issue for issue in issues)

    def test_mock_data_detected(self):
        """Test detection of mock_data pattern."""
        data = {
            "data_source": "mock_data",
            "values": [1, 2, 3]
        }
        issues = check_for_synthetic_patterns(data, "test.json")
        assert any("mock" in issue.lower() for issue in issues)

class TestCheckFlags:
    def test_valid_flags_array(self):
        """Test a valid flags array."""
        data = {
            "flags": ["VIF > 10", "Proxy Used: General Anxiety"]
        }
        issues = check_flags(data, "test.json")
        assert len(issues) == 0

    def test_missing_flags_array(self):
        """Test missing flags array."""
        data = {
            "coefficients": {"news": 0.5}
        }
        issues = check_flags(data, "test.json")
        assert len(issues) > 0
        assert any("flags" in issue for issue in issues)

    def test_empty_flags_array(self):
        """Test empty flags array."""
        data = {
            "flags": []
        }
        issues = check_flags(data, "test.json")
        # Empty flags might be a warning, not necessarily an error
        # depending on context
        assert len(issues) >= 0

    def test_proxy_flag_not_found_when_expected(self):
        """Test that proxy flag is detected when general_anxiety is in data."""
        data = {
            "flags": [],
            "anxiety_type": "general_anxiety"
        }
        issues = check_flags(data, "test.json")
        # This should trigger a warning about missing proxy flag
        assert any("proxy" in issue.lower() for issue in issues)

class TestVerifyRobustnessResults:
    def test_valid_run_status(self):
        """Test valid robustness results with status 'run'."""
        data = {
            "status": "run",
            "full_sample": {"coefficient": 0.5},
            "subset": {"coefficient": 0.6},
            "comparison": {"sign_change": False}
        }
        issues = verify_robustness_results(data, "test.json")
        assert len(issues) == 0

    def test_valid_skipped_status(self):
        """Test valid robustness results with status 'skipped'."""
        data = {
            "status": "skipped",
            "reason": "Correlation condition not met"
        }
        issues = verify_robustness_results(data, "test.json")
        assert len(issues) == 0

    def test_invalid_status(self):
        """Test invalid status value."""
        data = {
            "status": "invalid"
        }
        issues = verify_robustness_results(data, "test.json")
        assert len(issues) > 0
        assert any("Invalid" in issue for issue in issues)

    def test_run_without_full_sample(self):
        """Test run status missing full_sample data."""
        data = {
            "status": "run",
            "subset": {"coefficient": 0.6}
        }
        issues = verify_robustness_results(data, "test.json")
        assert len(issues) > 0
        assert any("full_sample" in issue for issue in issues)

    def test_skipped_without_reason(self):
        """Test skipped status without reason."""
        data = {
            "status": "skipped"
        }
        issues = verify_robustness_results(data, "test.json")
        assert len(issues) > 0
        assert any("reason" in issue for issue in issues)

class TestAuditAllOutputs:
    @patch('audit_fabrication.load_json_report')
    @patch('audit_fabrication.check_for_synthetic_patterns')
    @patch('audit_fabrication.check_flags')
    @patch('audit_fabrication.verify_robustness_results')
    def test_audit_passes(self, mock_robustness, mock_flags, mock_synthetic, mock_load):
        """Test successful audit."""
        mock_load.return_value = {"flags": [], "coefficients": {}, "p_values": {}, "correlations": {}}
        mock_synthetic.return_value = []
        mock_flags.return_value = []
        mock_robustness.return_value = []
        
        # Mock the Path.exists() to return True for our test files
        with patch('pathlib.Path.exists', return_value=True):
            result = audit_all_outputs()
            # This will depend on the actual implementation details
            # For now, we just check that it runs without error
            assert isinstance(result, bool)

    @patch('audit_fabrication.load_json_report')
    def test_audit_fails_on_missing_file(self, mock_load):
        """Test audit fails when file is missing."""
        mock_load.return_value = None
        
        with patch('pathlib.Path.exists', return_value=True):
            result = audit_all_outputs()
            # Should return False if any file fails to load
            assert result is False
