import pytest
import sys
from unittest.mock import MagicMock, patch
from environments.alfworld_env import ALFWorldWrapper
from environments.webshop_env import WebShopWrapper

class TestALFWorldWrapper:
    def test_alfworld_initialization(self):
        """Verify that the wrapper attempts to instantiate AlfredTWEnv correctly."""
        with patch("alfworld.AlfredTWEnv") as mock_env_cls:
        
            wrapper = ALFWorldWrapper(task_type="test_task", config={"seed": 42})
            # Trigger lazy initialization
            wrapper.reset()
            
            mock_env_cls.assert_called_once_with(task_type="test_task", seed=42)
            assert wrapper._initialized is True

    def test_alfworld_delegation(self):
        """Verify that reset and step calls are delegated to the underlying env."""
        with patch("alfworld.AlfredTWEnv") as mock_env_cls:
            mock_env_inst = mock_env_cls.return_value
            mock_env_inst.reset.return_value = ("obs1", {"status": "ok"})
            mock_env_inst.step.return_value = ("obs2", 1.0, False, {})

            wrapper = ALFWorldWrapper()
            
            obs, info = wrapper.reset()
            assert obs == "obs1"
            assert info["status"] == "ok"
            
            obs, rew, done, info = wrapper.step("move forward")
            assert obs == "obs2"
            assert rew == 1.0
            assert done is False

class TestWebShopWrapper:
    def test_webshop_initialization(self):
        """Verify that the wrapper attempts to instantiate WebShopEnv correctly."""
        with patch("webshop.WebShopEnv") as mock_env_cls:
            
                wrapper = WebShopWrapper(config={"seed": 123})
                wrapper.reset()
                
                mock_env_cls.assert_called_once_with(seed=123)
                assert wrapper._initialized is True

    def test_webshop_delegation(self):
        """Verify that reset and step calls are delegated to the underlying env."""
        with patch("webshop.WebShopEnv") as mock_env_cls:
            mock_env_inst = mock_env_cls.return_value
            mock_env_inst.reset.return_value = ("obs_ws", {"status": "ok"})
            mock_env_inst.step.return_value = ("obs_ws_2", 0.5, True, {})

            wrapper = WebShopWrapper()
            
            obs, info = wrapper.reset()
            assert obs == "obs_ws"
            
            obs, rew, done, info = wrapper.step("search laptop")
            assert obs == "obs_ws_2"
            assert rew == 0.5
            assert done is True

class TestEnvironmentFetchability:
    def test_alfworld_import_failure(self):
        """Verify that importing the wrapper fails if alfworld is missing."""
        with patch.dict(sys.modules, {"alfworld": None}):
            with pytest.raises(RuntimeError, match="ALFWorld is not installed"):
                # We must reload the module or use a fresh import to trigger the top-level check
                import importlib
                import environments.alfworld_env
                importlib.reload(environments.alfworld_env)

    def test_webshop_import_failure(self):
        """Verify that importing the wrapper fails if webshop is missing."""
        with patch.dict(sys.modules, {"webshop": None}):
            with pytest.raises(RuntimeError, match="WebShop is not installed"):
                import importlib
                import environments.webshop_env
                importlib.reload(environments.webshop_env)