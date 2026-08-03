import os
import pytest
from pathlib import Path
import sys

# Add code to path if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import (
    get_project_root, 
    get_model_path, 
    get_arm_config, 
    validate_config,
    get_environment
)

class TestEnvironmentConfig:
    
    def test_get_project_root_default(self):
        """Test that get_project_root returns the correct path when no env var is set."""
        # Unset env var to test default
        original = os.environ.pop("PROJECT_ROOT", None)
        try:
            root = get_project_root()
            # Should be the parent of the code directory
            assert (root / "code").exists() or (root / "tests").exists()
        finally:
            if original:
                os.environ["PROJECT_ROOT"] = original

    def test_get_project_root_env(self, tmp_path):
        """Test that get_project_root respects PROJECT_ROOT env var."""
        original = os.environ.get("PROJECT_ROOT")
        try:
            os.environ["PROJECT_ROOT"] = str(tmp_path)
            root = get_project_root()
            assert root == tmp_path.resolve()
        finally:
            if original:
                os.environ["PROJECT_ROOT"] = original
            else:
                os.environ.pop("PROJECT_ROOT", None)

    def test_get_model_path_default(self):
        """Test default model path resolution."""
        root = get_project_root()
        model_path = get_model_path()
        assert model_path == root / "models"

    def test_get_model_path_env(self, tmp_path):
        """Test model path respects MODEL_DIR env var."""
        original = os.environ.get("MODEL_DIR")
        try:
            os.environ["MODEL_DIR"] = str(tmp_path / "custom_models")
            model_path = get_model_path()
            assert model_path == (tmp_path / "custom_models").resolve()
        finally:
            if original:
                os.environ["MODEL_DIR"] = original
            else:
                os.environ.pop("MODEL_DIR", None)

    def test_get_arm_config_defaults(self):
        """Test that get_arm_config returns correct defaults."""
        # Clear specific env vars to force defaults
        for key in ["ARM_TYPE", "MAX_TOKENS", "SEED", "MODEL_ID"]:
            os.environ.pop(key, None)
        
        config = get_arm_config()
        
        assert config["arm_type"] == "B"  # Per T005 requirement
        assert config["max_tokens"] == 4096
        assert config["seed"] == 42
        assert config["model_id"] == "mmpro/MMProLong-7B-1.0"
        assert config["arm_primary"] == "B"

    def test_get_arm_config_env_override(self):
        """Test that get_arm_config respects environment overrides."""
        original_env = {}
        keys = ["ARM_TYPE", "MAX_TOKENS", "SEED", "MODEL_ID"]
        try:
            for key in keys:
                original_env[key] = os.environ.get(key)
            
            os.environ["ARM_TYPE"] = "A"
            os.environ["MAX_TOKENS"] = "8192"
            os.environ["SEED"] = "123"
            os.environ["MODEL_ID"] = "test/model"
            
            config = get_arm_config()
            
            assert config["arm_type"] == "A"
            assert config["max_tokens"] == 8192
            assert config["seed"] == 123
            assert config["model_id"] == "test/model"
            # Primary should still be B if arm_type is B, but here arm_type is A
            # The logic in get_arm_config sets primary based on current arm_type
            # If ARM_TYPE is A, primary is A? Or always B? 
            # Looking at code: "arm_primary": "B" if arm_type == "B" else "A"
            # So if arm_type is A, arm_primary is A.
            assert config["arm_primary"] == "A"
            
        finally:
            for key in keys:
                if original_env[key] is not None:
                    os.environ[key] = original_env[key]
                else:
                    os.environ.pop(key, None)

    def test_validate_config_valid(self):
        """Test validation passes with valid config."""
        # Ensure valid defaults
        for key in ["ARM_TYPE", "MAX_TOKENS"]:
            os.environ.pop(key, None)
        
        assert validate_config() is True

    def test_validate_config_invalid_arm(self):
        """Test validation fails with invalid arm type."""
        original = os.environ.get("ARM_TYPE")
        try:
            os.environ["ARM_TYPE"] = "C"
            with pytest.raises(ValueError, match="Invalid ARM_TYPE"):
                validate_config()
        finally:
            if original:
                os.environ["ARM_TYPE"] = original
            else:
                os.environ.pop("ARM_TYPE", None)

    def test_validate_config_invalid_tokens(self):
        """Test validation fails with invalid token count."""
        original = os.environ.get("MAX_TOKENS")
        try:
            os.environ["MAX_TOKENS"] = "-100"
            with pytest.raises(ValueError, match="Invalid MAX_TOKENS"):
                validate_config()
        finally:
            if original:
                os.environ["MAX_TOKENS"] = original
            else:
                os.environ.pop("MAX_TOKENS", None)

    def test_get_environment(self):
        """Test that get_environment returns a dictionary."""
        env = get_environment()
        assert isinstance(env, dict)
        assert "PROJECT_ROOT" in env
        assert "MODEL_DIR" in env
        assert "ARM_TYPE" in env
        assert "MAX_TOKENS" in env
        assert "MODEL_ID" in env
        assert "SEED" in env