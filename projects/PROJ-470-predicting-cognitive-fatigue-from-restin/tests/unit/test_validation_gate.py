"""Unit tests for the Data Validation Gate (T010).

These tests verify:
1. The script exits with code 1 and prints the correct error if variables are missing.
2. The script exits with code 1 and prints the correct error if N < 30.
3. The script writes data/processed/validation_report.json on success.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

from check_sample_size import check_sample_size, REQUIRED_VARIABLES, MIN_SAMPLE_SIZE, MANIFEST_PATH, OUTPUT_REPORT_PATH
from utils.logging import get_logger


class TestValidationGate(unittest.TestCase):
    def setUp(self):
        """Set up temporary directories and mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = os.path.join(self.temp_dir, "data", "raw")
        self.data_processed_dir = os.path.join(self.temp_dir, "data", "processed")
        os.makedirs(self.data_raw_dir, exist_ok=True)
        os.makedirs(self.data_processed_dir, exist_ok=True)
        
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Mock logger
        self.logger = get_logger("test_validation")

    def tearDown(self):
        """Clean up temporary directories."""
        os.chdir(self.original_cwd)
        # Remove temp dir
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_variables(self):
        """Test that the script exits with code 1 if required variables are missing."""
        # Create a manifest with missing variables
        manifest_data = {
            "participants": [
                {"file": "sub-01.fif", "variables": ["eeg_data", "missing_var"]},
                {"file": "sub-02.fif", "variables": ["eeg_data", "missing_var"]}
            ]
        }
        manifest_path = Path(MANIFEST_PATH)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)

        # We expect SystemExit with code 1
        with self.assertRaises(SystemExit) as context:
            check_sample_size(self.logger)

        self.assertEqual(context.exception.code, 1)

    def test_insufficient_sample_size(self):
        """Test that the script exits with code 1 if N < 30."""
        # Create a manifest with N < 30 but correct variables
        participants = [{"file": f"sub-{i:02d}.fif", "variables": REQUIRED_VARIABLES} for i in range(20)]
        manifest_data = {"participants": participants}
        
        manifest_path = Path(MANIFEST_PATH)
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)

        with self.assertRaises(SystemExit) as context:
            check_sample_size(self.logger)

        self.assertEqual(context.exception.code, 1)

    def test_validation_success(self):
        """Test that the script writes the validation report on success."""
        # Create a manifest with N >= 30 and correct variables
        participants = [{"file": f"sub-{i:02d}.fif", "variables": REQUIRED_VARIABLES} for i in range(30)]
        manifest_data = {"participants": participants}
        
        manifest_path = Path(MANIFEST_PATH)
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)

        # Run the check
        summary = check_sample_size(self.logger)
        
        # Verify the summary content
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["participant_count"], 30)
        self.assertIn("timestamp", summary)

        # Verify the file was written
        report_path = Path(OUTPUT_REPORT_PATH)
        self.assertTrue(report_path.exists(), f"Validation report not found at {report_path}")
        
        with open(report_path, "r") as f:
            written_summary = json.load(f)
        
        self.assertEqual(written_summary["status"], "passed")
        self.assertEqual(written_summary["participant_count"], 30)

    def test_manifest_not_found(self):
        """Test that the script exits with code 1 if manifest is missing."""
        # Ensure manifest does not exist
        if Path(MANIFEST_PATH).exists():
            Path(MANIFEST_PATH).unlink()

        with self.assertRaises(SystemExit) as context:
            check_sample_size(self.logger)

        self.assertEqual(context.exception.code, 1)


if __name__ == "__main__":
    unittest.main()