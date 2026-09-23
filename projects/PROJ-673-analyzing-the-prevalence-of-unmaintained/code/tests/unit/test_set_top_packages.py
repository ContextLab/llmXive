"""
Unit tests for T017a: Set DEFAULT TOP_PACKAGES count for adaptive sampling.

These tests verify that:
1. The default value is set correctly in the environment.
2. The .env file is updated or created correctly.
3. The value can be read back from the environment.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.set_top_packages import (
    set_default_top_packages,
    update_env_file,
    verify_setting,
    DEFAULT_TOP_PACKAGES,
    ENV_VAR_NAME
)

class TestSetTopPackages:
    """Tests for the set_top_packages configuration script."""

    def test_default_value_is_correct(self):
        """Verify the DEFAULT_TOP_PACKAGES constant is 100."""
        assert DEFAULT_TOP_PACKAGES == 100, "Default should be 100"

    @patch('src.config.set_top_packages.os.environ')
    def test_sets_environment_variable(self, mock_environ):
        """Verify the function sets the environment variable."""
        set_default_top_packages(100)
        mock_environ.__setitem__.assert_called_with(ENV_VAR_NAME, "100")

    @patch('src.config.set_top_packages.update_env_file')
    @patch('src.config.set_top_packages.os.environ')
    def test_calls_update_env_file(self, mock_environ, mock_update_env):
        """Verify the function updates the .env file."""
        set_default_top_packages(100)
        mock_update_env.assert_called_once_with(100)

    @patch('src.config.set_top_packages.ENV_FILE_PATH')
    @patch('builtins.open', new_callable=mock_open)
    def test_creates_env_file_if_not_exists(self, mock_file, mock_env_path):
        """Verify a new .env file is created if it doesn't exist."""
        mock_env_path.exists.return_value = False
        
        update_env_file(100)
        
        mock_file.assert_called_once_with(mock_env_path, 'w', encoding='utf-8')
        handle = mock_file()
        # Check that the file was written with the correct content
        written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
        assert f"{ENV_VAR_NAME}=100" in written_content

    @patch('src.config.set_top_packages.ENV_FILE_PATH')
    @patch('builtins.open', new_callable=mock_open, read_data=f"{ENV_VAR_NAME}=50\nOTHER_VAR=value\n")
    def test_updates_existing_env_file(self, mock_file, mock_env_path):
        """Verify an existing .env file is updated correctly."""
        mock_env_path.exists.return_value = True
        
        update_env_file(100)
        
        handle = mock_file()
        written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
        assert f"{ENV_VAR_NAME}=100" in written_content
        assert f"{ENV_VAR_NAME}=50" not in written_content
        assert "OTHER_VAR=value" in written_content

    @patch('src.config.set_top_packages.os.getenv')
    def test_verify_setting_returns_true_on_match(self, mock_getenv):
        """Verify the verification function returns True when values match."""
        mock_getenv.return_value = str(DEFAULT_TOP_PACKAGES)
        
        result = verify_setting()
        
        assert result is True

    @patch('src.config.set_top_packages.os.getenv')
    def test_verify_setting_returns_false_on_mismatch(self, mock_getenv):
        """Verify the verification function returns False when values don't match."""
        mock_getenv.return_value = "50"
        
        result = verify_setting()
        
        assert result is False

    def test_cli_override_simulation(self):
        """
        Simulate the scenario where a CLI argument overrides the default.
        This verifies that the environment variable is mutable and can be
        overridden, as required by the task specification.
        """
        # Set the default
        os.environ[ENV_VAR_NAME] = str(DEFAULT_TOP_PACKAGES)
        assert os.getenv(ENV_VAR_NAME) == "100"
        
        # Simulate CLI override
        os.environ[ENV_VAR_NAME] = "500"
        assert os.getenv(ENV_VAR_NAME) == "500"
        
        # Reset to default for other tests
        os.environ[ENV_VAR_NAME] = str(DEFAULT_TOP_PACKAGES)