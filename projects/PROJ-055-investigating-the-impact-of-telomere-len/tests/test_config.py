import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import load_env_config, validate_config, init_config, ConfigError, set_random_seed

class TestConfig:
    def test_load_env_config_from_file(self):
        """Test loading configuration from a .env file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write("RANDOM_SEED=123\n")
            f.write("DRYAD_API_KEY=test_key\n")
            f.write("# Comment line\n")
            f.write("ANAGE_API_KEY=\n")
            temp_path = Path(f.name)

        try:
            config = load_env_config(temp_path)
            assert config['RANDOM_SEED'] == '123'
            assert config['DRYAD_API_KEY'] == 'test_key'
            assert 'ANAGE_API_KEY' in config
        finally:
            os.unlink(temp_path)

    def test_validate_config_missing_seed(self):
        """Test that validation fails if RANDOM_SEED is missing."""
        config = {'DRYAD_API_KEY': 'test'}
        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "RANDOM_SEED" in str(exc_info.value)

    def test_validate_config_invalid_seed(self):
        """Test that validation fails if RANDOM_SEED is not an integer."""
        config = {'RANDOM_SEED': 'not_a_number'}
        with pytest.raises(ConfigError) as exc_info:
            validate_config(config)
        assert "integer" in str(exc_info.value)

    def test_validate_config_success(self):
        """Test successful validation with valid config."""
        config = {'RANDOM_SEED': '42', 'DRYAD_API_KEY': 'key'}
        # Should not raise
        validate_config(config)

    def test_set_random_seed(self):
        """Test that set_random_seed correctly sets the seed."""
        seed_val = 999
        result = set_random_seed(seed_val)
        assert result == seed_val
        
        # Verify randomness is deterministic
        import random
        val1 = random.random()
        
        set_random_seed(seed_val)
        val2 = random.random()
        
        assert val1 == val2

    def test_init_config_integration(self):
        """Test the full initialization flow with a temporary .env file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
            f.write("RANDOM_SEED=555\n")
            temp_path = Path(f.name)

        try:
            config = init_config(temp_path)
            assert config['RANDOM_SEED'] == '555'
        finally:
            os.unlink(temp_path)
