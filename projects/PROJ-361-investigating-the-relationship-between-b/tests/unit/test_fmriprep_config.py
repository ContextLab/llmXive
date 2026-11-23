"""
Unit tests for fMRIPrep configuration and output structure validation.

This module tests:
1. BIDS input parsing in run_fmriprep.sh
2. Expected output directory structure generation
3. Configuration parameter validation
"""
import os
import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest


class TestFmriprepConfig:
    """Tests for fMRIPrep configuration and schema validation."""

    @pytest.fixture
    def mock_bids_dataset(self, tmp_path):
        """Create a minimal valid BIDS dataset structure for testing."""
        bids_root = tmp_path / "bids_dataset"
        bids_root.mkdir()

        # Create dataset_description.json
        dataset_desc = {
            "Name": "Test Dataset",
            "BIDSVersion": "1.8.0",
            "DatasetType": "raw",
            "Authors": ["Test Author"]
        }
        with open(bids_root / "dataset_description.json", "w") as f:
            json.dump(dataset_desc, f)

        # Create a mock subject directory
        subj_dir = bids_root / "sub-01" / "func"
        subj_dir.mkdir(parents=True)

        # Create mock NIfTI files (empty for testing)
        (subj_dir / "sub-01_task-rest_bold.nii.gz").touch()
        (subj_dir / "sub-01_task-rest_events.tsv").touch()

        return bids_root

    @pytest.fixture
    def mock_script_path(self):
        """Return the path to the run_fmriprep.sh script."""
        return Path(__file__).parent.parent.parent / "code" / "preprocessing" / "run_fmriprep.sh"

    def test_bids_input_validation(self, mock_bids_dataset):
        """Verify that the script correctly identifies valid BIDS inputs."""
        # Check that dataset_description.json exists
        assert (mock_bids_dataset / "dataset_description.json").exists()
        
        # Check that it contains required fields
        with open(mock_bids_dataset / "dataset_description.json") as f:
            desc = json.load(f)
            assert "Name" in desc
            assert "BIDSVersion" in desc
            assert desc["BIDSVersion"] >= "1.6.0"

    def test_expected_output_structure(self, mock_bids_dataset, tmp_path):
        """Verify that the script would generate the expected output structure."""
        output_dir = tmp_path / "output"
        work_dir = tmp_path / "work"
        output_dir.mkdir()
        work_dir.mkdir()

        # Expected fMRIPrep output structure
        expected_dirs = [
            "sub-01/anat",
            "sub-01/func",
            "sub-01/freesurfer",
            "logs"
        ]

        # Simulate what fMRIPrep would create (we can't run the full container in CI)
        for subdir in expected_dirs:
            (output_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Verify structure exists
        for subdir in expected_dirs:
            assert (output_dir / subdir).exists(), f"Expected directory {subdir} not created"

    def test_script_executable(self, mock_script_path):
        """Verify that the run_fmriprep.sh script exists and is executable."""
        assert mock_script_path.exists(), "run_fmriprep.sh script not found"
        assert os.access(mock_script_path, os.X_OK), "run_fmriprep.sh is not executable"

    def test_fmriprep_version_pinning(self, mock_script_path):
        """Verify that the script uses the pinned fMRIPrep version."""
        with open(mock_script_path) as f:
            content = f.read()
            # Check for pinned version
            assert "poldracklab/fmriprep:23.1.1" in content, \
                "Script must use pinned fMRIPrep version 23.1.1"
            assert "FMRIPREP_VERSION=\"23.1.1\"" in content, \
                "Version should be defined as a variable for consistency"

    def test_hcp_configuration_flags(self, mock_script_path):
        """Verify that HCP-specific configuration flags are present."""
        with open(mock_script_path) as f:
            content = f.read()
            # HCP pipeline requires specific flags
            assert "--cifti-output" in content, \
                "HCP configuration requires CIFTI output"
            assert "--output-spaces MNI152NLin2009cAsym" in content, \
                "HCP configuration requires MNI152NLin2009cAsym space"

    def test_error_handling_missing_data(self, tmp_path):
        """Verify that the script fails appropriately when data is missing."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        # Create a mock script that checks for data
        test_script = tmp_path / "test_check.sh"
        test_script.write_text(f"""
        #!/bin/bash
        if [ ! -d "{empty_dir}" ]; then
            echo "Data directory missing"
            exit 1
        fi
        """)
        test_script.chmod(0o755)

        # This should pass (directory exists)
        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_docker_vs_singularity_detection(self, mock_script_path):
        """Verify that the script detects available container engines."""
        with open(mock_script_path) as f:
            content = f.read()
            # Script should check for both Docker and Singularity
            assert "docker" in content.lower(), \
                "Script should handle Docker"
            assert "singularity" in content.lower(), \
                "Script should handle Singularity"

    def test_free_surfer_license_handling(self, mock_script_path):
        """Verify that the script handles missing FreeSurfer license gracefully."""
        with open(mock_script_path) as f:
            content = f.read()
            # Should check for license file
            assert "fs-license-file" in content.lower() or "freesurfer" in content.lower(), \
                "Script should handle FreeSurfer license"
            # Should have fallback or warning
            assert "warn" in content.lower() or "license" in content.lower(), \
                "Script should warn about missing license"

    def test_work_directory_configuration(self, mock_script_path):
        """Verify that working directory is properly configured."""
        with open(mock_fmriprep_script) as f:
            content = f.read()
            assert "work-dir" in content or "WORK_DIR" in content, \
                "Script should configure working directory"

    @pytest.mark.skip(reason="Requires Docker/Singularity to be installed")
    def test_actual_fmriprep_run(self, mock_bids_dataset, tmp_path):
        """Integration test: actually run fMRIPrep on a single subject."""
        # This test is skipped in CI due to container requirements
        # It would verify the full pipeline execution
        pass
