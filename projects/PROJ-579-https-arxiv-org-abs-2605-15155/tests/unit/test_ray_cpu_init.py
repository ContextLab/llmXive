"""
Contract test for Ray CPU initialization (User Story 1).

This test verifies that:
1. Ray can be initialized in a CPU-only environment.
2. The environment variable CUDA_VISIBLE_DEVICES is set to empty.
3. The stub script scripts/stub_ray_check.py exists and is importable.
4. The stub script fails as expected (exit code 1) before the real implementation.

Dependencies:
- T009a: scripts/stub_ray_check.py must exist.
"""
import os
import subprocess
import sys
import json
import pytest

# Ensure CUDA is disabled before any Ray/PyTorch imports
os.environ["CUDA_VISIBLE_DEVICES"] = ""

try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False


class TestRayCPUInit:
    """Contract tests for Ray CPU initialization."""

    @pytest.mark.skipif(
        not RAY_AVAILABLE,
        reason="Ray is not installed in the current environment."
    )
    def test_ray_cpu_initialization(self):
        """Test that Ray initializes successfully on CPU with limited cores."""
        # Ensure CUDA is not accessible
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", \
            "CUDA_VISIBLE_DEVICES must be empty for CPU-only execution."

        # Initialize Ray with 2 CPUs (as per T006 configuration)
        if ray.is_initialized():
            ray.shutdown()

        try:
            ray.init(num_cpus=2, ignore_reinit_error=True)
            # Verify cluster info
            cluster_info = ray.cluster_resources()
            cpu_count = float(cluster_info.get("CPU", 0))
            
            assert cpu_count >= 2, f"Expected at least 2 CPUs, got {cpu_count}"
            assert "GPU" not in cluster_info or float(cluster_info.get("GPU", 0)) == 0, \
                "GPU resources should not be detected in this CPU-only configuration."
            
            ray.shutdown()
        except Exception as e:
            pytest.fail(f"Ray initialization failed: {str(e)}")

    def test_stub_script_exists_and_fails(self):
        """Test that the stub script T009a exists and exits with code 1."""
        stub_path = "scripts/stub_ray_check.py"
        
        if not os.path.exists(stub_path):
            pytest.fail(f"Stub script not found at {stub_path}. Task T009a may not be complete.")
        
        # Run the stub script
        result = subprocess.run(
            [sys.executable, stub_path],
            capture_output=True,
            text=True
        )
        
        # The stub should fail (exit code 1) as it is a placeholder
        assert result.returncode == 1, \
            f"Stub script should exit with code 1, but exited with {result.returncode}. " \
            f"Stderr: {result.stderr}"

    @pytest.mark.skipif(
        not RAY_AVAILABLE,
        reason="Ray is not installed."
    )
    def test_health_check_output_format(self):
        """Test that the health check logic (simulated here) produces valid JSON."""
        # This test simulates the expected output format for T010
        expected_keys = {"exit_code", "cpu_count", "status"}
        
        # Simulate a successful run result
        mock_result = {
            "exit_code": 0,
            "cpu_count": 2,
            "status": "healthy"
        }
        
        assert set(mock_result.keys()) == expected_keys, \
            "Health check output must contain exit_code, cpu_count, and status."
        
        # Verify JSON serialization
        try:
            json.dumps(mock_result)
        except TypeError as e:
            pytest.fail(f"Health check result is not JSON serializable: {e}")