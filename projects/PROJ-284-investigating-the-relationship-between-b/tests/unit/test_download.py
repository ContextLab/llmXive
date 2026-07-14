"""
Contract tests for the HCP Data Fetcher.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.data.download import (
    check_ica_fix_availability,
    set_ica_fix_available,
    fetch_adhd_dataset,
    generate_synthetic_nifti_for_ci_validation,
    run_ci_validation_pipeline,
)
from code.logging_config import get_logger

logger = get_logger(__name__)


class TestICAFixAvailability:
    def test_check_ica_fix_returns_false_by_default(self, tmp_path, monkeypatch):
        """Verifies that ICA-FIX is not available by default."""
        # Ensure no marker file exists
        marker = tmp_path / ".ica_fix_available"
        assert not marker.exists()
        monkeypatch.setattr("code.data.download.ICA_FIX_AVAILABLE_FLAG", marker)
        
        result = check_ica_fix_availability()
        assert result is False

    def test_check_ica_fix_returns_true_when_marker_exists(self, tmp_path, monkeypatch):
        """Verifies that ICA-FIX is available when the marker file exists."""
        marker = tmp_path / ".ica_fix_available"
        marker.touch()
        monkeypatch.setattr("code.data.download.ICA_FIX_AVAILABLE_FLAG", marker)

        result = check_ica_fix_availability()
        assert result is True

    def test_check_ica_fix_returns_true_when_forced(self, monkeypatch):
        """Verifies that ICA-FIX is available when environment variable is set."""
        monkeypatch.setenv("HCP_ICA_FIX_FORCE_AVAILABLE", "true")
        
        result = check_ica_fix_availability()
        assert result is True


class TestSyntheticData:
    def test_generate_synthetic_nifti_creates_valid_file(self, tmp_path):
        """Verifies that the synthetic NIfTI generator creates a valid file."""
        output_path = tmp_path / "test_synthetic.nii.gz"
        result_path = generate_synthetic_nifti_for_ci_validation(output_path)
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0

        # Verify it can be loaded by nibabel
        try:
            import nibabel as nib
            img = nib.load(str(result_path))
            data = img.get_fdata()
            assert data.shape == (10, 10, 10, 10)
            assert data.size > 0
        except ImportError:
            pytest.skip("nibabel not installed")


class TestCIFallback:
    @patch("code.data.download.os.system")
    def test_run_ci_validation_pipeline_with_mock_tools(self, mock_system, tmp_path, monkeypatch):
        """
        Verifies that the CI validation pipeline runs successfully with mocked tools.
        This simulates the environment where FSL/AFNI are missing.
        """
        # Mock os.system to return 1 (tool not found) for all checks
        mock_system.return_value = 1
        
        # Setup paths
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        marker = tmp_path / "data" / "analysis" / ".ci_validation_complete"
        monkeypatch.setattr("code.data.download.CI_VALIDATION_MARKER", marker)
        
        subjects = ["sub-001", "sub-002"]
        
        # Run the validation
        result = run_ci_validation_pipeline(subjects)
        
        # Verify the marker was created
        assert marker.exists()
        assert result is True
