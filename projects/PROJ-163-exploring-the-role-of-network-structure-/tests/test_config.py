"""
Tests for environment configuration management (T006).
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from code.config import IBMQuantumConfig, load_config, setup_ibm_runtime


class TestIBMQuantumConfig:
    """Unit tests for the IBMQuantumConfig dataclass."""

    def test_config_with_token(self):
        """Config should be valid when token is provided."""
        cfg = IBMQuantumConfig(token="fake_token_123")
        assert cfg.channel == "ibm_quantum"
        assert cfg.token == "fake_token_123"
        assert cfg.verify is True

    def test_config_missing_token_raises(self):
        """Config initialization should fail if token is missing for ibm_quantum."""
        with pytest.raises(ValueError, match="IBM Quantum token is missing"):
            IBMQuantumConfig(channel="ibm_quantum", token=None)

    def test_config_custom_channel(self):
        """Config should allow custom channel types."""
        cfg = IBMQuantumConfig(channel="ibm_cloud", token="cloud_token")
        assert cfg.channel == "ibm_cloud"


class TestLoadConfig:
    """Unit tests for load_config function."""

    @patch.dict(os.environ, {"IBMQ_TOKEN": "env_token_456"})
    def test_load_from_env_token_only(self):
        """Should load token from environment variable."""
        cfg = load_config()
        assert cfg.token == "env_token_456"
        assert cfg.channel == "ibm_quantum"

    @patch.dict(os.environ, {
        "IBMQ_TOKEN": "env_token_456",
        "IBMQ_CHANNEL": "ibm_cloud",
        "IBMQ_URL": "https://custom.url",
        "IBMQ_INSTANCE": "hub/group/project",
        "IBMQ_VERIFY": "false"
    })
    def test_load_full_env_config(self):
        """Should load all configuration options from environment."""
        cfg = load_config()
        assert cfg.token == "env_token_456"
        assert cfg.channel == "ibm_cloud"
        assert cfg.url == "https://custom.url"
        assert cfg.instance == "hub/group/project"
        assert cfg.verify is False

    @patch.dict(os.environ, {}, clear=True)
    def test_load_missing_token_raises(self):
        """Should raise ValueError if token is not in environment."""
        with pytest.raises(ValueError, match="IBM Quantum token is missing"):
            load_config()


class TestSetupIBMRuntime:
    """Integration-style tests for setup_ibm_runtime (mocked)."""

    @patch("code.config.QiskitRuntimeService")
    @patch.dict(os.environ, {"IBMQ_TOKEN": "mock_token"})
    def test_setup_runtime_success(self, mock_service_class):
        """Should return a service instance on success."""
        mock_instance = MagicMock()
        mock_service_class.return_value = mock_instance

        service = setup_ibm_runtime()

        mock_service_class.assert_called_once()
        assert service == mock_instance

    @patch("code.config.QiskitRuntimeService")
    @patch.dict(os.environ, {"IBMQ_TOKEN": "mock_token"})
    def test_setup_runtime_failure(self, mock_service_class):
        """Should raise RuntimeError if service init fails."""
        mock_service_class.side_effect = Exception("Auth failed")

        with pytest.raises(RuntimeError, match="Service initialization failed"):
            setup_ibm_runtime()