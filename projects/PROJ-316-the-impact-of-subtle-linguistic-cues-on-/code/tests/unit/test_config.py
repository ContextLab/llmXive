"""
Unit tests for the configuration management module.

Tests verify:
- Seed setting and reproducibility
- Timeout enforcement
- CPU-only mode configuration
- Environment variable configuration
"""
import os
import random
import pytest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import (
    Config,
    get_seed,
    set_seed,
    get_timeout_seconds,
    is_cpu_only,
    enforce_cpu_only,
    reset_config,
    configure_from_env
)


class TestSeedManagement:
    """Tests for random seed management."""
    
    def test_default_seed(self):
        """Test that the default seed is 42."""
        reset_config()
        assert get_seed() == 42
    
    def test_set_seed(self):
        """Test setting a custom seed."""
        set_seed(123)
        assert get_seed() == 123
    
    def test_seed_reproducibility(self):
        """Test that setting the same seed produces the same random sequence."""
        set_seed(42)
        sequence1 = [random.random() for _ in range(5)]
        
        set_seed(42)
        sequence2 = [random.random() for _ in range(5)]
        
        assert sequence1 == sequence2
    
    def test_different_seed_different_sequence(self):
        """Test that different seeds produce different sequences."""
        set_seed(42)
        sequence1 = [random.random() for _ in range(5)]
        
        set_seed(123)
        sequence2 = [random.random() for _ in range(5)]
        
        assert sequence1 != sequence2
    
    def test_numpy_seed_propagation(self):
        """Test that seed is propagated to numpy if available."""
        try:
            import numpy as np
            set_seed(42)
            val1 = np.random.random()
            
            set_seed(42)
            val2 = np.random.random()
            
            assert val1 == val2
        except ImportError:
            pytest.skip("numpy not available")


class TestTimeoutManagement:
    """Tests for timeout enforcement."""
    
    def test_default_timeout(self):
        """Test that the default timeout is None."""
        reset_config()
        assert get_timeout_seconds() is None
    
    def test_set_timeout(self):
        """Test setting a timeout."""
        # Note: We can't easily test the actual timeout enforcement without
        # blocking the test, so we just verify the value is set
        config = Config()
        config.timeout_seconds = 30
        assert config.timeout_seconds == 30
    
    def test_timeout_none(self):
        """Test setting timeout to None."""
        config = Config()
        config.timeout_seconds = None
        assert config.timeout_seconds is None


class TestCPUOnlyMode:
    """Tests for CPU-only mode."""
    
    def test_default_cpu_only(self):
        """Test that CPU-only mode is enabled by default."""
        reset_config()
        assert is_cpu_only() is True
    
    def test_set_cpu_only(self):
        """Test enabling/disabling CPU-only mode."""
        config = Config()
        config.cpu_only = False
        assert config.cpu_only is False
        
        config.cpu_only = True
        assert config.cpu_only is True
    
    def test_enforce_cpu_only(self):
        """Test the enforce_cpu_only function."""
        config = Config()
        config.cpu_only = False
        enforce_cpu_only()
        assert is_cpu_only() is True


class TestConfigReset:
    """Tests for configuration reset."""
    
    def test_reset_to_defaults(self):
        """Test that reset_config restores defaults."""
        set_seed(999)
        config = Config()
        config.timeout_seconds = 120
        config.cpu_only = False
        
        reset_config()
        
        assert get_seed() == 42
        assert get_timeout_seconds() is None
        assert is_cpu_only() is True


class TestEnvironmentConfiguration:
    """Tests for environment variable configuration."""
    
    def setup_method(self):
        """Clean environment before each test."""
        self.original_env = {
            'RESEARCH_SEED': os.environ.get('RESEARCH_SEED'),
            'RESEARCH_TIMEOUT': os.environ.get('RESEARCH_TIMEOUT'),
            'RESEARCH_CPU_ONLY': os.environ.get('RESEARCH_CPU_ONLY')
        }
    
    def teardown_method(self):
        """Restore original environment after each test."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        reset_config()
    
    def test_configure_from_env_seed(self):
        """Test configuring seed from environment."""
        os.environ['RESEARCH_SEED'] = '777'
        configure_from_env()
        assert get_seed() == 777
    
    def test_configure_from_env_timeout(self):
        """Test configuring timeout from environment."""
        os.environ['RESEARCH_TIMEOUT'] = '180'
        configure_from_env()
        assert get_timeout_seconds() == 180
    
    def test_configure_from_env_cpu_only_true(self):
        """Test configuring CPU-only from environment (true)."""
        os.environ['RESEARCH_CPU_ONLY'] = 'true'
        configure_from_env()
        assert is_cpu_only() is True
    
    def test_configure_from_env_cpu_only_false(self):
        """Test configuring CPU-only from environment (false)."""
        os.environ['RESEARCH_CPU_ONLY'] = 'false'
        configure_from_env()
        assert is_cpu_only() is False
    
    def test_configure_from_env_invalid_seed(self):
        """Test that invalid seed defaults to 42."""
        os.environ['RESEARCH_SEED'] = 'invalid'
        configure_from_env()
        assert get_seed() == 42
    
    def test_configure_from_env_invalid_timeout(self):
        """Test that invalid timeout is treated as None."""
        os.environ['RESEARCH_TIMEOUT'] = 'invalid'
        configure_from_env()
        assert get_timeout_seconds() is None
    
    def test_configure_from_env_defaults(self):
        """Test that missing env vars use defaults."""
        # Ensure env vars are not set
        for key in ['RESEARCH_SEED', 'RESEARCH_TIMEOUT', 'RESEARCH_CPU_ONLY']:
            os.environ.pop(key, None)
        
        configure_from_env()
        assert get_seed() == 42
        assert get_timeout_seconds() is None
        assert is_cpu_only() is True


class TestConfigIntegration:
    """Integration tests for configuration module."""
    
    def test_full_workflow(self):
        """Test a complete configuration workflow."""
        # Reset to defaults
        reset_config()
        assert get_seed() == 42
        
        # Configure from environment
        os.environ['RESEARCH_SEED'] = '555'
        configure_from_env()
        assert get_seed() == 555
        
        # Manual override
        set_seed(333)
        assert get_seed() == 333
        
        # Reset again
        reset_config()
        assert get_seed() == 42
