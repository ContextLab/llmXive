"""
Unit tests for environment configuration management.
"""
import os
import tempfile
from pathlib import Path
import pytest

from utils.env_config import (
    load_environment,
    get_hf_token,
    get_env_var,
    validate_required_env_vars,
    get_environment_summary
)


class TestLoadEnvironment:
    def test_load_environment_from_file(self):
        """Test loading environment variables from a .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "TEST_VAR=hello\n"
                "ANOTHER_VAR=world\n"
                "# Comment line\n"
                "QUOTED_VAR=\"quoted value\"\n"
            )
            
            result = load_environment(env_path)
            
            assert result == {
                "TEST_VAR": "hello",
                "ANOTHER_VAR": "world",
                "QUOTED_VAR": "quoted value"
            }
            assert os.environ.get("TEST_VAR") == "hello"
            assert os.environ.get("ANOTHER_VAR") == "world"
            assert os.environ.get("QUOTED_VAR") == "quoted value"

    def test_load_environment_missing_file(self):
        """Test behavior when .env file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "nonexistent.env"
            
            result = load_environment(env_path)
            
            assert result == {}

    def test_load_environment_empty_file(self):
        """Test loading from an empty .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("")
            
            result = load_environment(env_path)
            
            assert result == {}

    def test_load_environment_with_comments_only(self):
        """Test loading from a .env file with only comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("# This is a comment\n# Another comment\n")
            
            result = load_environment(env_path)
            
            assert result == {}


class TestGetHfToken:
    def setup_method(self):
        """Clean up environment before each test."""
        # Remove HF tokens if they exist
        for key in ["HUGGING_FACE_TOKEN", "HF_TOKEN", "HuggingfaceToken"]:
            if key in os.environ:
                del os.environ[key]

    def test_get_hf_token_from_huggingface_token(self):
        """Test retrieving token from HUGGING_FACE_TOKEN."""
        os.environ["HUGGING_FACE_TOKEN"] = "hf_test_token_1"
        token = get_hf_token()
        assert token == "hf_test_token_1"

    def test_get_hf_token_from_hf_token(self):
        """Test retrieving token from HF_TOKEN."""
        os.environ["HF_TOKEN"] = "hf_test_token_2"
        token = get_hf_token()
        assert token == "hf_test_token_2"

    def test_get_hf_token_from_huggingfaceToken(self):
        """Test retrieving token from HuggingfaceToken."""
        os.environ["HuggingfaceToken"] = "hf_test_token_3"
        token = get_hf_token()
        assert token == "hf_test_token_3"

    def test_get_hf_token_priority(self):
        """Test that HUGGING_FACE_TOKEN has highest priority."""
        os.environ["HUGGING_FACE_TOKEN"] = "hf_priority_1"
        os.environ["HF_TOKEN"] = "hf_priority_2"
        os.environ["HuggingfaceToken"] = "hf_priority_3"
        
        token = get_hf_token()
        assert token == "hf_priority_1"

    def test_get_hf_token_missing(self):
        """Test that ValueError is raised when no token is found."""
        with pytest.raises(ValueError) as excinfo:
            get_hf_token()
        
        assert "Hugging Face token not found" in str(excinfo.value)


class TestGetEnvVar:
    def setup_method(self):
        """Clean up environment before each test."""
        for key in ["TEST_VAR", "REQUIRED_VAR"]:
            if key in os.environ:
                del os.environ[key]

    def test_get_env_var_existing(self):
        """Test getting an existing environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        value = get_env_var("TEST_VAR")
        assert value == "test_value"

    def test_get_env_var_with_default(self):
        """Test getting a non-existing variable with default."""
        value = get_env_var("NON_EXISTING", default="default_value")
        assert value == "default_value"

    def test_get_env_var_required_missing(self):
        """Test that ValueError is raised for required missing variable."""
        with pytest.raises(ValueError) as excinfo:
            get_env_var("NON_EXISTING", required=True)
        
        assert "Required environment variable" in str(excinfo.value)

    def test_get_env_var_required_present(self):
        """Test that no error is raised for required present variable."""
        os.environ["REQUIRED_VAR"] = "present_value"
        value = get_env_var("REQUIRED_VAR", required=True)
        assert value == "present_value"


class TestValidateRequiredEnvVars:
    def setup_method(self):
        """Clean up environment before each test."""
        for key in ["VAR_A", "VAR_B", "VAR_C"]:
            if key in os.environ:
                del os.environ[key]

    def test_validate_all_present(self):
        """Test validation when all required variables are present."""
        os.environ["VAR_A"] = "a"
        os.environ["VAR_B"] = "b"
        
        result = validate_required_env_vars(["VAR_A", "VAR_B"])
        assert result is True

    def test_validate_missing_variable(self):
        """Test validation when a required variable is missing."""
        os.environ["VAR_A"] = "a"
        
        with pytest.raises(ValueError) as excinfo:
            validate_required_env_vars(["VAR_A", "VAR_B"])
        
        assert "Missing required environment variables" in str(excinfo.value)

    def test_validate_empty_list(self):
        """Test validation with an empty list of required variables."""
        result = validate_required_env_vars([])
        assert result is True


class TestGetEnvironmentSummary:
    def test_get_environment_summary(self):
        """Test that environment summary returns expected structure."""
        summary = get_environment_summary()
        
        assert "env_file_exists" in summary
        assert "hf_token_configured" in summary
        assert "loaded_vars_count" in summary
        assert "python_path" in summary
        
        assert isinstance(summary["env_file_exists"], bool)
        assert isinstance(summary["hf_token_configured"], bool)
        assert isinstance(summary["loaded_vars_count"], int)
        assert isinstance(summary["python_path"], str)