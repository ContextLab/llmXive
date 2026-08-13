"""
Unit tests for src/evaluation/init_env_logic.py
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluation.init_env_logic import verify_alfworld_environment, run_alfworld_dry_run


class TestVerifyAlfworldEnvironment:
    """Tests for verify_alfworld_environment function."""

    @patch("src.evaluation.init_env_logic.alfworld")
    @patch("src.evaluation.init_env_logic.alfworld_env")
    def test_environment_available(self, mock_env, mock_alfworld):
        """Test that function returns True when environment is available."""
        # Setup mocks
        mock_alfworld.__file__ = "/fake/path/alfworld/__init__.py"
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_alfworld_path = Path("/fake/path/alfworld")
        mock_alfworld_path.__truediv__ = lambda self, key: mock_config_path

        with patch("src.evaluation.init_env_logic.Path") as mock_path_cls:
            mock_path_cls.return_value = mock_alfworld_path

            result = verify_alfworld_environment()

            assert result is True

    def test_environment_not_available_import_error(self):
        """Test that function returns False when import fails."""
        with patch.dict(sys.modules, {"alfworld": None}):
            # Force import error by mocking the import
            with patch("builtins.__import__", side_effect=ImportError("No module named 'alfworld'")):
                result = verify_alfworld_environment()
                assert result is False


class TestRunAlfworldDryRun:
    """Tests for run_alfworld_dry_run function."""

    @patch("src.evaluation.init_env_logic.verify_alfworld_environment")
    def test_dry_run_success(self, mock_verify):
        """Test successful dry-run execution."""
        mock_verify.return_value = True

        # Mock the environment classes
        mock_env_instance = MagicMock()
        mock_env_instance.reset.return_value = "Initial observation"
        mock_env_instance.step.return_value = ("New observation", 1.0, False, {})

        mock_env_class = MagicMock(return_value=mock_env_instance)
        mock_load_config = MagicMock(return_value={})

        with patch("src.evaluation.init_env_logic.alfworld_env") as mock_env_module:
            with patch("src.evaluation.init_env_logic.load_config", mock_load_config):
                mock_env_module.ALFWorldEnv = mock_env_class

                success, message = run_alfworld_dry_run("pick_and_place_simple")

                assert success is True
                assert "passed" in message.lower()
                mock_env_instance.reset.assert_called_once()
                mock_env_instance.step.assert_called_once()

    @patch("src.evaluation.init_env_logic.verify_alfworld_environment")
    def test_dry_run_failure_invalid_reward(self, mock_verify):
        """Test dry-run failure when reward is invalid."""
        mock_verify.return_value = True

        mock_env_instance = MagicMock()
        mock_env_instance.reset.return_value = "Initial observation"
        mock_env_instance.step.return_value = ("New observation", "invalid_reward", False, {})

        mock_env_class = MagicMock(return_value=mock_env_instance)
        mock_load_config = MagicMock(return_value={})

        with patch("src.evaluation.init_env_logic.alfworld_env") as mock_env_module:
            with patch("src.evaluation.init_env_logic.load_config", mock_load_config):
                mock_env_module.ALFWorldEnv = mock_env_class

                success, message = run_alfworld_dry_run("pick_and_place_simple")

                assert success is False
                assert "unexpected reward" in message.lower()

    @patch("src.evaluation.init_env_logic.verify_alfworld_environment")
    def test_dry_run_environment_not_available(self, mock_verify):
        """Test dry-run failure when environment is not available."""
        mock_verify.return_value = False

        success, message = run_alfworld_dry_run("pick_and_place_simple")

        assert success is False
        assert "verification failed" in message.lower()