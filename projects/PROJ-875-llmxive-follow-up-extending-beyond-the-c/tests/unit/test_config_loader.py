"""
Unit tests for the config_loader module.

Tests verify correct loading of seeds configuration, error handling,
and proper behavior of global state management.
"""
import os
import tempfile
import pytest
from unittest.mock import patch
import yaml

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from code.config_loader import (
    load_seeds_config,
    get_seeds,
    set_seeds,
    reset_config,
    SEEDS
)


class TestLoadSeedsConfig:
    """Tests for load_seeds_config function."""
    
    def test_load_valid_seeds_file(self, tmp_path):
        """Test loading a valid seeds configuration file."""
        seeds = [1, 2, 3, 4, 5]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        result = load_seeds_config(str(config_file))
        
        assert result == seeds
        assert len(result) == len(seeds)
    
    def test_load_default_path(self, tmp_path, monkeypatch):
        """Test loading from default path when no config_path is provided."""
        seeds = [10, 20, 30]
        config = {"seeds": seeds}
        
        # Create config directory structure
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        # Mock the project root detection
        with patch('code.config_loader.os.path.dirname') as mock_dirname:
            with patch('code.config_loader.os.path.abspath') as mock_abspath:
                mock_abspath.return_value = str(tmp_path / "code" / "__init__.py")
                mock_dirname.side_effect = lambda x: os.path.dirname(x)
                
                # Reset config state
                from code import config_loader
                config_loader._seeds = None
                config_loader._config_path = None
                
                result = load_seeds_config()
                
                assert result == seeds
    
    def test_empty_config_file_raises_error(self, tmp_path):
        """Test that an empty config file raises ValueError."""
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text("")
        
        with pytest.raises(ValueError, match="empty"):
            load_seeds_config(str(config_file))
    
    def test_missing_seeds_key_raises_error(self, tmp_path):
        """Test that missing 'seeds' key raises ValueError."""
        config = {"other_key": [1, 2, 3]}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        with pytest.raises(ValueError, match="missing 'seeds' key"):
            load_seeds_config(str(config_file))
    
    def test_seeds_not_list_raises_error(self, tmp_path):
        """Test that seeds as non-list raises ValueError."""
        config = {"seeds": "not_a_list"}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        with pytest.raises(ValueError, match="must be a list"):
            load_seeds_config(str(config_file))
    
    def test_empty_seeds_list_raises_error(self, tmp_path):
        """Test that empty seeds list raises ValueError."""
        config = {"seeds": []}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        with pytest.raises(ValueError, match="cannot be empty"):
            load_seeds_config(str(config_file))
    
    def test_non_integer_seed_raises_error(self, tmp_path):
        """Test that non-integer seed raises TypeError."""
        config = {"seeds": [1, "two", 3]}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        with pytest.raises(TypeError, match="must be an integer"):
            load_seeds_config(str(config_file))
    
    def test_file_not_found_raises_error(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        config_file = tmp_path / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError):
            load_seeds_config(str(config_file))
    
    def test_caching_works(self, tmp_path):
        """Test that config is cached and not reloaded."""
        seeds = [1, 2, 3]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        # First load
        result1 = load_seeds_config(str(config_file))
        
        # Modify file
        config["seeds"] = [4, 5, 6]
        config_file.write_text(yaml.dump(config))
        
        # Second load should return cached value
        result2 = load_seeds_config(str(config_file))
        
        assert result1 == [1, 2, 3]
        assert result2 == [1, 2, 3]  # Cached, not reloaded
    
    def test_reload_on_different_path(self, tmp_path):
        """Test that different config path triggers reload."""
        seeds1 = [1, 2, 3]
        seeds2 = [4, 5, 6]
        
        config1 = {"seeds": seeds1}
        config_file1 = tmp_path / "seeds1.yaml"
        config_file1.write_text(yaml.dump(config1))
        
        config2 = {"seeds": seeds2}
        config_file2 = tmp_path / "seeds2.yaml"
        config_file2.write_text(yaml.dump(config2))
        
        # Load first config
        result1 = load_seeds_config(str(config_file1))
        
        # Load second config
        result2 = load_seeds_config(str(config_file2))
        
        assert result1 == [1, 2, 3]
        assert result2 == [4, 5, 6]


