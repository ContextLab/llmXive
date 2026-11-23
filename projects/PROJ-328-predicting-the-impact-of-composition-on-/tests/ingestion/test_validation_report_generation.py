"""
Test Task T016c: Verify Validation Report Generation.

This test verifies that `code/ingestion/generate_validation_report.py`
executes without errors and produces valid YAML when provided with a
mock `data/processed/.ingestion_status.json`.

It creates a temporary mock status file, runs the generation script,
and validates the output structure and content.
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.generate_validation_report import (
    load_ingestion_status,
    generate_validation_report,
    save_report,
    main,
    STATUS_FILE,
    REPORT_FILE
)
from utils.error_handlers import ConfigurationError


class TestValidationReportGeneration:
    """Tests for the validation report generation logic."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup: Create a temporary directory structure and mock status file.
        Teardown: Clean up temporary files.
        """
        # Create a temporary directory to act as the project root for this test
        self.temp_dir = tempfile.mkdtemp(prefix="test_t016c_")
        self.temp_processed_dir = Path(self.temp_dir) / "data" / "processed"
        self.temp_processed_dir.mkdir(parents=True, exist_ok=True)

        # Temporarily override the module-level paths
        self.original_status_file = STATUS_FILE
        self.original_report_file = REPORT_FILE

        # We need to reload the module or patch the constants.
        # Since the constants are defined at module load time, we patch them here.
        import ingestion.generate_validation_report as gen_report_module
        gen_report_module.STATUS_FILE = self.temp_processed_dir / ".ingestion_status.json"
        gen_report_module.REPORT_FILE = self.temp_processed_dir / "validation_report.yaml"
        
        # Also update the PROCESSED_DIR constant used inside functions
        gen_report_module.PROCESSED_DIR = self.temp_processed_dir

        self.mock_status_file = gen_report_module.STATUS_FILE
        self.mock_report_file = gen_report_module.REPORT_FILE

        yield

        # Teardown: Restore original paths and remove temp directory
        import ingestion.generate_validation_report as gen_report_module
        gen_report_module.STATUS_FILE = self.original_status_file
        gen_report_module.REPORT_FILE = self.original_report_file
        gen_report_module.PROCESSED_DIR = self.original_status_file.parent # Approximate restore

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_ingestion_status_with_valid_file(self):
        """Test loading a valid mock status file."""
        mock_data = {
            "threshold_status": "N>=100",
            "exact_N": 150,
            "power_limitation_warning": ""
        }
        self.mock_status_file.write_text(json.dumps(mock_data))

        status = load_ingestion_status()
        assert status == mock_data
        assert status["exact_N"] == 150

    def test_load_ingestion_status_missing_file(self):
        """Test that missing status file raises ConfigurationError."""
        if self.mock_status_file.exists():
            self.mock_status_file.unlink()

        with pytest.raises(ConfigurationError) as exc_info:
            load_ingestion_status()
        
        assert "not found" in str(exc_info.value).lower()

    def test_generate_validation_report_structure(self):
        """Test that the generated report has the correct schema."""
        mock_status = {
            "threshold_status": "50<=N<100",
            "exact_N": 75,
            "power_limitation_warning": "N < 100"
        }

        report = generate_validation_report(mock_status)

        # Verify top-level keys
        assert "report_metadata" in report
        assert "status" in report
        assert "count" in report
        assert "power_limitation_warning" in report
        assert "associational_warning" in report

        # Verify values map correctly
        assert report["status"] == "50<=N<100"
        assert report["count"] == 75
        assert report["power_limitation_warning"] == "N < 100"
        
        # Verify metadata presence
        assert "generated_at" in report["report_metadata"]
        assert "task_id" in report["report_metadata"]
        assert report["report_metadata"]["task_id"] == "T016b"

    def test_full_execution_flow(self):
        """
        Test the full execution flow:
        1. Create mock status file.
        2. Run main() (which calls load, generate, save).
        3. Verify output file exists and is valid YAML.
        """
        # 1. Create mock status
        mock_status = {
            "threshold_status": "N>=100",
            "exact_N": 120,
            "power_limitation_warning": ""
        }
        self.mock_status_file.write_text(json.dumps(mock_status))

        # 2. Run main
        exit_code = main()
        assert exit_code == 0, f"main() returned non-zero exit code: {exit_code}"

        # 3. Verify output
        assert self.mock_report_file.exists(), "Report file was not created."
        
        try:
            with open(self.mock_report_file, 'r', encoding='utf-8') as f:
                loaded_report = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Generated file is not valid YAML: {e}")

        assert loaded_report["status"] == "N>=100"
        assert loaded_report["count"] == 120
        assert "associational_warning" in loaded_report
        assert "NOTE" in loaded_report["associational_warning"]

    def test_main_with_missing_status_file(self):
        """Test that main() returns error code when status file is missing."""
        if self.mock_status_file.exists():
            self.mock_status_file.unlink()

        exit_code = main()
        assert exit_code == 1
        assert not self.mock_report_file.exists()