import os
import pytest
from utils.seed_manager import initialize_reproducibility
from config import get_seed, get_version_hash, get_config_summary

class TestConfigSeedIntegration:
    def test_seed_persistence_across_modules(self):
        """Verify seed set in seed_manager is visible in config."""
        seed_val = 54321
        initialize_reproducibility(seed_val)
        
        assert get_seed() == seed_val
        assert get_version_hash() is not None
        assert len(get_version_hash()) > 0

    def test_version_hash_changes_with_seed(self):
        """Verify that different seeds produce different version hashes."""
        initialize_reproducibility(111)
        hash1 = get_version_hash()
        
        initialize_reproducibility(222)
        hash2 = get_version_hash()
        
        assert hash1 != hash2, "Version hash should change with seed"

    def test_config_summary_includes_seed(self):
        """Verify config summary contains the current seed."""
        seed_val = 77777
        initialize_reproducibility(seed_val)
        
        summary = get_config_summary()
        assert summary["seed"] == seed_val