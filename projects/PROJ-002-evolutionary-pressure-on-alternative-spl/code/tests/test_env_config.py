"""
Unit tests for environment configuration management (T008).

Verifies that:
1. Config file loads correctly for both CI and HPC modes.
2. Constraints are retrieved accurately.
3. Replicate validation logic enforces mode-specific rules.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.env_config import (
    load_environment_config,
    get_constraint,
    get_tool_param,
    validate_replicate_count
)

@pytest.fixture
def ci_config():
    """Fixture to load CI configuration."""
    return load_environment_config('ci_sampled')

@pytest.fixture
def hpc_config():
    """Fixture to load HPC configuration."""
    return load_environment_config('hpc_full')

class TestConfigLoading:
    def test_load_ci_mode(self, ci_config):
        """Verify CI mode loads with correct description."""
        assert ci_config is not None
        assert 'ci_sampled' in str(ci_config.get('description', '')).lower()
        assert ci_config.get('use_synthetic_data') is True

    def test_load_hpc_mode(self, hpc_config):
        """Verify HPC mode loads with correct description."""
        assert hpc_config is not None
        assert 'hpc_full' in str(hpc_config.get('description', '')).lower()
        assert hpc_config.get('use_synthetic_data') is False

    def test_invalid_mode_raises_error(self):
        """Verify loading a non-existent mode raises KeyError."""
        with pytest.raises(KeyError):
            load_environment_config('non_existent_mode')

class TestConstraintRetrieval:
    def test_get_max_replicates_ci(self, ci_config):
        """Verify CI mode max replicates constraint."""
        max_rep = get_constraint(ci_config, 'max_replicates_per_species')
        assert max_rep == 1

    def test_get_min_replicates_hpc(self, hpc_config):
        """Verify HPC mode min replicates constraint."""
        min_rep = get_constraint(hpc_config, 'min_replicates_per_species')
        assert min_rep == 3

    def test_get_tool_param_star(self, ci_config):
        """Verify STAR parameter retrieval."""
        run_mode = get_tool_param(ci_config, 'star_params', 'runMode')
        assert run_mode == 'singleEnd'

    def test_missing_constraint_returns_default(self, ci_config):
        """Verify missing constraint returns default value."""
        val = get_constraint(ci_config, 'non_existent_constraint', default=99)
        assert val == 99

class TestReplicateValidation:
    def test_ci_mode_allows_single_replicate(self, ci_config):
        """Verify CI mode allows 1 replicate."""
        result = validate_replicate_count(ci_config, 1, "Human")
        assert result is True

    def test_hpc_mode_requires_minimum(self, hpc_config):
        """Verify HPC mode rejects < 3 replicates."""
        with pytest.raises(ValueError, match="minimum required is 3"):
            validate_replicate_count(hpc_config, 2, "Human")

    def test_hpc_mode_allows_valid_count(self, hpc_config):
        """Verify HPC mode allows 3-10 replicates."""
        result = validate_replicate_count(hpc_config, 5, "Chimp")
        assert result is True

    def test_hpc_mode_rejects_maximum(self, hpc_config):
        """Verify HPC mode rejects > 10 replicates."""
        with pytest.raises(ValueError, match="maximum allowed is 10"):
            validate_replicate_count(hpc_config, 11, "Macaque")

class TestConfigIntegration:
    def test_config_reflects_env_var(self):
        """Verify environment variable can override default mode (if implemented)."""
        # This test assumes the system might use an env var like PIPELINE_MODE
        # For now, we just verify the config structure is robust
        ci = load_environment_config('ci_sampled')
        hpc = load_environment_config('hpc_full')
        
        # Ensure they have distinct constraints
        assert get_constraint(ci, 'max_replicates_per_species') != get_constraint(hpc, 'max_replicates_per_species')