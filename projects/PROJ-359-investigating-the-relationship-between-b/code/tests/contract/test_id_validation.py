"""
Contract test for ID validation.

Verifies that missing IDs in behavioral data or directory structure
cause the validator to exit with code 1.
"""
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from unittest import TestCase, mock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.validators import run_validators, validate_id_matching, validate_behavioral_columns


class TestIDValidation(TestCase):
    """Test ID matching validation logic."""

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

    def test_valid_id_matching(self):
        """Test that matching IDs pass validation."""
        # Create behavioral file with matching IDs
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "nback_dprime": [1.5, 2.0, 1.8]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 0, "Valid ID matching should return exit code 0")

    def test_missing_id_in_behavioral(self):
        """Test that missing ID in behavioral data fails validation."""
        # Create behavioral file with missing ID (sub-03 is missing)
        df = pd.DataFrame({
            "participant_id": ["01", "02"],
            "nback_dprime": [1.5, 2.0]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 1, "Missing ID in behavioral data should return exit code 1")

    def test_extra_id_in_behavioral(self):
        """Test that extra ID in behavioral data fails validation."""
        # Create behavioral file with extra ID (sub-04 doesn't exist in dirs)
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03", "04"],
            "nback_dprime": [1.5, 2.0, 1.8, 2.1]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 1, "Extra ID in behavioral data should return exit code 1")

    def test_missing_behavioral_column(self):
        """Test that missing behavioral column fails validation."""
        # Create behavioral file with matching IDs but missing required column
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "other_column": [1.5, 2.0, 1.8]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 1, "Missing behavioral column should return exit code 1")

    def test_wm_accuracy_column_accepted(self):
        """Test that wm_accuracy column is accepted as alternative to nback_dprime."""
        # Create behavioral file with wm_accuracy instead of nback_dprime
        df = pd.DataFrame({
            "participant_id": ["01", "02", "03"],
            "wm_accuracy": [0.85, 0.90, 0.88]
        })
        df.to_csv(self.behavioral_path, sep='\t', index=False)
        
        exit_code = run_validators(str(self.data_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 0, "wm_accuracy column should be accepted")

    def test_nonexistent_data_directory(self):
        """Test that nonexistent data directory fails validation."""
        nonexistent_dir = Path(self.temp_dir) / "nonexistent"
        
        exit_code = run_validators(str(nonexistent_dir), str(self.behavioral_path), str(self.log_path))
        
        self.assertEqual(exit_code, 1, "Nonexistent data directory should return exit code 1")

    def test_nonexistent_behavioral_file(self):
        """Test that nonexistent behavioral file fails validation."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.tsv"
        
        exit_code = run_validators(str(self.data_dir), str(nonexistent_file), str(self.log_path))
        
        self.assertEqual(exit_code, 1, "Nonexistent behavioral file should return exit code 1")
