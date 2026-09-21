"""
Unit tests for VDOS Retention Report generation (T024c).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from vdos_retention_report import (
    load_filtered_config_ids,
    load_vdos_missing_status,
    generate_retention_report,
    save_retention_report,
    main
)
from config.env_config import get_processed_dir


class TestLoadFilteredConfigIds:
    def test_load_valid_filtered_ids(self, tmp_path):
        """Test loading valid filtered config IDs."""
        # Setup mock file
        filtered_file = tmp_path / "filtered_config_ids.json"
        test_data = {"config_ids": ["config_001", "config_002", "config_003"]}
        with open(filtered_file, "w") as f:
            json.dump(test_data, f)

        # Patch get_processed_dir to return tmp_path
        with patch("vdos_retention_report.get_processed_dir", return_value=tmp_path):
            result = load_filtered_config_ids(tmp_path)

        assert result == ["config_001", "config_002", "config_003"]

    def test_missing_filtered_ids_file(self, tmp_path):
        """Test error when filtered config IDs file is missing."""
        with patch("vdos_retention_report.get_processed_dir", return_value=tmp_path):
            with pytest.raises(FileNotFoundError):
                load_filtered_config_ids(tmp_path)


class TestLoadVdosMissingStatus:
    def test_load_from_status_file(self, tmp_path):
        """Test loading VDOS status from status file."""
        status_file = tmp_path / "vdos_missing_status.json"
        test_data = {
            "config_001": "VDOS-MISSING",
            "config_002": "VDOS-PRESENT"
        }
        with open(status_file, "w") as f:
            json.dump(test_data, f)

        result = load_vdos_missing_status(tmp_path)

        assert result["config_001"] == "VDOS-MISSING"
        assert result["config_002"] == "VDOS-PRESENT"

    def test_load_from_missing_report_file(self, tmp_path):
        """Test loading VDOS status from missing report file."""
        missing_file = tmp_path / "vdos_missing_report.json"
        test_data = {
            "missing_configs": [
                {"id": "config_001", "status": "VDOS-MISSING"},
                {"id": "config_003", "status": "VDOS-MISSING"}
            ]
        }
        with open(missing_file, "w") as f:
            json.dump(test_data, f)

        result = load_vdos_missing_status(tmp_path)

        assert result["config_001"] == "VDOS-MISSING"
        assert result["config_003"] == "VDOS-MISSING"
        assert "config_002" not in result


class TestGenerateRetentionReport:
    def test_generate_with_missing_vdos(self):
        """Test report generation with VDOS-missing configs."""
        config_ids = ["config_001", "config_002", "config_003"]
        vdos_status = {
            "config_001": "VDOS-MISSING",
            "config_002": "VDOS-PRESENT",
            "config_003": "VDOS-MISSING"
        }

        report = generate_retention_report(config_ids, vdos_status)

        assert len(report["retained_configs"]) == 2
        ids = [item["id"] for item in report["retained_configs"]]
        assert "config_001" in ids
        assert "config_003" in ids

        # Verify structure
        for item in report["retained_configs"]:
            assert item["status"] == "VDOS-MISSING"
            assert "reason" in item

    def test_generate_with_no_missing_vdos(self):
        """Test report generation when all configs have VDOS."""
        config_ids = ["config_001", "config_002"]
        vdos_status = {
            "config_001": "VDOS-PRESENT",
            "config_002": "VDOS-PRESENT"
        }

        report = generate_retention_report(config_ids, vdos_status)

        assert len(report["retained_configs"]) == 0


class TestSaveRetentionReport:
    def test_save_report(self, tmp_path):
        """Test saving the retention report."""
        report = {
            "retained_configs": [
                {"id": "config_001", "status": "VDOS-MISSING", "reason": "Test reason"}
            ]
        }
        output_path = tmp_path / "vdos_retention_report.json"

        save_retention_report(report, output_path)

        assert output_path.exists()
        with open(output_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data == report


class TestMainIntegration:
    @patch("vdos_retention_report.load_filtered_config_ids")
    @patch("vdos_retention_report.load_vdos_missing_status")
    @patch("vdos_retention_report.save_retention_report")
    @patch("vdos_retention_report.get_processed_dir")
    def test_main_execution(
        self,
        mock_get_dir,
        mock_save,
        mock_load_status,
        mock_load_ids
    ):
        """Test the main function execution flow."""
        mock_get_dir.return_value = Path("/fake/processed")
        mock_load_ids.return_value = ["config_001", "config_002"]
        mock_load_status.return_value = {
            "config_001": "VDOS-MISSING",
            "config_002": "VDOS-PRESENT"
        }

        main()

        mock_load_ids.assert_called_once()
        mock_load_status.assert_called_once()
        mock_save.assert_called_once()