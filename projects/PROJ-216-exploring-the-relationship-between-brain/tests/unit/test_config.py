"""
Unit tests for the environment configuration management (T008).

Tests cover:
- Default values
- CI environment override (N=10)
- Explicit environment variable overrides
"""
import os
import pytest

# Import the functions from the module we just created
# Note: The import path assumes the test is run from the project root
# or that 'code' is in sys.path. The task implementation ensures
# the file structure supports this.
from code.config import (
    get_dataset_ids,
    get_sample_limit,
    DEFAULT_DATASET_IDS,
    DEFAULT_SAMPLE_LIMIT,
    CI_SAMPLE_LIMIT,
    ENV_DATASET_IDS,
    ENV_SAMPLE_LIMIT,
    CI_ENV_VAR
)


class TestGetDatasetIds:
    def test_default_values(self):
        """Test that default dataset IDs are returned when no env var is set."""
        # Ensure env var is not set
        if ENV_DATASET_IDS in os.environ:
            del os.environ[ENV_DATASET_IDS]

        result = get_dataset_ids()
        assert result == DEFAULT_DATASET_IDS
        assert "ds000224" in result
        assert "ds000230" in result

    def test_env_var_override(self):
        """Test that env var correctly overrides default dataset IDs."""
        test_ids = "ds009999,ds008888"
        os.environ[ENV_DATASET_IDS] = test_ids

        result = get_dataset_ids()
        assert result == ["ds009999", "ds008888"]

        # Cleanup
        del os.environ[ENV_DATASET_IDS]

    def test_env_var_whitespace_handling(self):
        """Test that whitespace in env var is handled correctly."""
        os.environ[ENV_DATASET_IDS] = " ds007777 , ds006666 "
        result = get_dataset_ids()
        assert result == ["ds007777", "ds006666"]
        del os.environ[ENV_DATASET_IDS]


class TestGetSampleLimit:
    def test_default_value(self):
        """Test default sample limit (Spec SC-001) when no env vars are set."""
        # Ensure env vars are not set
        for var in [CI_ENV_VAR, ENV_SAMPLE_LIMIT]:
            if var in os.environ:
                del os.environ[var]

        result = get_sample_limit()
        assert result == DEFAULT_SAMPLE_LIMIT
        assert result == 50

    def test_ci_environment_override(self):
        """Test that CI environment forces sample limit to 10 (Plan constraint)."""
        # Ensure other env vars are cleared
        if ENV_SAMPLE_LIMIT in os.environ:
            del os.environ[ENV_SAMPLE_LIMIT]

        os.environ[CI_ENV_VAR] = "true"
        result = get_sample_limit()
        assert result == CI_SAMPLE_LIMIT
        assert result == 10

        del os.environ[CI_ENV_VAR]

    def test_explicit_env_override(self):
        """Test that explicit LMMXIVE_SAMPLE_LIMIT overrides default."""
        if CI_ENV_VAR in os.environ:
            del os.environ[CI_ENV_VAR]

        os.environ[ENV_SAMPLE_LIMIT] = "25"
        result = get_sample_limit()
        assert result == 25

        del os.environ[ENV_SAMPLE_LIMIT]

    def test_ci_takes_precedence_over_explicit(self):
        """Test that CI limit (10) overrides an explicit larger limit."""
        os.environ[CI_ENV_VAR] = "true"
        os.environ[ENV_SAMPLE_LIMIT] = "100"

        result = get_sample_limit()
        # CI constraint should win
        assert result == 10

        del os.environ[CI_ENV_VAR]
        del os.environ[ENV_SAMPLE_LIMIT]