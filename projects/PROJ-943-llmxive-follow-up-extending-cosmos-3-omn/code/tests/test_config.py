import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, set_seed, get_path, get_device, set_config, _BASE_DIR

class TestConfig:
    def test_get_config_returns_dict(self):
        """Test that get_config returns a dictionary."""
        cfg = get_config()
        assert isinstance(cfg, dict)
        assert "seed" in cfg
        assert "data" in cfg

    def test_set_seed_sets_random_seed(self):
        """Test that set_seed sets the random module seed."""
        set_seed(12345)
        val1 = random.randint(0, 1000000)
        
        set_seed(12345)
        val2 = random.randint(0, 1000000)
        
        assert val1 == val2

    def test_get_path_constructs_correct_path(self):
        """Test that get_path constructs the correct absolute path."""
        # Test data raw dir
        path = get_path("data", "raw_dir")
        expected = _BASE_DIR / "code" / "data" / "raw"
        assert path == expected
        assert path.is_absolute()

    def test_get_path_with_subpaths(self):
        """Test that get_path handles subpaths correctly."""
        path = get_path("data", "raw_dir", "subfolder", "file.txt")
        expected = _BASE_DIR / "code" / "data" / "raw" / "subfolder" / "file.txt"
        assert path == expected

    def test_get_path_invalid_key(self):
        """Test that get_path raises KeyError for invalid key."""
        with pytest.raises(KeyError):
            get_path("nonexistent_key")

    def test_get_path_invalid_subkey(self):
        """Test that get_path raises KeyError for invalid subkey."""
        with pytest.raises(KeyError):
            get_path("data", "nonexistent_subdir")

    def test_get_device_cpu_fallback(self):
        """Test that get_device returns cpu when cuda is not available or forced."""
        with patch("config.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            set_config({"device": "auto"})
            assert get_device() == "cpu"

    def test_set_config_updates_state(self):
        """Test that set_config updates the global state."""
        original_seed = get_config()["seed"]
        set_config({"seed": 999})
        assert get_config()["seed"] == 999
        # Reset
        set_config({"seed": original_seed})

    def test_set_seed_with_numpy(self):
        """Test that set_seed also seeds numpy if available."""
        try:
            import numpy as np
            set_seed(42)
            val1 = np.random.randint(0, 10000)
            set_seed(42)
            val2 = np.random.randint(0, 10000)
            assert val1 == val2
        except ImportError:
            pytest.skip("numpy not available")

    def test_set_seed_with_torch(self):
        """Test that set_seed also seeds torch if available."""
        try:
            import torch
            set_seed(42)
            val1 = torch.randint(0, 10000, (1,)).item()
            set_seed(42)
            val2 = torch.randint(0, 10000, (1,)).item()
            assert val1 == val2
        except ImportError:
            pytest.skip("torch not available")