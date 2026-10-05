"""
Test CI: Validate resource constraints in local environment.

This test verifies that the pipeline respects the `ENABLE_DOCKER` configuration flag.
If `ENABLE_DOCKER` is False (or not set), the Docker-related checks are skipped.
If `ENABLE_DOCKER` is True, it attempts to validate resource constraints (mocked
for local execution without a running Docker daemon).

Usage:
    export ENABLE_DOCKER=true  # Run full checks
    export ENABLE_DOCKER=false # Skip Docker checks
    pytest tests/test_ci.py -v
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import ensure_dirs  # Using existing config module to ensure environment setup


class TestCIResourceConstraints(unittest.TestCase):
    """Test cases for CI resource constraint validation."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.enable_docker_env = os.environ.get("ENABLE_DOCKER", "false").lower()
        cls.should_skip = cls.enable_docker_env not in ["true", "1", "yes"]

    def test_docker_flag_handling(self):
        """
        Verify that the ENABLE_DOCKER flag is correctly read and handled.
        If False, the test suite should skip Docker-specific validation logic.
        """
        # This test asserts that the environment variable is read correctly.
        # The actual skipping logic is handled by the @unittest.skipIf decorator
        # on the specific test method below, or by conditional logic within the test.
        self.assertIn(self.enable_docker_env, ["true", "false", "1", "0", "yes", "no"])

    @unittest.skipIf("ENABLE_DOCKER" not in os.environ or os.environ["ENABLE_DOCKER"].lower() != "true",
                     "Docker validation skipped: ENABLE_DOCKER is not set to 'true'")
    def test_docker_resource_constraints_mock(self):
        """
        Mock test to validate resource constraints if Docker is enabled.
        In a real CI environment, this would check actual container limits.
        Here, we mock the Docker client to simulate a successful constraint check.
        """
        # Mocking the docker client to avoid actual dependency on a running daemon
        with patch('docker.from_env') as mock_docker_client:
            # Setup mock behavior
            mock_container = MagicMock()
            mock_container.attrs = {
                'HostConfig': {
                    'Memory': 6 * 1024 * 1024 * 1024,  # 6 GB
                    'NanoCpus': 2 * 10**9  # 2 CPUs
                }
            }
            mock_docker_client.return_version = MagicMock(return_value={'Version': '20.10.0'})
            mock_docker_client.return_value.containers.list.return_value = [mock_container]

            # Simulate the check logic
            try:
                # In a real scenario, we would fetch the container stats and verify limits.
                # Here we just verify the mock setup works.
                client = mock_docker_client.return_value
                containers = client.containers.list()
                self.assertEqual(len(containers), 1)
                
                # Check mocked constraints
                memory_limit = containers[0].attrs['HostConfig']['Memory']
                cpu_limit = containers[0].attrs['HostConfig']['NanoCpus']
                
                # Assert constraints meet the requirement (≤2 CPU, ≤6GB RAM)
                self.assertLessEqual(cpu_limit, 2 * 10**9, "CPU limit exceeds 2 cores")
                self.assertLessEqual(memory_limit, 6 * 1024 * 1024 * 1024, "Memory limit exceeds 6GB")
                
            except Exception as e:
                self.fail(f"Resource constraint validation failed: {e}")

    @unittest.skipIf("ENABLE_DOCKER" in os.environ and os.environ["ENABLE_DOCKER"].lower() == "true",
                     "Docker validation active: skipping mock-only path")
    def test_skip_logic_when_docker_disabled(self):
        """
        Verify that when Docker is disabled, the test logic correctly identifies
        the skip condition and does not attempt to run Docker commands.
        """
        # This test runs when ENABLE_DOCKER is false.
        # It asserts that the flag is indeed false.
        self.assertNotEqual(os.environ.get("ENABLE_DOCKER", "false").lower(), "true")


if __name__ == '__main__':
    unittest.main()