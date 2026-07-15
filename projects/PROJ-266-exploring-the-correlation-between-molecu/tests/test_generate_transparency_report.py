"""
Unit tests for the generate_transparency_report.py script.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.generate_transparency_report import (
    load_deviation_record,
    scan_execution_logs,
    gather_artifacts,
    generate_report,
    write_report,
    main
)


class TestLoadDeviationRecord:
    def test_load_existing_record(self, tmp_path):
        """Test loading an existing deviation record."""
        # Create a mock deviation record
        deviation_data = {
            "project_id": "TEST-001",
            "deviations": [
                {
                    "id": "DEV-001",
                    "description": "Test deviation",
                    "justification": "Test justification"
                }
            ]
        }

        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        deviation_file = state_dir / "TEST-001.yaml"

        with open(deviation_file, 'w') as f:
            yaml.dump(deviation_data, f)

        # Mock get_project_root to return tmp_path
        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            result = load_deviation_record()

        assert result["project_id"] == "TEST-001"
        assert len(result["deviations"]) == 1
        assert result["deviations"][0]["id"] == "DEV-001"

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when record is missing."""
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)

        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            with pytest.raises(FileNotFoundError):
                load_deviation_record()


class TestScanExecutionLogs:
    def test_scan_empty_logs_dir(self, tmp_path):
        """Test scanning an empty logs directory."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            result = scan_execution_logs()

        assert result == []

    def test_scan_log_files(self, tmp_path):
        """Test scanning log files."""
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        # Create a mock log file
        log_file = logs_dir / "test.log"
        log_content = """{"script": "test_script.py", "status": "success"}
        {"script": "test_script2.py", "status": "failed"}"""

        with open(log_file, 'w') as f:
            f.write(log_content)

        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            result = scan_execution_logs()

        assert len(result) >= 2
        assert any("test_script.py" in str(entry) for entry in result)


class TestGatherArtifacts:
    def test_gather_from_mock_structure(self, tmp_path):
        """Test gathering artifacts from a mock project structure."""
        # Create mock structure
        code_dir = tmp_path / "code"
        data_dir = tmp_path / "data"
        code_dir.mkdir()
        data_dir.mkdir()

        # Create mock files
        (code_dir / "script.py").touch()
        (data_dir / "data.csv").touch()
        (tmp_path / "config.yaml").touch()

        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            result = gather_artifacts()

        assert len(result["scripts"]) >= 1
        assert len(result["data_files"]) >= 1
        assert len(result["configs"]) >= 1


class TestGenerateReport:
    def test_generate_report_content(self):
        """Test that report generation produces valid markdown."""
        deviation_record = {
            "deviations": [
                {
                    "id": "DEV-001",
                    "description": "Test",
                    "justification": "Reason"
                }
            ]
        }
        logs = [{"source_file": "test.log"}]
        artifacts = {
            "scripts": [{"path": "test.py", "size_bytes": 100, "modified": "2026-01-01"}],
            "data_files": [],
            "configs": []
        }

        report = generate_report(deviation_record, logs, artifacts)

        assert "Computational Method Transparency" in report
        assert "DEV-001" in report
        assert "Test" in report
        assert "test.py" in report


class TestWriteReport:
    def test_write_report_to_file(self, tmp_path):
        """Test writing report to a file."""
        report_content = "# Test Report\n\nContent here."
        output_path = tmp_path / "report.md"

        write_report(report_content, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            content = f.read()
        assert content == report_content


class TestMain:
    def test_main_success(self, tmp_path):
        """Test main function with valid setup."""
        # Setup mock files
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        deviation_file = state_dir / "PROJ-266-exploring-the-correlation-between-molecu.yaml"
        with open(deviation_file, 'w') as f:
            yaml.dump({"deviations": []}, f)

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir()

        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "test.py").touch()

        data_dir = tmp_path / "data"
        data_dir.mkdir()

        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            result = main()

        assert result == 0
        assert (tmp_path / "data" / "transparency_report.md").exists()
        assert (tmp_path / "data" / "transparency_summary.json").exists()

    def test_main_file_not_found(self, tmp_path):
        """Test main function when deviation record is missing."""
        with patch('code.utils.generate_transparency_report.get_project_root', return_value=tmp_path):
            result = main()

        assert result == 1