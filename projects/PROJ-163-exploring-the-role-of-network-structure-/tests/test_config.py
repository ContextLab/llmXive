"""
Tests for the IBM Quantum configuration management module.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from code.config import (
    IBMQuantumConfig,
    load_config,
    setup_ibm_runtime
)

class TestIBMQuantumConfig:
    """Tests for the IBMQuantumConfig class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        config = IBMQuantumConfig(token="fake_token_1234567890")
        assert config.token == "fake_token_1234567890"
        assert config.channel == "ibm_quantum"
        assert config.timeout == 60
        assert config.max_retries == 3
        assert config.url is None
        assert config.instance is None

    def test_init_custom(self):
        """Test initialization with custom values."""
        config = IBMQuantumConfig(
            token="my_token",
            instance="hub/group/project",
            channel="ibm_cloud",
            url="https://custom.url",
            timeout=120,
            max_retries=5
        )
        assert config.token == "my_token"
        assert config.instance == "hub/group/project"
        assert config.channel == "ibm_cloud"
        assert config.url == "https://custom.url"
        assert config.timeout == 120
        assert config.max_retries == 5

    def test_validate_success(self):
        """Test validation with a valid token."""
        config = IBMQuantumConfig(token="a" * 30)
        assert config.validate() is True
        assert config._validated is True

    def test_validate_missing_token(self):
        """Test validation fails if token is missing."""
        config = IBMQuantumConfig(token=None)
        assert config.validate() is False
        assert config._validated is False

    def test_validate_short_token(self):
        """Test validation fails if token is too short."""
        config = IBMQuantumConfig(token="short")
        assert config.validate() is False

    def test_from_env(self):
        """Test loading from environment variables."""
        with patch.dict(os.environ, {
            "IBM_QUANTUM_TOKEN": "env_token_1234567890",
            "IBM_QUANTUM_INSTANCE": "env_hub/env_group",
            "IBM_QUANTUM_TIMEOUT": "90",
            "IBM_QUANTUM_MAX_RETRIES": "4"
        }):
            config = IBMQuantumConfig.from_env()
            assert config.token == "env_token_1234567890"
            assert config.instance == "env_hub/env_group"
            assert config.timeout == 90
            assert config.max_retries == 4

    def test_from_env_defaults(self):
        """Test loading from environment uses defaults when vars missing."""
        with patch.dict(os.environ, {}, clear=True):
            config = IBMQuantumConfig.from_env()
            assert config.token is None
            assert config.timeout == 60
            assert config.max_retries == 3

    def test_from_file_valid(self):
        """Test loading from a valid YAML file."""
        yaml_content = """
        token: file_token_1234567890
        instance: file_hub/file_group
        timeout: 100
        max_retries: 6
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            config = IBMQuantumConfig.from_file(temp_path)
            assert config.token == "file_token_1234567890"
            assert config.instance == "file_hub/file_group"
            assert config.timeout == 100
            assert config.max_retries == 6
        finally:
            temp_path.unlink()

    def test_from_file_invalid_yaml(self):
        """Test loading from an invalid YAML file raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError):
                IBMQuantumConfig.from_file(temp_path)
        finally:
            temp_path.unlink()

    def test_from_file_not_found(self):
        """Test loading from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            IBMQuantumConfig.from_file(Path("/nonexistent/path/config.yaml"))

    def test_get_runtime_credentials(self):
        """Test generating credentials dict for qiskit-ibm-runtime."""
        config = IBMQuantumConfig(
            token="my_token",
            instance="hub/group/project",
            url="https://custom.url"
        )
        creds = config.get_runtime_credentials()
        assert creds == {
            "channel": "ibm_quantum",
            "token": "my_token",
            "instance": "hub/group/project",
            "url": "https://custom.url"
        }

        # Test without optional fields
        config_min = IBMQuantumConfig(token="my_token")
        creds_min = config_min.get_runtime_credentials()
        assert creds_min == {
            "channel": "ibm_quantum",
            "token": "my_token"
        }

class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_from_file(self):
        """Test load_config prioritizes file over env."""
        yaml_content = """
        token: file_token_1234567890
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            # Set env var to different value
            with patch.dict(os.environ, {"IBM_QUANTUM_TOKEN": "env_token_1234567890"}):
                config = load_config(temp_path)
                assert config.token == "file_token_1234567890"
        finally:
            temp_path.unlink()

    def test_load_from_env_fallback(self):
        """Test load_config falls back to env if file missing."""
        with patch.dict(os.environ, {"IBM_QUANTUM_TOKEN": "env_token_1234567890"}):
            config = load_config(Path("/nonexistent.yaml"))
            assert config.token == "env_token_1234567890"

    def test_load_default_file(self):
        """Test load_config looks for default config.yaml in cwd."""
        # This test is tricky without a real file in cwd, so we mock the check
        # We verify the logic by ensuring it tries to load from cwd if no path given
        # and falls back to env if not found.
        with patch.dict(os.environ, {"IBM_QUANTUM_TOKEN": "env_token_1234567890"}):
            # Mock Path.cwd() to return a temp dir with no config
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch('code.config.Path.cwd', return_value=Path(tmpdir)):
                    config = load_config()
                    assert config.token == "env_token_1234567890"

class TestSetupIbmRuntime:
    """Tests for the setup_ibm_runtime function."""

    def test_setup_with_valid_config(self):
        """Test setup_ibm_runtime with a valid config object."""
        config = IBMQuantumConfig(token="valid_token_1234567890")
        
        # Clear env vars first
        vars_to_clear = ["IBM_QUANTUM_TOKEN", "IBM_QUANTUM_INSTANCE", "IBM_QUANTUM_URL"]
        original = {}
        for v in vars_to_clear:
            original[v] = os.environ.pop(v, None)

        try:
            setup_ibm_runtime(config)
            assert os.environ.get("IBM_QUANTUM_TOKEN") == "valid_token_1234567890"
        finally:
            # Restore original env
            for k, v in original.items():
                if v is not None:
                    os.environ[k] = v
                elif k in os.environ:
                    del os.environ[k]

    def test_setup_with_invalid_config(self):
        """Test setup_ibm_runtime raises RuntimeError with invalid config."""
        config = IBMQuantumConfig(token=None)
        
        with pytest.raises(RuntimeError, match="IBM Quantum configuration is invalid"):
            setup_ibm_runtime(config)

    def test_setup_uses_env_if_not_set(self):
        """Test setup_ibm_runtime sets env vars only if not already set."""
        config = IBMQuantumConfig(token="new_token_1234567890")
        
        # Set existing env var
        original_token = os.environ.get("IBM_QUANTUM_TOKEN")
        os.environ["IBM_QUANTUM_TOKEN"] = "existing_token_1234567890"
        
        try:
            setup_ibm_runtime(config)
            # Should not overwrite existing
            assert os.environ.get("IBM_QUANTUM_TOKEN") == "existing_token_1234567890"
        finally:
            if original_token is not None:
                os.environ["IBM_QUANTUM_TOKEN"] = original_token
            elif "IBM_QUANTUM_TOKEN" in os.environ:
                del os.environ["IBM_QUANTUM_TOKEN"]