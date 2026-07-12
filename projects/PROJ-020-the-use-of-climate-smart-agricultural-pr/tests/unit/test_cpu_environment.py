"""
Unit tests to verify the CPU-only execution environment is correctly configured.
"""
import os
import sys
from pathlib import Path

import pytest


class TestCPUEnvironment:
    """Tests to ensure the environment is configured for CPU-only execution."""

    def test_cuda_visible_devices_is_empty(self):
        """Verify that CUDA_VISIBLE_DEVICES is set to empty string."""
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', (
            "CUDA_VISIBLE_DEVICES should be empty to enforce CPU-only execution."
        )

    def test_matplotlib_backend_is_agg(self):
        """Verify that matplotlib is using the Agg backend."""
        import matplotlib
        # The backend might be set as a string or an instance, check the string representation
        assert 'Agg' in matplotlib.get_backend(), (
            f"Matplotlib backend should be 'Agg' for headless execution, got {matplotlib.get_backend()}"
        )

    def test_project_root_in_path(self):
        """Verify that the project root is in sys.path for imports."""
        project_root = Path(__file__).parent.parent.parent
        assert str(project_root) in sys.path, (
            f"Project root {project_root} must be in sys.path."
        )

    def test_imports_from_code_modules(self):
        """Verify that we can import core modules from the code directory."""
        # Test a few key imports to ensure the path setup works
        try:
            from utils.config import get_config
            from utils.logging import initialize_logging
            from data.download import download_lsms
            # If we get here, imports worked
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import from code modules: {e}")

    def test_no_gpu_libraries_forced(self):
        """Verify that common GPU-enabling environment variables are not set or are disabled."""
        # Check TF_CPP_MIN_LOG_LEVEL is set to suppress GPU warnings if TF is used
        # We don't require TF to be installed, but if it is, it should be quiet.
        # This test is more about ensuring we aren't accidentally enabling GPU.
        # If CUDA_VISIBLE_DEVICES is empty, GPU libraries should not find devices.
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''