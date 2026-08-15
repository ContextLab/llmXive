"""
Tests for the IBM Quantum configuration management module.

These tests verify that:
- Environment variables are correctly loaded
- Validation logic works as expected
- The service setup handles errors appropriately
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from code.config import load_config, IBMQuantumConfig, setup_ibm_runtime
from qiskit_ibm_runtime.exceptions import IBMInputValueError

class TestIBMQuantumConfig:
    """Tests for the IBMQuantumConfig dataclass."""

    def test_valid_config_creation(self):
        """Test creation of a valid config object."""
        config = IBMQuantumConfig(token="valid_token_12345678901234567890123456789012")
        assert config.token == "valid_token_12345678901234567890123456789012"
        assert config.channel == "ibm_quantum"
        assert config.timeout_seconds == 120

    def test_config_with_optional_fields(self):
        """Test config with optional fields populated."""
        config = IBMQuantumConfig(
            token="valid_token_12345678901234567890123456789012",
            instance="ibm-q/open/main",
            url="https://custom.url/api",
            channel="ibm_cloud",
            timeout_seconds=60
        )
        assert config.instance == "ibm-q/open/main"
        assert config.url == "https://custom.url/api"
        assert config.channel == "ibm_cloud"
        assert config.timeout_seconds == 60

    def test_empty_token_raises_error(self):
        """Test that empty token raises ValueError."""
        with pytest.raises(ValueError, match="token cannot be empty"):
            IBMQuantumConfig(token="")

    def test_whitespace_token_raises_error(self):
        """Test that whitespace-only token raises ValueError."""
        with pytest.raises(ValueError, match="token cannot be empty"):
            IBMQuantumConfig(token="   ")

    def test_invalid_channel_raises_error(self):
        """Test that invalid channel raises ValueError."""
        with pytest.raises(ValueError, match="Invalid channel"):
            IBMQuantumConfig(token="valid_token_12345678901234567890123456789012", channel="invalid")

class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_missing_token(self):
        """Test that missing token raises RuntimeError."""
        # Ensure the env var is not set
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="IBM Quantum token not found"):
                load_config()

    def test_load_config_success(self):
        """Test successful loading of config from environment."""
        test_token = "test_token_12345678901234567890123456789012"
        with patch.dict(os.environ, {"IBM_QUANTUM_TOKEN": test_token}):
            config = load_config()
            assert config.token == test_token
            assert config.channel == "ibm_quantum"

    def test_load_config_with_all_env_vars(self):
        """Test loading config with all optional environment variables."""
        env_vars = {
            "IBM_QUANTUM_TOKEN": "test_token_12345678901234567890123456789012",
            "IBM_QUANTUM_INSTANCE": "ibm-q/open/main",
            "IBM_QUANTUM_URL": "https://custom.url/api",
            "IBM_QUANTUM_CHANNEL": "ibm_cloud",
            "IBM_QUANTUM_TIMEOUT": "60",
            "IBM_QUANTUM_MAX_RETRIES": "5",
            "IBM_QUANTUM_BACKOFF_FACTOR": "3"
        }
        with patch.dict(os.environ, env_vars):
            config = load_config()
            assert config.token == env_vars["IBM_QUANTUM_TOKEN"]
            assert config.instance == env_vars["IBM_QUANTUM_INSTANCE"]
            assert config.url == env_vars["IBM_QUANTUM_URL"]
            assert config.channel == env_vars["IBM_QUANTUM_CHANNEL"]
            assert config.timeout_seconds == 60
            assert config.max_retries == 5
            assert config.backoff_factor == 3

    def test_load_config_invalid_timeout(self):
        """Test that invalid timeout value raises ValueError."""
        with patch.dict(os.environ, {
            "IBM_QUANTUM_TOKEN": "test_token_12345678901234567890123456789012",
            "IBM_QUANTUM_TIMEOUT": "not_a_number"
        }):
            with pytest.raises(ValueError, match="Invalid numeric configuration value"):
                load_config()

class TestSetupIbmRuntime:
    """Tests for the setup_ibm_runtime function."""

    @patch('code.config.QiskitRuntimeService')
    def test_setup_success(self, mock_service_class):
        """Test successful service setup."""
        mock_service_instance = MagicMock()
        mock_service_instance.backends.return_value = [MagicMock(name="fake_backend")]
        mock_service_class.return_value = mock_service_instance

        config = IBMQuantumConfig(token="valid_token_12345678901234567890123456789012")
        service = setup_ibm_runtime(config)

        mock_service_class.assert_called_once_with(
            channel="ibm_quantum",
            token="valid_token_12345678901234567890123456789012",
            instance=None,
            url=None
        )
        assert service == mock_service_instance

    @patch('code.config.QiskitRuntimeService')
    def test_setup_with_config_params(self, mock_service_class):
        """Test service setup with specific config parameters."""
        mock_service_instance = MagicMock()
        mock_service_instance.backends.return_value = []
        mock_service_class.return_value = mock_service_instance

        config = IBMQuantumConfig(
            token="valid_token_12345678901234567890123456789012",
            instance="ibm-q/open/main",
            url="https://custom.url/api",
            channel="ibm_cloud"
        )
        service = setup_ibm_runtime(config)

        mock_service_class.assert_called_once_with(
            channel="ibm_cloud",
            token="valid_token_12345678901234567890123456789012",
            instance="ibm-q/open/main",
            url="https://custom.url/api"
        )

    @patch('code.config.QiskitRuntimeService')
    def test_setup_invalid_credentials(self, mock_service_class):
        """Test service setup with invalid credentials."""
        mock_service_class.side_effect = IBMInputValueError(
            "Invalid token", "Invalid token provided"
        )

        config = IBMQuantumConfig(token="invalid_token")
        with pytest.raises(RuntimeError, match="Configuration error"):
            setup_ibm_runtime(config)

    @patch('code.config.QiskitRuntimeService')
    def test_setup_runtime_error(self, mock_service_class):
        """Test service setup with runtime error."""
        from qiskit_ibm_runtime.exceptions import IBMRuntimeError
        mock_service_class.side_effect = IBMRuntimeError("Runtime error", "Connection failed")

        config = IBMQuantumConfig(token="valid_token_12345678901234567890123456789012")
        with pytest.raises(RuntimeError, match="Runtime error"):
            setup_ibm_runtime(config)
