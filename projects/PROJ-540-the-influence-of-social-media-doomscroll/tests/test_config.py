import pytest
import random
import numpy as np
import logging
from pathlib import Path
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import (
    ConfigError,
    load_config,
    set_seed,
    verify_and_apply_seed,
    log_seed_status,
    get_dataset_url,
    ensure_directories
)

# Mock config for testing
MOCK_CONFIG_VALID = {
    'seed': 42,
    'dataset_url': 'https://example.com/data.csv'
}

MOCK_CONFIG_NO_SEED = {
    'dataset_url': 'https://example.com/data.csv'
}

MOCK_CONFIG_NO_URL = {
    'seed': 42
}

class TestSeedVerification:
    """Tests for seed verification and application logic in code/config.py"""

    def test_set_seed_applies_to_random(self):
        """Verify set_seed applies to Python's random module"""
        set_seed(123)
        val1 = random.random()
        
        set_seed(123)
        val2 = random.random()
        
        assert val1 == val2, "Random seed application failed"

    def test_set_seed_applies_to_numpy(self):
        """Verify set_seed applies to numpy random"""
        set_seed(456)
        arr1 = np.random.rand(5)
        
        set_seed(456)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2), "Numpy random seed application failed"

    def test_verify_and_apply_seed_success(self):
        """Verify verify_and_apply_seed returns correct seed and applies it"""
        seed = verify_and_apply_seed(MOCK_CONFIG_VALID)
        assert seed == 42
        # Verify it was actually applied by checking reproducibility
        set_seed(42)
        val = random.random()
        # If we reset and get same value, it was applied correctly
        verify_and_apply_seed(MOCK_CONFIG_VALID)
        val2 = random.random()
        assert val == val2

    def test_verify_and_apply_seed_raises_on_missing(self):
        """Verify verify_and_apply_seed raises ValueError when seed is missing"""
        with pytest.raises(ValueError) as exc_info:
            verify_and_apply_seed(MOCK_CONFIG_NO_SEED)
        assert "Seed is not set" in str(exc_info.value)

    def test_log_seed_status_set(self, caplog):
        """Verify log_seed_status logs correctly when seed is set"""
        with caplog.at_level(logging.INFO):
            log_seed_status(999)
        assert any("999" in record.message for record in caplog.records)

    def test_log_seed_status_none(self, caplog):
        """Verify log_seed_status logs warning when seed is None"""
        with caplog.at_level(logging.WARNING):
            log_seed_status(None)
        assert any("not set" in record.message for record in caplog.records)

class TestConfiguration:
    """Tests for configuration loading and URL retrieval"""

    def test_get_dataset_url_success(self):
        """Verify get_dataset_url returns URL from config"""
        url = get_dataset_url(MOCK_CONFIG_VALID)
        assert url == 'https://example.com/data.csv'

    def test_get_dataset_url_raises_on_missing(self):
        """Verify get_dataset_url raises ConfigError when URL missing"""
        with pytest.raises(ConfigError) as exc_info:
            get_dataset_url(MOCK_CONFIG_NO_URL)
        assert "Dataset URL not found" in str(exc_info.value)

    def test_load_config_missing_file(self, tmp_path, caplog):
        """Verify load_config handles missing file gracefully"""
        with caplog.at_level(logging.WARNING):
            # Pass a path that definitely doesn't exist
            result = load_config(str(tmp_path / "nonexistent.yaml"))
        assert result == {}
        assert any("not found" in record.message for record in caplog.records)

    def test_ensure_directories_creates_paths(self, tmp_path):
        """Verify ensure_directories creates required directories"""
        test_dir = tmp_path / "test_subdir"
        ensure_directories([test_dir])
        assert test_dir.exists()
        assert test_dir.is_dir()
