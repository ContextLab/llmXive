"""
Tests for Project Structure Creation (Task T001a).

Verifies that the required directory hierarchy exists and is accessible.
"""
import os
import pytest
from pathlib import Path


PROJECT_ROOT = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "artifacts",
    "artifacts/checkpoints",
    "artifacts/results",
]

# Additional directories expected based on project API surface
ADDITIONAL_DIRS = [
    "code/models",
    "code/training",
    "code/evaluation",
    "code/analysis",
    "code/utils",
    "code/validation",
]


class TestProjectStructure:
    """Test cases for verifying project directory structure."""

    def test_project_root_exists(self):
        """Verify the main project root directory exists."""
        assert PROJECT_ROOT.exists(), f"Project root {PROJECT_ROOT} does not exist"
        assert PROJECT_ROOT.is_dir(), f"{PROJECT_ROOT} is not a directory"

    @pytest.mark.parametrize("subdir", REQUIRED_DIRS)
    def test_required_subdirectories_exist(self, subdir):
        """Verify all required subdirectories exist."""
        full_path = PROJECT_ROOT / subdir
        assert full_path.exists(), f"Required directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"

    @pytest.mark.parametrize("subdir", ADDITIONAL_DIRS)
    def test_additional_subdirectories_exist(self, subdir):
        """Verify additional subdirectories exist for code organization."""
        full_path = PROJECT_ROOT / subdir
        assert full_path.exists(), f"Additional directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_data_raw_is_writable(self):
        """Verify data/raw directory is writable."""
        data_raw = PROJECT_ROOT / "data/raw"
        if data_raw.exists():
            test_file = data_raw / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (IOError, OSError) as e:
                pytest.fail(f"data/raw is not writable: {e}")

    def test_artifacts_checkpoints_is_writable(self):
        """Verify artifacts/checkpoints directory is writable."""
        checkpoints = PROJECT_ROOT / "artifacts/checkpoints"
        if checkpoints.exists():
            test_file = checkpoints / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (IOError, OSError) as e:
                pytest.fail(f"artifacts/checkpoints is not writable: {e}")

    def test_directory_hierarchy_integrity(self):
        """Verify the full directory hierarchy is correctly nested."""
        # Check that data/raw is inside data
        data_dir = PROJECT_ROOT / "data"
        raw_dir = PROJECT_ROOT / "data/raw"
        processed_dir = PROJECT_ROOT / "data/processed"
        
        assert data_dir.exists(), "data directory missing"
        assert raw_dir.exists(), "data/raw missing"
        assert processed_dir.exists(), "data/processed missing"
        assert raw_dir.is_relative_to(data_dir), "data/raw not inside data"
        assert processed_dir.is_relative_to(data_dir), "data/processed not inside data"

        # Check artifacts hierarchy
        artifacts_dir = PROJECT_ROOT / "artifacts"
        checkpoints_dir = PROJECT_ROOT / "artifacts/checkpoints"
        results_dir = PROJECT_ROOT / "artifacts/results"
        
        assert artifacts_dir.exists(), "artifacts directory missing"
        assert checkpoints_dir.exists(), "artifacts/checkpoints missing"
        assert results_dir.exists(), "artifacts/results missing"
        assert checkpoints_dir.is_relative_to(artifacts_dir), "checkpoints not inside artifacts"
        assert results_dir.is_relative_to(artifacts_dir), "results not inside artifacts"