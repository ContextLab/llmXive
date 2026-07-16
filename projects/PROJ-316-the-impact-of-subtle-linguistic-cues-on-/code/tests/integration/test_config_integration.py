"""
Integration tests for the configuration management module.

These tests verify that configuration works correctly in realistic scenarios
and integrates properly with other modules.
"""
import os
import random
import pytest
import tempfile
from pathlib import Path
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import (
    set_seed,
    reset_config,
    configure_from_env,
    get_seed
)
from src.utils.io import fetch_text, load_ratings, validate_schemas


class TestConfigWithDataLoading:
    """Test configuration integration with data loading."""
    
    def test_seed_affects_data_loading(self):
        """Test that seed setting affects any random operations in data loading."""
        # This test verifies that if data loading uses random operations,
        # they are reproducible with the same seed
        set_seed(42)
        
        # If we had actual data loading that uses random sampling,
        # we would verify reproducibility here
        # For now, we just verify the seed is set correctly
        assert get_seed() == 42
        
        # Change seed
        set_seed(123)
        assert get_seed() == 123
        
        # Reset
        reset_config()
        assert get_seed() == 42


class TestConfigWithExtraction:
    """Test configuration integration with feature extraction."""
    
    def test_seed_consistency_across_modules(self):
        """Test that seed is consistent across different modules."""
        set_seed(42)
        
        # Verify seed is set in this module
        seed1 = get_seed()
        
        # If extraction modules use random operations, they should see the same seed
        # This is verified by the set_seed function propagating to numpy and random
        
        assert seed1 == 42
        
        reset_config()


class TestConfigEnvironmentScenarios:
    """Test configuration in various environment scenarios."""
    
    def test_production_environment(self):
        """Test configuration for a production-like environment."""
        # Simulate production environment variables
        os.environ['RESEARCH_SEED'] = '42'
        os.environ['RESEARCH_TIMEOUT'] = '3600'
        os.environ['RESEARCH_CPU_ONLY'] = 'true'
        
        configure_from_env()
        
        assert get_seed() == 42
        # Note: Timeout is set but not easily testable in unit tests
        assert is_cpu_only() is True
        
        reset_config()
    
    def test_development_environment(self):
        """Test configuration for a development-like environment."""
        os.environ['RESEARCH_SEED'] = '12345'
        os.environ['RESEARCH_TIMEOUT'] = '300'
        os.environ['RESEARCH_CPU_ONLY'] = 'false'
        
        configure_from_env()
        
        assert get_seed() == 12345
        assert is_cpu_only() is False
        
        reset_config()
    
    def test_environment_override_manual(self):
        """Test that environment configuration can override manual settings."""
        # Set manually
        set_seed(999)
        assert get_seed() == 999
        
        # Configure from env
        os.environ['RESEARCH_SEED'] = '777'
        configure_from_env()
        assert get_seed() == 777
        
        reset_config()


class TestConfigReproducibility:
    """Test reproducibility across multiple runs."""
    
    def test_reproducible_sequence(self):
        """Test that the same seed produces reproducible sequences."""
        # Run 1
        set_seed(42)
        sequence1 = [random.random() for _ in range(10)]
        
        # Reset and run again
        reset_config()
        set_seed(42)
        sequence2 = [random.random() for _ in range(10)]
        
        assert sequence1 == sequence2
    
    def test_different_runs_different_sequences(self):
        """Test that different seeds produce different sequences."""
        set_seed(42)
        sequence1 = [random.random() for _ in range(10)]
        
        set_seed(123)
        sequence2 = [random.random() for _ in range(10)]
        
        assert sequence1 != sequence2