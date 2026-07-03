"""
Unit tests for generate_synthetic_test_data.py
"""
import os
import sys
import subprocess
import tempfile
import shutil
import yaml

import pytest
import pandas as pd

# Add code to path
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from utils.provenance import hash_file


class TestSyntheticDataGeneration:

    def test_no_flag_exits_error(self):
        """Test that running without --test-mode exits with error."""
        result = subprocess.run(
            [sys.executable, "code/generate_synthetic_test_data.py"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        assert result.returncode != 0
        assert "test-mode" in result.stdout or "test-mode" in result.stderr

    def test_with_flag_generates_files(self, tmp_path):
        """Test that running with --test-mode generates expected files."""
        output_dir = tmp_path / "raw"
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Run script
        result = subprocess.run(
            [
                sys.executable, "code/generate_synthetic_test_data.py",
                "--test-mode",
                "--output-dir", str(output_dir),
                "--num-subjects", "1",
                "--num-trials", "2",
                "--seed", "123"
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check output dir
        files = list(output_dir.glob("*.csv"))
        assert len(files) == 1
        assert files[0].name.startswith("synthetic_subject_")

        # Check manifest
        # Note: The script writes to 'state/test_artifacts.yaml' relative to cwd.
        # We need to ensure we check the right place or mock the path.
        # For this test, we assume the script writes to the provided cwd's state/.
        # Since we ran from project root, it wrote to project_root/state/.
        # To make this test isolated, we might need to modify the script to accept --state-dir
        # or check the actual project root state if running in CI.
        # For now, we verify the CSV content.

        df = pd.read_csv(files[0])
        required_cols = [
            'subject_id', 'trial_id', 'timestamp', 'pupil_diameter',
            'x', 'y', 'search_time', 'target_salience', 'fixation_count'
        ]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

        # Check data types
        assert df['subject_id'].iloc[0] == 101  # First subject ID
        assert df['trial_id'].nunique() == 2    # 2 trials
        assert len(df) > 0

    def test_deterministic_output(self, tmp_path):
        """Test that same seed produces same output."""
        output_dir_1 = tmp_path / "run1"
        output_dir_2 = tmp_path / "run2"
        output_dir_1.mkdir()
        output_dir_2.mkdir()

        # Run 1
        subprocess.run(
            [
                sys.executable, "code/generate_synthetic_test_data.py",
                "--test-mode", "--output-dir", str(output_dir_1),
                "--num-subjects", "1", "--seed", "999"
            ],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        # Run 2
        subprocess.run(
            [
                sys.executable, "code/generate_synthetic_test_data.py",
                "--test-mode", "--output-dir", str(output_dir_2),
                "--num-subjects", "1", "--seed", "999"
            ],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        file1 = list(output_dir_1.glob("*.csv"))[0]
        file2 = list(output_dir_2.glob("*.csv"))[0]

        hash1 = hash_file(str(file1))
        hash2 = hash_file(str(file2))

        assert hash1 == hash2, "Deterministic generation failed: hashes differ"