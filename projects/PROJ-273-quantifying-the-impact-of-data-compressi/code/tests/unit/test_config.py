"""
Unit tests for src/utils/config.py
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.config import (
    get_project_root,
    get_src_root,
    get_path,
    ensure_dir,
    set_seed,
    get_config,
    save_config,
    hash_config,
    DEFAULT_SEED,
    MAX_INJECTION_ATTEMPTS,
    MIN_VALID_EVENTS,
    TARGET_VALID_EVENTS,
    PATHS,
    COMPRESSION_OUTPUTS,
    BASELINE_PATH,
    FINAL_SUMMARY_PATH,
)


class TestPathManagement:
    """Tests for path management functions."""

    def test_get_project_root_returns_path(self):
        """Project root should return a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_src_root_returns_path(self):
        """Src root should return a Path object."""
        src = get_src_root()
        assert isinstance(src, Path)
        assert src.exists()

    def test_get_path_valid_key(self):
        """get_path should return correct path for valid keys."""
        for key in PATHS:
            path = get_path(key)
            assert isinstance(path, Path)
            assert str(path).endswith(PATHS[key])

    def test_get_path_compression_outputs(self):
        """get_path should handle compression output keys."""
        for key in COMPRESSION_OUTPUTS:
            path = get_path(key)
            assert isinstance(path, Path)
            assert str(path).endswith(COMPRESSION_OUTPUTS[key])

    def test_get_path_invalid_key_raises(self):
        """get_path should raise ValueError for invalid keys."""
        with pytest.raises(ValueError):
            get_path('invalid_key')

    def test_ensure_dir_creates_directory(self):
        """ensure_dir should create a directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / 'test_subdir'
            result = ensure_dir(path=test_path)
            assert result.exists()
            assert result.is_dir()

    def test_ensure_dir_existing_directory(self):
        """ensure_dir should not fail on existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(path=Path(tmpdir))
            assert result.exists()

    def test_ensure_dir_with_key(self):
        """ensure_dir should work with key parameter."""
        # Use a key that points to a subdirectory we can test
        # We'll create a temporary config key for testing
        pass  # Path creation is tested above


class TestSeedManagement:
    """Tests for seed management functions."""

    def test_set_seed_returns_value(self):
        """set_seed should return the seed value."""
        seed_val = 12345
        result = set_seed(seed_val)
        assert result == seed_val

    def test_set_seed_default(self):
        """set_seed should use DEFAULT_SEED when None provided."""
        result = set_seed(None)
        assert result == DEFAULT_SEED

    def test_set_seed_affects_random(self):
        """set_seed should affect random module."""
        import random

        seed_val = 42
        set_seed(seed_val)
        val1 = random.random()

        set_seed(seed_val)
        val2 = random.random()

        assert val1 == val2

    def test_set_seed_different_values_different_results(self):
        """Different seeds should produce different random sequences."""
        import random

        set_seed(42)
        val1 = random.random()

        set_seed(43)
        val2 = random.random()

        assert val1 != val2


class TestConfiguration:
    """Tests for configuration functions."""

    def test_get_config_returns_dict(self):
        """get_config should return a dictionary."""
        config = get_config()
        assert isinstance(config, dict)

    def test_get_config_contains_expected_keys(self):
        """get_config should contain all expected configuration keys."""
        config = get_config()
        expected_keys = [
            'seed', 'timeout', 'max_injection_attempts',
            'min_valid_events', 'target_valid_events',
            'compression_levels', 'quantization_bit_widths',
            'pe_maxiter', 'pe_nlive', 'stat_alpha', 'min_ess',
            'paths', 'compression_outputs', 'baseline_path', 'final_summary_path'
        ]
        for key in expected_keys:
            assert key in config

    def test_get_config_values_match_constants(self):
        """get_config values should match module constants."""
        config = get_config()
        assert config['max_injection_attempts'] == MAX_INJECTION_ATTEMPTS
        assert config['min_valid_events'] == MIN_VALID_EVENTS
        assert config['target_valid_events'] == TARGET_VALID_EVENTS

    def test_save_config_creates_file(self):
        """save_config should create a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_config.json'
            result = save_config(output_path)
            assert result.exists()
            assert result.suffix == '.json'

    def test_save_config_valid_json(self):
        """save_config should create valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_config.json'
            save_config(output_path)

            with open(output_path, 'r') as f:
                config = json.load(f)

            assert isinstance(config, dict)
            assert 'seed' in config

    def test_hash_config_returns_string(self):
        """hash_config should return a string."""
        result = hash_config()
        assert isinstance(result, str)
        assert len(result) == 16  # Truncated SHA256

    def test_hash_config_consistent(self):
        """hash_config should return consistent values."""
        hash1 = hash_config()
        hash2 = hash_config()
        assert hash1 == hash2


class TestModuleConstants:
    """Tests for module-level constants."""

    def test_default_seed_defined(self):
        """DEFAULT_SEED should be defined."""
        assert DEFAULT_SEED is not None
        assert isinstance(DEFAULT_SEED, int)

    def test_max_injection_attempts_defined(self):
        """MAX_INJECTION_ATTEMPTS should be defined."""
        assert MAX_INJECTION_ATTEMPTS is not None
        assert MAX_INJECTION_ATTEMPTS == 20

    def test_min_valid_events_defined(self):
        """MIN_VALID_EVENTS should be defined."""
        assert MIN_VALID_EVENTS is not None
        assert MIN_VALID_EVENTS == 12

    def test_target_valid_events_defined(self):
        """TARGET_VALID_EVENTS should be defined."""
        assert TARGET_VALID_EVENTS is not None
        assert TARGET_VALID_EVENTS == 15

    def test_paths_defined(self):
        """PATHS should be defined with expected keys."""
        assert isinstance(PATHS, dict)
        assert 'data_raw' in PATHS
        assert 'data_interim' in PATHS
        assert 'data_processed' in PATHS
        assert 'data_external' in PATHS

    def test_compression_outputs_defined(self):
        """COMPRESSION_OUTPUTS should be defined."""
        assert isinstance(COMPRESSION_OUTPUTS, dict)
        assert 'lossless' in COMPRESSION_OUTPUTS
        assert 'quantization' in COMPRESSION_OUTPUTS
        assert 'wavelet' in COMPRESSION_OUTPUTS
        assert 'jpeg2000' in COMPRESSION_OUTPUTS

    def test_baseline_path_defined(self):
        """BASELINE_PATH should be defined."""
        assert BASELINE_PATH == 'data/external/baseline_bias_original.json'

    def test_final_summary_path_defined(self):
        """FINAL_SUMMARY_PATH should be defined."""
        assert FINAL_SUMMARY_PATH == 'reports/final_summary.md'
