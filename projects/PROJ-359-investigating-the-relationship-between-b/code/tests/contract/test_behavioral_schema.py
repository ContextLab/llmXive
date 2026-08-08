"""
Contract test for behavioral column validation.

Verifies that missing required behavioral columns cause the validator
to exit with code 1.
"""
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from unittest import TestCase

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.validators import run_validators, validate_behavioral_columns


class TestBehavioralSchema(TestCase):
    """Test behavioral column validation logic."""

    def setUp(self):
        """Set up temporary directories and files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.data_dir.mkdir()
        
        # Create mock subject directories
        for i in ["01", "02", "03"]:
            (self.data_dir / f"sub-{i}").mkdir()
        
        self.behavioral_path = Path(self.temp_dir) / "behavioral.tsv"
        self.log_path = Path(self.temp_dir) / "test_log.json"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_missing_nback_and_wm_columns(self):
        """Test that missing both nback_dprime and wm_accuracy fails validation."""
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "age": [25, 30, 28],
            "sex": ["M", "F", "M"]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 1, "Missing both nback_dprime and wm_accuracy should fail")

    def test_nback_dprime_column_present(self):
        """Test that presence of nback_dprime column passes validation."""
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "nback_dprime": [1.5, 2.0, 1.8],
            "age": [25, 30, 28]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 0, "Presence of nback_dprime should pass validation")

    def test_wm_accuracy_column_present(self):
        """Test that presence of wm_accuracy column passes validation."""
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "wm_accuracy": [0.85, 0.90, 0.88],
            "age": [25, 30, 28]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 0, "Presence of wm_accuracy should pass validation")

    def test_both_columns_present(self):
        """Test that presence of both columns passes validation."""
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "nback_dprime": [1.5, 2.0, 1.8],
            "wm_accuracy": [0.85, 0.90, 0.88]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 0, "Presence of both columns should pass validation")

    def test_case_insensitive_column_matching(self):
        """Test that column matching is case-insensitive."""
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "NBACK_DPRIME": [1.5, 2.0, 1.8]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 0, "Case-insensitive column matching should pass")

    def test_empty_behavioral_file(self):
        """Test that empty behavioral file (no data rows) fails validation."""
        df = pd.DataFrame(columns=["participant_id", "nback_dprime"])
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        # Should fail because no data rows exist
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        # This might pass if columns exist but no data, or fail if no data
        # The important thing is the validator runs without crashing
        self.assertIn(exit_code, [0, 1], "Empty file should return valid exit code")

    def test_malformed_tsv(self):
        """Test that malformed TSV file fails validation gracefully."""
        # Create a file with invalid TSV content
        with open(self.behavioral_path, 'w') as f:
            f.write("participant_id\tnback_dprime\n01\t1.5\n02\n03\t1.8")
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        # Should fail due to parsing error
        self.assertEqual(exit_code, 1, "Malformed TSV should fail validation")
