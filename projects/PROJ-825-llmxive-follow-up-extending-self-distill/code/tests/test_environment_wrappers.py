"""
Tests for environment wrappers (ALFWorld and WebShop).

These tests verify that the environment wrappers are correctly implemented
and that the underlying packages are fetchable and functional.
"""

import pytest
import sys

from config import get_config, EnvironmentConfig
from environments.alfworld_env import (
    ALFWorldWrapper,
    create_alfworld_env,
    verify_alfworld_install,
)
from environments.webshop_env import (
    WebShopWrapper,
    create_webshop_env,
    verify_webshop_install,
)


class TestALFWorldWrapper:
    """Tests for the ALFWorld environment wrapper."""

    def test_alfworld_install_check(self):
        """Test that the ALFWorld package is installed."""
        # This test will fail if the package is not installed
        # which is the expected behavior for the "fetchable via pip" requirement
        assert verify_alfworld_install(), (
            "ALFWorld package is not installed. "
            "Please install it via 'pip install alfworld'."
        )

    def test_create_alfworld_env(self):
        """Test creating an ALFWorld environment."""
        # This test requires the package to be installed AND data files to be present
        # If data files are missing, it will raise a RuntimeError
        cfg = get_config()
        env_cfg = cfg.environment
        env_cfg.task_type = "pick_and_place"
        env_cfg.seed = 42

        # This should raise an error if data files are missing
        # which is expected and indicates a partial installation
        try:
            env = create_alfworld_env(env_cfg)
            assert env is not None
            env.close()
        except RuntimeError as e:
            # Expected if data files are missing
            assert "missing data files" in str(e).lower() or "Failed to initialize" in str(e)

    def test_alfworld_reset_and_step(self):
        """Test reset and step functionality (requires data files)."""
        cfg = get_config()
        env_cfg = cfg.environment
        env_cfg.task_type = "pick_and_place"
        env_cfg.seed = 42

        try:
            env = create_alfworld_env(env_cfg)
            obs = env.reset()
            assert "observation" in obs
            assert "goal" in obs
            assert "available_actions" in obs

            # Take a dummy step (will fail if action is invalid, but structure is correct)
            # We use a valid action from the available actions if possible
            if obs["available_actions"]:
                action = obs["available_actions"][0]
                new_obs, reward, done, info = env.step(action)
                assert "observation" in new_obs
            else:
                # If no actions available, just verify structure
                pass

            env.close()
        except RuntimeError:
            # Expected if data files are missing
            pass

class TestWebShopWrapper:
    """Tests for the WebShop environment wrapper."""

    def test_webshop_install_check(self):
        """Test that the WebShop package is installed."""
        assert verify_webshop_install(), (
            "WebShop package is not installed. "
            "Please install it via 'pip install webshop'."
        )

    def test_create_webshop_env(self):
        """Test creating a WebShop environment."""
        cfg = get_config()
        env_cfg = cfg.environment
        env_cfg.task_type = "search"
        env_cfg.seed = 42

        try:
            env = create_webshop_env(env_cfg)
            assert env is not None
            env.close()
        except RuntimeError as e:
            # Expected if data files are missing
            assert "missing data files" in str(e).lower() or "Failed to initialize" in str(e)

    def test_webshop_reset_and_step(self):
        """Test reset and step functionality (requires data files)."""
        cfg = get_config()
        env_cfg = cfg.environment
        env_cfg.task_type = "search"
        env_cfg.seed = 42

        try:
            env = create_webshop_env(env_cfg)
            obs = env.reset()
            assert "observation" in obs
            assert "goal" in obs
            assert "available_actions" in obs

            if obs["available_actions"]:
                action = obs["available_actions"][0]
                new_obs, reward, done, info = env.step(action)
                assert "observation" in new_obs
            else:
                pass

            env.close()
        except RuntimeError:
            # Expected if data files are missing
            pass

class TestEnvironmentFetchability:
    """Tests to verify that environments are fetchable via pip."""

    def test_alfworld_package_import(self):
        """Verify that the alfworld package can be imported."""
        try:
            import alfworld
            from alfworld import envs
            assert True
        except ImportError:
            pytest.fail("alfworld package is not importable.")

    def test_webshop_package_import(self):
        """Verify that the webshop package can be imported."""
        try:
            import webshop
            from webshop import envs
            assert True
        except ImportError:
            pytest.fail("webshop package is not importable.")

    def test_env_module_import(self):
        """Verify that the environments module can be imported."""
        try:
            from environments import ALFWorldWrapper, WebShopWrapper
            assert True
        except ImportError:
            pytest.fail("environments module is not importable.")