"""
Unit tests for T013b: Session validation metrics calculation.

These tests verify the logic of calculate_pass_rate and write_metrics
without requiring actual data ingestion (mocked data).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.session_validation_metrics import calculate_pass_rate, write_metrics

class TestSessionValidationMetrics:
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / 'data' / 'processed'
        self.data_dir.mkdir(parents=True)
        
        # Mock state file path
        self.mock_state_file = self.data_dir / 'session_validation_state.json'
        
        # Patch project_root in the module
        self.original_project_root = None
        # We will patch the module's project_root variable directly in tests

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_calculate_pass_rate_with_valid_data(self):
        """Test pass rate calculation with valid distinct sessions."""
        # Create mock validation data
        mock_data = {
            "total_subjects_checked": 100,
            "distinct_session_count": 95,
            "duplicate_session_ids": ["sub-001_ses-01", "sub-001_ses-02"],
            "excluded_subjects": ["sub-001"]
        }
        
        # Write mock data to temp file
        with open(self.mock_state_file, 'w') as f:
            json.dump(mock_data, f)
        
        # Temporarily override the module's project_root
        import code.session_validation_metrics as module
        original_project_root = module.project_root
        module.project_root = Path(self.test_dir)
        
        try:
            metrics = calculate_pass_rate()
            
            assert metrics['total_subjects_checked'] == 100
            assert metrics['subjects_with_distinct_sessions'] == 95
            assert metrics['pass_rate_percent'] == 95.0
            assert metrics['subjects_excluded'] == 1
            assert metrics['status'] == 'passed'
        finally:
            module.project_root = original_project_root

    def test_calculate_pass_rate_with_zero_pass_rate(self):
        """Test pass rate calculation when no subjects pass."""
        mock_data = {
            "total_subjects_checked": 50,
            "distinct_session_count": 0,
            "duplicate_session_ids": ["sub-001_ses-01", "sub-001_ses-02", "sub-002_ses-01", "sub-002_ses-02"],
            "excluded_subjects": ["sub-001", "sub-002"]
        }
        
        with open(self.mock_state_file, 'w') as f:
            json.dump(mock_data, f)
        
        import code.session_validation_metrics as module
        original_project_root = module.project_root
        module.project_root = Path(self.test_dir)
        
        try:
            metrics = calculate_pass_rate()
            
            assert metrics['pass_rate_percent'] == 0.0
            assert metrics['status'] == 'failed'
            assert metrics['subjects_excluded'] == 2
        finally:
            module.project_root = original_project_root

    def test_calculate_pass_rate_with_no_data(self):
        """Test pass rate calculation when no subjects were checked."""
        mock_data = {
            "total_subjects_checked": 0,
            "distinct_session_count": 0,
            "duplicate_session_ids": [],
            "excluded_subjects": []
        }
        
        with open(self.mock_state_file, 'w') as f:
            json.dump(mock_data, f)
        
        import code.session_validation_metrics as module
        original_project_root = module.project_root
        module.project_root = Path(self.test_dir)
        
        try:
            metrics = calculate_pass_rate()
            
            assert metrics['pass_rate_percent'] == 0.0
            assert metrics['status'] == 'no_data'
            assert metrics['total_subjects_checked'] == 0
        finally:
            module.project_root = original_project_root

    def test_calculate_pass_rate_missing_file(self):
        """Test that FileNotFoundError is raised when state file is missing."""
        # Ensure the file does not exist
        if self.mock_state_file.exists():
            self.mock_state_file.unlink()
        
        import code.session_validation_metrics as module
        original_project_root = module.project_root
        module.project_root = Path(self.test_dir)
        
        try:
            with pytest.raises(FileNotFoundError):
                calculate_pass_rate()
        finally:
            module.project_root = original_project_root

    def test_write_metrics_creates_file(self):
        """Test that write_metrics creates the output file."""
        metrics = {
            "pass_rate_percent": 90.0,
            "total_subjects_checked": 100,
            "subjects_with_distinct_sessions": 90,
            "subjects_excluded": 10,
            "excluded_count": 10,
            "status": "passed"
        }
        
        output_path = write_metrics(metrics)
        
        assert output_path.exists()
        assert output_path.suffix == '.json'
        
        # Verify content
        with open(output_path, 'r') as f:
            written_data = json.load(f)
        
        assert written_data['pass_rate_percent'] == 90.0
        assert written_data['status'] == 'passed'

    def test_write_metrics_ensures_directory_exists(self):
        """Test that write_metrics creates the output directory if missing."""
        metrics = {
            "pass_rate_percent": 50.0,
            "total_subjects_checked": 10,
            "subjects_with_distinct_sessions": 5,
            "subjects_excluded": 5,
            "excluded_count": 5,
            "status": "passed"
        }
        
        # Remove the directory
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)
        
        import code.session_validation_metrics as module
        original_project_root = module.project_root
        module.project_root = Path(self.test_dir)
        
        try:
            output_path = write_metrics(metrics)
            assert output_path.parent.exists()
        finally:
            module.project_root = original_project_root
