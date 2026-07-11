"""
Unit tests for config.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import (
    load_config,
    set_seed,
    get_seed,
    load_schema,
    validate_against_schema,
    get_contract_paths,
    save_config,
    reset_config,
    DEFAULT_CONFIG,
    CONFIG_FILE
)

class TestConfigLoading:
    def test_load_config_returns_default(self):
        """Test that load_config returns default values when no file exists."""
        reset_config()
        # Create a temporary directory to avoid using real config
        original_config = CONFIG_FILE
        try:
            # Temporarily move config file if it exists
            if original_config.exists():
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(original_config.read_bytes())
                    tmp_path = Path(tmp.name)
                os.rename(original_config, tmp_path)
            
            cfg = load_config()
            assert cfg == DEFAULT_CONFIG
            
            # Restore if it was moved
            if tmp_path.exists():
                os.rename(tmp_path, original_config)
                reset_config()
        except Exception:
            reset_config()
            raise

    def test_load_config_merges_with_file(self):
        """Test that load_config merges file values with defaults."""
        reset_config()
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"random_seed": 123, "author_count": 15}, f)
            temp_path = Path(f.name)
        
        try:
            cfg = load_config(temp_path)
            assert cfg["random_seed"] == 123
            assert cfg["author_count"] == 15
            # Default values should remain
            assert cfg["ngram_orders"] == [4, 5, 6]
        finally:
            temp_path.unlink()
            reset_config()

class TestSeedManagement:
    def test_set_seed_returns_value(self):
        """Test that set_seed returns the seed value."""
        reset_config()
        seed = set_seed(999)
        assert seed == 999
        reset_config()

    def test_get_seed_returns_config_value(self):
        """Test that get_seed returns the configured seed."""
        reset_config()
        cfg = load_config()
        expected = cfg.get("random_seed", 42)
        assert get_seed() == expected
        reset_config()

    def test_seed_determinism(self):
        """Test that setting the same seed produces same results."""
        reset_config()
        import random
        
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2
        reset_config()

class TestSchemaLoading:
    def test_load_schema_raises_on_missing(self):
        """Test that load_schema raises FileNotFoundError for missing schema."""
        with pytest.raises(FileNotFoundError):
            load_schema("nonexistent_schema")

    def test_get_contract_paths(self):
        """Test that get_contract_paths returns list of schema files."""
        paths = get_contract_paths()
        # Should return a list (may be empty if no schemas exist)
        assert isinstance(paths, list)
        # All paths should be .json files
        for p in paths:
            assert p.suffix == ".json"

class TestConfigSave:
    def test_save_config_creates_file(self):
        """Test that save_config creates a file with correct content."""
        reset_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            test_config = {"random_seed": 555, "test_key": "test_value"}
            save_config(test_config, temp_path)
            
            assert temp_path.exists()
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["random_seed"] == 555
            assert loaded["test_key"] == "test_value"
        finally:
            temp_path.unlink()
            reset_config()