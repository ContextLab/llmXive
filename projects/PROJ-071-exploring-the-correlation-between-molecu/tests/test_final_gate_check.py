"""
Unit tests for Final Gate Check (T057)
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from final_gate_check import get_project_root, check_gate_status, check_report_branching


class TestCheckGateStatus:
    """Tests for check_gate_status function"""

    def test_missing_file(self, tmp_path):
        """Test behavior when gate_status.json is missing"""
        gate_path = tmp_path / 'nonexistent.json'
        is_valid, data, message = check_gate_status(gate_path)
        
        assert is_valid is False
        assert data is None
        assert 'not found' in message.lower()

    def test_invalid_json(self, tmp_path):
        """Test behavior with invalid JSON"""
        gate_path = tmp_path / 'gate_status.json'
        gate_path.write_text('not valid json')
        
        is_valid, data, message = check_gate_status(gate_path)
        
        assert is_valid is False
        assert 'invalid json' in message.lower()

    def test_missing_required_fields(self, tmp_path):
        """Test behavior when required fields are missing"""
        gate_path = tmp_path / 'gate_status.json'
        gate_path.write_text(json.dumps({'gate_outcome': 'PASS'}))
        
        is_valid, data, message = check_gate_status(gate_path)
        
        assert is_valid is False
        assert 'missing required fields' in message.lower()

    def test_invalid_gate_outcome(self, tmp_path):
        """Test behavior with invalid gate_outcome value"""
        gate_path = tmp_path / 'gate_status.json'
        data = {
            'gate_outcome': 'INVALID',
            'n_records': 50,
            'gate_passed': True
        }
        gate_path.write_text(json.dumps(data))
        
        is_valid, result_data, message = check_gate_status(gate_path)
        
        assert is_valid is False
        assert 'invalid gate_outcome' in message.lower()

    def test_gate_passed_not_boolean(self, tmp_path):
        """Test behavior when gate_passed is not a boolean"""
        gate_path = tmp_path / 'gate_status.json'
        data = {
            'gate_outcome': 'PASS',
            'n_records': 50,
            'gate_passed': 'true'  # String instead of boolean
        }
        gate_path.write_text(json.dumps(data))
        
        is_valid, result_data, message = check_gate_status(gate_path)
        
        assert is_valid is False
        assert 'must be a boolean' in message.lower()

    def test_consistency_check_pass(self, tmp_path):
        """Test consistency check for PASS outcome"""
        gate_path = tmp_path / 'gate_status.json'
        data = {
            'gate_outcome': 'PASS',
            'n_records': 50,
            'gate_passed': True
        }
        gate_path.write_text(json.dumps(data))
        
        is_valid, result_data, message = check_gate_status(gate_path)
        
        assert is_valid is True
        assert 'Gate status valid' in message

    def test_consistency_check_fail(self, tmp_path):
        """Test consistency check for FAIL outcome"""
        gate_path = tmp_path / 'gate_status.json'
        data = {
            'gate_outcome': 'FAIL',
            'n_records': 20,
            'gate_passed': False
        }
        gate_path.write_text(json.dumps(data))
        
        is_valid, result_data, message = check_gate_status(gate_path)
        
        assert is_valid is True
        assert 'Gate status valid' in message

    def test_inconsistent_passed_and_outcome(self, tmp_path):
        """Test detection of inconsistent gate_passed and gate_outcome"""
        gate_path = tmp_path / 'gate_status.json'
        data = {
            'gate_outcome': 'FAIL',
            'n_records': 20,
            'gate_passed': True  # Inconsistent!
        }
        gate_path.write_text(json.dumps(data))
        
        is_valid, result_data, message = check_gate_status(gate_path)
        
        assert is_valid is False
        assert 'Inconsistent' in message


class TestCheckReportBranching:
    """Tests for check_report_branching function"""

    def test_gate_passed_no_results_report(self, tmp_path):
        """Test when gate passed but results_report.md is missing"""
        gate_data = {
            'gate_outcome': 'PASS',
            'n_records': 50,
            'gate_passed': True
        }
        
        is_valid, message = check_report_branching(tmp_path, True, gate_data)
        
        assert is_valid is False
        assert 'results_report.md not found' in message

    def test_gate_passed_with_results_report(self, tmp_path):
        """Test when gate passed and results_report.md exists"""
        results_report = tmp_path / 'results_report.md'
        results_report.write_text('# Results Report\n\nData Availability Gate: PASS (N=50)')
        
        gate_data = {
            'gate_outcome': 'PASS',
            'n_records': 50,
            'gate_passed': True
        }
        
        is_valid, message = check_report_branching(tmp_path, True, gate_data)
        
        assert is_valid is True
        assert 'Correct branching' in message

    def test_gate_failed_no_insufficiency_report(self, tmp_path):
        """Test when gate failed but data_insufficiency_report.md is missing"""
        gate_data = {
            'gate_outcome': 'FAIL',
            'n_records': 20,
            'gate_passed': False
        }
        
        is_valid, message = check_report_branching(tmp_path, False, gate_data)
        
        assert is_valid is False
        assert 'data_insufficiency_report.md not found' in message

    def test_gate_failed_with_insufficiency_report(self, tmp_path):
        """Test when gate failed and data_insufficiency_report.md exists"""
        insufficiency_report = tmp_path / 'data_insufficiency_report.md'
        insufficiency_report.write_text('# Data Insufficiency Report\n\nGate: FAIL (N=20)')
        
        gate_data = {
            'gate_outcome': 'FAIL',
            'n_records': 20,
            'gate_passed': False
        }
        
        is_valid, message = check_report_branching(tmp_path, False, gate_data)
        
        assert is_valid is True
        assert 'Correct branching' in message

    def test_empty_results_report(self, tmp_path):
        """Test when results_report.md exists but is empty"""
        results_report = tmp_path / 'results_report.md'
        results_report.write_text('')
        
        gate_data = {
            'gate_outcome': 'PASS',
            'n_records': 50,
            'gate_passed': True
        }
        
        is_valid, message = check_report_branching(tmp_path, True, gate_data)
        
        assert is_valid is False
        assert 'empty' in message.lower()

    def test_empty_insufficiency_report(self, tmp_path):
        """Test when data_insufficiency_report.md exists but is empty"""
        insufficiency_report = tmp_path / 'data_insufficiency_report.md'
        insufficiency_report.write_text('')
        
        gate_data = {
            'gate_outcome': 'FAIL',
            'n_records': 20,
            'gate_passed': False
        }
        
        is_valid, message = check_report_branching(tmp_path, False, gate_data)
        
        assert is_valid is False
        assert 'empty' in message.lower()


class TestGetProjectRoot:
    """Tests for get_project_root function"""

    def test_returns_path(self):
        """Test that get_project_root returns a Path object"""
        root = get_project_root()
        assert isinstance(root, Path)
        
    def test_root_exists(self):
        """Test that the returned path exists"""
        root = get_project_root()
        assert root.exists()