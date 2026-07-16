"""
Tests specifically for the CPU-only execution fixture.

These tests ensure that the autouse fixture in conftest.py is working correctly.
"""
import pytest
import os


class TestCPUOnlyFixture:
    """Test suite for CPU-only execution fixture."""

    def test_cuda_env_var_is_empty(self):
        """Verify that the CUDA_VISIBLE_DEVICES environment variable is empty."""
        # This test runs after the autouse fixture has been applied
        assert 'CUDA_VISIBLE_DEVICES' in os.environ
        assert os.environ['CUDA_VISIBLE_DEVICES'] == ''

    def test_tf_log_level_is_suppressed(self):
        """Verify that TensorFlow logging is suppressed."""
        # This test runs after the autouse fixture has been applied
        assert 'TF_CPP_MIN_LOG_LEVEL' in os.environ
        assert os.environ['TF_CPP_MIN_LOG_LEVEL'] == '3'

    def test_environment_persistence_across_tests(self):
        """Verify that the environment variables persist throughout the test session."""
        # This test verifies that the autouse fixture is applied consistently
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        assert os.environ.get('TF_CPP_MIN_LOG_LEVEL') == '3'

    @pytest.mark.parametrize("test_var", ["test1", "test2", "test3"])
    def test_environment_in_parametrized_test(self, test_var):
        """Verify that environment variables are set correctly in parametrized tests."""
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        assert os.environ.get('TF_CPP_MIN_LOG_LEVEL') == '3'
        # Test passes if we get here
        assert test_var in ["test1", "test2", "test3"]