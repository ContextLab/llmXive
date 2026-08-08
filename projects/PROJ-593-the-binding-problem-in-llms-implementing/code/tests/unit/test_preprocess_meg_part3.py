"""
Unit tests for T008: Validate and store pre-processed MEG data.

These tests verify that:
1. The validation function correctly identifies valid data
2. The validation function correctly identifies invalid data
3. The main function creates the expected output files
"""
import os
import tempfile
import json
from pathlib import Path
import numpy as np
import pytest
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocess_meg import validate_psd_data, main


class TestValidatePSDData:
    """Tests for the validate_psd_data function."""

    def test_valid_normalized_psd(self):
        """Test validation of properly normalized PSD data."""
        # Create valid normalized PSD data (sums to 1)
        psd_data = np.array([[0.1, 0.2, 0.3, 0.4]])  # Sum = 1.0
        expected_shape = (1, 4)

        result = validate_psd_data(psd_data, expected_shape, min_value=0.0, max_value=1.0)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["shape"] == [1, 4]
        assert np.isclose(result["sum_normalized"], 1.0)

    def test_shape_mismatch(self):
        """Test validation detects shape mismatch."""
        psd_data = np.array([[0.1, 0.2, 0.3, 0.4]])
        expected_shape = (2, 4)  # Different shape

        result = validate_psd_data(psd_data, expected_shape, min_value=0.0, max_value=1.0)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Shape mismatch" in result["errors"][0]

    def test_nan_values(self):
        """Test validation detects NaN values."""
        psd_data = np.array([[0.1, np.nan, 0.3, 0.4]])
        expected_shape = (1, 4)

        result = validate_psd_data(psd_data, expected_shape, min_value=0.0, max_value=1.0)

        assert result["valid"] is False
        assert "NaN" in str(result["errors"])

    def test_inf_values(self):
        """Test validation detects Inf values."""
        psd_data = np.array([[0.1, np.inf, 0.3, 0.4]])
        expected_shape = (1, 4)

        result = validate_psd_data(psd_data, expected_shape, min_value=0.0, max_value=1.0)

        assert result["valid"] is False
        assert "Inf" in str(result["errors"])

    def test_values_out_of_range(self):
        """Test validation warns about values outside expected range."""
        psd_data = np.array([[0.1, -0.1, 0.3, 0.4]])  # Negative value
        expected_shape = (1, 4)

        result = validate_psd_data(psd_data, expected_shape, min_value=0.0, max_value=1.0)

        # Should still be valid but with warnings
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_not_normalized(self):
        """Test validation warns about data that is not normalized."""
        psd_data = np.array([[0.1, 0.2, 0.3, 0.4]])  # Sum = 1.0, but we'll test with non-normalized
        psd_data_unnorm = np.array([[0.1, 0.2, 0.3, 0.4]]) * 10  # Sum = 10.0
        expected_shape = (1, 4)

        result = validate_psd_data(psd_data_unnorm, expected_shape, min_value=0.0, max_value=10.0)

        # Should warn about not being normalized (sum not close to 1)
        assert len(result["warnings"]) > 0


class TestPreprocessMegScriptExecution:
    """Tests for the main script execution."""

    def test_main_creates_output_files(self):
        """Test that main() creates the expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a mock data directory structure
            processed_dir = tmpdir_path / "data" / "processed"
            processed_dir.mkdir(parents=True)

            # Create a mock input file (bandpass filtered data)
            input_path = processed_dir / "meg_filtered.npy"
            mock_data = np.random.randn(10, 512)  # 10 samples, 512 timepoints
            np.save(input_path, mock_data)

            # Create a mock config file
            config_dir = tmpdir_path / "config"
            config_dir.mkdir()
            config_path = config_dir / "default.yaml"
            config_content = """
            preprocessing:
              low_freq: 30.0
              high_freq: 50.0
              seq_len: 512
              fps: 1000
            """
            with open(config_path, 'w') as f:
                f.write(config_content)

            # Temporarily change the working directory
            original_cwd = os.getcwd()
            original_sys_path = sys.path.copy()

            try:
                os.chdir(tmpdir)
                if str(tmpdir_path) not in sys.path:
                    sys.path.insert(0, str(tmpdir_path))

                # Import the main function from the correct location
                from src.data.preprocess_meg import main as preprocess_main

                # Run the main function
                preprocess_main()

                # Check that output files were created
                output_path = processed_dir / "meg_psd_normalized.npy"
                validation_path = processed_dir / "meg_validation_report.json"

                assert output_path.exists(), "Output PSD file was not created"
                assert validation_path.exists(), "Validation report was not created"

                # Verify the output file contains valid data
                saved_data = np.load(output_path)
                assert saved_data.shape[0] == 10, "Number of samples mismatch"
                assert saved_data.shape[1] > 0, "PSD frequency bins should exist"

                # Verify the validation report is valid JSON
                with open(validation_path, 'r') as f:
                    validation_report = json.load(f)

                assert "valid" in validation_report
                assert "errors" in validation_report
                assert "warnings" in validation_report

            finally:
                os.chdir(original_cwd)
                sys.path = original_sys_path

    def test_main_fails_without_input(self):
        """Test that main() fails gracefully when input file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a mock data directory structure but NO input file
            processed_dir = tmpdir_path / "data" / "processed"
            processed_dir.mkdir(parents=True)

            # Create a mock config file
            config_dir = tmpdir_path / "config"
            config_dir.mkdir()
            config_path = config_dir / "default.yaml"
            config_content = """
            preprocessing:
              low_freq: 30.0
              high_freq: 50.0
              seq_len: 512
              fps: 1000
            """
            with open(config_path, 'w') as f:
                f.write(config_content)

            original_cwd = os.getcwd()
            original_sys_path = sys.path.copy()

            try:
                os.chdir(tmpdir)
                if str(tmpdir_path) not in sys.path:
                    sys.path.insert(0, str(tmpdir_path))

                from src.data.preprocess_meg import main as preprocess_main

                # This should exit with code 1
                with pytest.raises(SystemExit) as exc_info:
                    preprocess_main()

                assert exc_info.value.code == 1

            finally:
                os.chdir(original_cwd)
                sys.path = original_sys_path