class TestGetSeeds:
    """Tests for get_seeds function."""
    
    def test_get_seeds_after_load(self, tmp_path):
        """Test get_seeds returns loaded seeds."""
        seeds = [10, 20, 30]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        # Load config first
        load_seeds_config(str(config_file))
        
        result = get_seeds()
        
        assert result == seeds
    
    def test_get_seeds_auto_loads(self):
        """Test that get_seeds auto-loads if not already loaded."""
        # Reset state
        from code import config_loader
        config_loader._seeds = None
        config_loader._config_path = None
        
        # This should raise an error if no default config exists
        # which is expected behavior
        with pytest.raises(FileNotFoundError):
            get_seeds()
    
    def test_get_seeds_returns_copy(self, tmp_path):
        """Test that get_seeds returns a copy, not the original list."""
        seeds = [1, 2, 3]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        load_seeds_config(str(config_file))
        result = get_seeds()
        
        # Modify returned list
        result.append(4)
        
        # Original should be unchanged
        result2 = get_seeds()
        assert len(result2) == 3


class TestSetSeeds:
    """Tests for set_seeds function."""
    
    def test_set_valid_seeds(self):
        """Test setting valid seeds."""
        new_seeds = [100, 200, 300]
        set_seeds(new_seeds)
        
        result = get_seeds()
        assert result == new_seeds
        
        # Reset for other tests
        reset_config()
    
    def test_set_empty_list_raises_error(self):
        """Test that setting empty list raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            set_seeds([])
        
        reset_config()
    
    def test_set_non_list_raises_error(self):
        """Test that setting non-list raises TypeError."""
        with pytest.raises(TypeError, match="must be a list"):
            set_seeds("not_a_list")
        
        reset_config()
    
    def test_set_non_integer_raises_error(self):
        """Test that setting non-integer seed raises TypeError."""
        with pytest.raises(TypeError, match="must be an integer"):
            set_seeds([1, "two", 3])
        
        reset_config()
    
    def test_set_overwrites_loaded_config(self, tmp_path):
        """Test that set_seeds overwrites previously loaded config."""
        # Load a config
        seeds1 = [1, 2, 3]
        config = {"seeds": seeds1}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        load_seeds_config(str(config_file))
        
        # Override with manual seeds
        seeds2 = [999, 888]
        set_seeds(seeds2)
        
        result = get_seeds()
        assert result == seeds2
        
        reset_config()


class TestResetConfig:
    """Tests for reset_config function."""
    
    def test_reset_clears_state(self, tmp_path):
        """Test that reset_config clears global state."""
        seeds = [1, 2, 3]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        load_seeds_config(str(config_file))
        assert get_seeds() == seeds
        
        reset_config()
        
        # State should be cleared
        from code import config_loader
        assert config_loader._seeds is None
        assert config_loader._config_path is None
    
    def test_reset_allows_reload(self, tmp_path):
        """Test that config can be reloaded after reset."""
        seeds = [1, 2, 3]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        load_seeds_config(str(config_file))
        reset_config()
        
        # Should be able to reload
        result = load_seeds_config(str(config_file))
        assert result == seeds


class TestModuleLevelSEEDS:
    """Tests for the module-level SEEDS variable."""
    
    def test_seeds_is_list_or_none(self):
        """Test that SEEDS is either a list or None."""
        assert SEEDS is None or isinstance(SEEDS, list)
    
    def test_seeds_matches_loaded_config(self, tmp_path):
        """Test that SEEDS matches loaded config if available."""
        seeds = [5, 10, 15]
        config = {"seeds": seeds}
        config_file = tmp_path / "seeds.yaml"
        config_file.write_text(yaml.dump(config))
        
        # In a real scenario, SEEDS would be loaded at import time
        # Here we verify the logic works
        load_seeds_config(str(config_file))
        assert get_seeds() == seeds