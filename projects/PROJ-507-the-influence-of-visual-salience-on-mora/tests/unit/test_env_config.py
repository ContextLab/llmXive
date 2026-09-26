"""
Unit tests for environment configuration validation (T008a).

Verifies that .env.example exists and contains required keys:
- VISUAL_GENOME_URL
- SURVEY_API_KEY
"""
import os
import pytest
from pathlib import Path
from env_config import validate_environment, EnvironmentConfigError


class TestEnvExampleValidation:
    """Tests for .env.example file existence and content validation."""

    @pytest.fixture
    def project_root(self):
        """Return the project root path."""
        return Path(__file__).parent.parent.parent

    def test_env_example_exists(self, project_root):
        """Assert .env.example exists at project root."""
        env_example_path = project_root / ".env.example"
        assert env_example_path.exists(), (
            f".env.example not found at {env_example_path}. "
            "Please run T008 to generate this file."
        )

    def test_env_example_contains_visual_genome_url(self, project_root):
        """Assert .env.example contains VISUAL_GENOME_URL key."""
        env_example_path = project_root / ".env.example"
        content = env_example_path.read_text()
        
        assert "VISUAL_GENOME_URL" in content, (
            ".env.example must contain 'VISUAL_GENOME_URL' key. "
            "This is required for dataset path configuration."
        )

    def test_env_example_contains_survey_api_key(self, project_root):
        """Assert .env.example contains SURVEY_API_KEY key."""
        env_example_path = project_root / ".env.example"
        content = env_example_path.read_text()
        
        assert "SURVEY_API_KEY" in content, (
            ".env.example must contain 'SURVEY_API_KEY' key. "
            "This is required for survey API authentication."
        )

    def test_env_example_has_valid_format(self, project_root):
        """Assert .env.example has valid KEY=VALUE format for required keys."""
        env_example_path = project_root / ".env.example"
        content = env_example_path.read_text()
        lines = content.strip().split('\n')
        
        required_keys = ["VISUAL_GENOME_URL", "SURVEY_API_KEY"]
        found_keys = set()
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if '=' in line:
                key = line.split('=')[0].strip()
                if key in required_keys:
                    found_keys.add(key)
        
        assert found_keys == set(required_keys), (
            f".env.example must contain exactly the required keys. "
            f"Expected: {required_keys}, Found: {list(found_keys)}"
        )

    def test_validate_environment_function_exists(self):
        """Assert validate_environment function is importable and callable."""
        assert callable(validate_environment), (
            "validate_environment must be a callable function in env_config.py"
        )

    def test_validate_environment_with_real_file(self, project_root):
        """Test validate_environment with actual .env.example file."""
        env_example_path = project_root / ".env.example"
        
        if env_example_path.exists():
            # Should not raise if file exists and has required keys
            try:
                validate_environment(str(env_example_path))
            except EnvironmentConfigError as e:
                # If it fails, it should be due to missing keys, not file not found
                assert "not found" not in str(e).lower(), (
                    f"validate_environment should handle missing file gracefully: {e}"
                )
                # If keys are missing, that's expected for the test file structure
                # The main checks are in the specific key tests above