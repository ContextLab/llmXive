"""
Unit and Integration tests for T016c: Verify Validation Report Generation.

This test suite ensures that:
1. The script runs without errors.
2. The generated YAML is valid and matches the expected schema.
3. The --mock flag correctly generates a mock input file.
"""
import os
import sys
import json
import yaml
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code/ to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.generate_validation_report import (
    load_ingestion_status,
    generate_validation_report,
    save_report,
    main
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

class TestValidationReportGeneration:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories for each test."""
        self.tmp_dir = tmp_path
        self.input_file = self.tmp_dir / ".ingestion_status.json"
        self.output_file = self.tmp_dir / "validation_report.yaml"
        yield
    
    def test_load_ingestion_status_valid(self):
        """Test loading a valid JSON status file."""
        mock_data = {
            "threshold_status": "N>=100",
            "exact_N": 120,
            "excluded_count": 5,
            "power_limitation_warning": None
        }
        self.input_file.write_text(json.dumps(mock_data))
        
        result = load_ingestion_status(self.input_file)
        
        assert result == mock_data
        assert result["threshold_status"] == "N>=100"
        assert result["exact_N"] == 120

    def test_load_ingestion_status_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_ingestion_status(self.tmp_dir / "nonexistent.json")

    def test_generate_validation_report_mapping(self):
        """Test that the report generation correctly maps fields."""
        input_data = {
            "threshold_status": "50<=N<100",
            "exact_N": 85,
            "excluded_count": 10,
            "power_limitation_warning": "Power limitation warning"
        }
        
        report = generate_validation_report(input_data)
        
        assert report["status"] == "50<=N<100"
        assert report["count"] == 85
        assert report["excluded_count"] == 10
        assert report["power_limitation_warning"] == "Power limitation warning"

    def test_generate_validation_report_default_excluded_count(self):
        """Test that excluded_count defaults to 0 if missing."""
        input_data = {
            "threshold_status": "N>=100",
            "exact_N": 100
        }
        
        report = generate_validation_report(input_data)
        
        assert report["excluded_count"] == 0

    def test_save_report_creates_yaml(self):
        """Test that saving the report creates a valid YAML file."""
        report_data = {
            "status": "N>=100",
            "count": 100,
            "excluded_count": 0,
            "power_limitation_warning": None
        }
        
        saved_path = save_report(report_data, self.output_file)
        
        assert saved_path.exists()
        assert saved_path == self.output_file
        
        # Verify YAML content
        with open(saved_path, 'r', encoding='utf-8') as f:
            loaded_report = yaml.safe_load(f)
        
        assert loaded_report == report_data

    def test_main_success_path(self, caplog):
        """Test the main function success path with valid input."""
        mock_data = {
            "threshold_status": "N>=100",
            "exact_N": 150,
            "excluded_count": 2,
            "power_limitation_warning": None
        }
        self.input_file.write_text(json.dumps(mock_data))
        
        # Mock sys.argv to simulate command line arguments
        with patch.object(sys, 'argv', ['script', '--input', str(self.input_file), '--output', str(self.output_file)]):
            exit_code = main()
        
        assert exit_code == 0
        assert self.output_file.exists()
        
        # Verify content
        with open(self.output_file, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f)
        
        assert result["status"] == "N>=100"
        assert result["count"] == 150

    def test_main_mock_flag_creates_mock_file(self, caplog):
        """Test that --mock flag creates a mock file when input is missing."""
        # Ensure input file does NOT exist
        assert not self.input_file.exists()
        
        with patch.object(sys, 'argv', [
            'script', 
            '--input', str(self.input_file), 
            '--output', str(self.output_file),
            '--mock'
        ]):
            exit_code = main()
        
        assert exit_code == 0
        # Verify mock file was created
        assert self.input_file.exists()
        
        # Verify output file was created
        assert self.output_file.exists()
        
        # Verify output content matches mock schema
        with open(self.output_file, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f)
        
        assert "status" in result
        assert "count" in result

    def test_main_invalid_json(self):
        """Test main function behavior with invalid JSON input."""
        self.input_file.write_text("not valid json {{{")
        
        with patch.object(sys, 'argv', ['script', '--input', str(self.input_file)]):
            exit_code = main()
        
        assert exit_code == 1

    def test_main_invalid_yaml_write(self, caplog):
        """Test main function behavior if YAML write fails (simulated)."""
        mock_data = {
            "threshold_status": "N>=100",
            "exact_N": 100,
            "excluded_count": 0,
            "power_limitation_warning": None
        }
        self.input_file.write_text(json.dumps(mock_data))
        
        # Simulate a failure in yaml.dump by patching save_report
        with patch('ingestion.generate_validation_report.save_report') as mock_save:
            mock_save.side_effect = yaml.YAMLError("Write error")
            
            with patch.object(sys, 'argv', ['script', '--input', str(self.input_file), '--output', str(self.output_file)]):
                exit_code = main()
        
        assert exit_code == 1