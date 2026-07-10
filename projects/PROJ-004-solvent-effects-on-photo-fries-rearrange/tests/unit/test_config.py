"""
Unit tests for code/config.py

Verifies:
1. CPU-only constraints are enforced (CUDA_VISIBLE_DEVICES is empty).
2. Data directory paths are correctly resolved relative to project root.
3. All required data directories exist after import.
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure code/ is in path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import (
    PROJECT_ROOT,
    DATA_RAW,
    DATA_COMPUTE,
    DATA_PROCESSED,
    DATA_CHEMICALS,
    SOLVENTS_YAML_PATH,
    ALLOW_GPU,
    get_project_root,
    get_data_path,
    enforce_cpu_only
)


class TestCPUConstraints:
    """Tests for CPU-only execution constraints."""

    def test_cpu_env_var_set_on_import(self):
        """Verify CUDA_VISIBLE_DEVICES is set to empty string."""
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", \
            "CUDA_VISIBLE_DEVICES must be empty to enforce CPU-only mode."

    def test_allow_gpu_flag_is_false(self):
        """Verify ALLOW_GPU constant is False."""
        assert ALLOW_GPU is False, "ALLOW_GPU must be False for CI compliance."

    def test_enforce_cpu_function(self):
        """Verify enforce_cpu_only does not raise when GPU is disabled."""
        # This should not raise an exception in a CPU-only environment
        try:
            enforce_cpu_only()
        except RuntimeError as e:
            pytest.fail(f"enforce_cpu_only raised unexpectedly: {e}")


class TestPathResolution:
    """Tests for file path definitions."""

    def test_project_root_is_path_object(self):
        """Verify PROJECT_ROOT is a valid Path object."""
        assert isinstance(PROJECT_ROOT, Path), "PROJECT_ROOT must be a Path object."
        assert PROJECT_ROOT.exists(), "PROJECT_ROOT must exist on disk."

    def test_data_dirs_exist(self):
        """Verify all data directories exist after import."""
        assert DATA_RAW.exists(), f"{DATA_RAW} must exist."
        assert DATA_COMPUTE.exists(), f"{DATA_COMPUTE} must exist."
        assert DATA_PROCESSED.exists(), f"{DATA_PROCESSED} must exist."
        assert DATA_CHEMICALS.exists(), f"{DATA_CHEMICALS} must exist."

    def test_data_dirs_are_subdirs_of_root(self):
        """Verify data directories are subdirectories of PROJECT_ROOT."""
        assert str(DATA_RAW).startswith(str(PROJECT_ROOT))
        assert str(DATA_COMPUTE).startswith(str(PROJECT_ROOT))
        assert str(DATA_PROCESSED).startswith(str(PROJECT_ROOT))
        assert str(DATA_CHEMICALS).startswith(str(PROJECT_ROOT))

    def test_solvents_yaml_path(self):
        """Verify SOLVENTS_YAML_PATH points to correct location."""
        expected = DATA_CHEMICALS / "solvents.yaml"
        assert SOLVENTS_YAML_PATH == expected, \
            f"SOLVENTS_YAML_PATH should be {expected}"

    def test_get_project_root(self):
        """Test get_project_root() function."""
        assert get_project_root() == PROJECT_ROOT

    def test_get_data_path(self):
        """Test get_data_path() helper."""
        path = get_data_path("raw/test.csv")
        assert path == DATA_ROOT / "raw/test.csv"
        assert path.is_absolute()

    def test_data_root_global(self):
        """Verify DATA_ROOT global is accessible."""
        from config import DATA_ROOT
        assert isinstance(DATA_ROOT, Path)
        assert DATA_ROOT.exists()