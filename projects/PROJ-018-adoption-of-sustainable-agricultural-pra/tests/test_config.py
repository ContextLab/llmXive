import os
import random
import tempfile
from pathlib import Path
import yaml

import pytest

# Import from the project code
from config import (
    Config,
    ConfigError,
    load_config_from_yaml,
    get_config,
    set_random_seed,
    get_config_path,
    get_data_path,
)


class TestConfigClass:
    def test_init_empty(self):
        config = Config()
        assert config.get("key") is None

    def test_init_with_dict(self):
        data = {"seed": 42, "path": "/tmp"}
        config = Config(data)
        assert config.get("seed") == 42
        assert config.get("path") == "/tmp"
        assert config.get("missing", "default") == "default"

    def test_get_with_default(self):
        config = Config({"a": 1})
        assert config.get("a", 99) == 1
        assert config.get("b", 99) == 99

    def test_contains(self):
        config = Config({"x": 1})
        assert "x" in config
        assert "y" not in config

    def test_keys_and_items(self):
        data = {"a": 1, "b": 2}
        config = Config(data)
        assert set(config.keys()) == {"a", "b"}
        assert set(dict(config.items()).keys()) == {"a", "b"}

    def test_to_dict(self):
        data = {"k": "v"}
        config = Config(data)
        d = config.to_dict()
        assert d == data
        d["k"] = "modified"
        assert config.get("k") == "v"  # Original unchanged

    def test_tolerant_fallback(self):
        config = Config({})
        # Should not raise AttributeError
        result = config.info("test")
        assert result is None
        result = config.debug(1, 2, a=3)
        assert result is None


class TestLoadConfigFromYaml:
    def test_load_valid_yaml(self, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        data = {"seed": 123, "path": str(tmp_path)}
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)

        config = load_config_from_yaml(yaml_file)
        assert config.get("seed") == 123
        assert config.get("path") == str(tmp_path)

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(ConfigError):
            load_config_from_yaml(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        yaml_file = tmp_path / "bad.yaml"
        with open(yaml_file, "w") as f:
            f.write("key: [unclosed")
        with pytest.raises(ConfigError):
            load_config_from_yaml(yaml_file)

    def test_load_null_yaml(self, tmp_path):
        yaml_file = tmp_path / "null.yaml"
        with open(yaml_file, "w") as f:
            f.write("null")
        config = load_config_from_yaml(yaml_file)
        assert config.to_dict() == {}


class TestGetConfig:
    def test_get_full_config(self, monkeypatch, tmp_path):
        # Create a temp config file
        yaml_file = tmp_path / "config.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump({"seed": 999}, f)

        # Monkeypatch the search path
        original_get_config_path = get_config_path
        # We can't easily monkeypatch the internal list in get_config,
        # so we place the file where it expects it relative to cwd
        # or rely on the fact that get_config checks current dir first.
        monkeypatch.chdir(tmp_path)

        # Reset global config
        import config as config_module
        config_module._global_config = None

        cfg = get_config()
        assert isinstance(cfg, Config)
        assert cfg.get("seed") == 999

    def test_get_value(self, monkeypatch, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump({"seed": 888}, f)
        monkeypatch.chdir(tmp_path)

        import config as config_module
        config_module._global_config = None

        val = get_config("seed")
        assert val == 888

    def test_get_value_with_default(self, monkeypatch, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump({}, f)
        monkeypatch.chdir(tmp_path)

        import config as config_module
        config_module._global_config = None

        val = get_config("missing_key", "default_val")
        assert val == "default_val"


class TestSetRandomSeed:
    def test_sets_python_seed(self):
        set_random_seed(42)
        r1 = random.random()
        set_random_seed(42)
        r2 = random.random()
        assert r1 == r2

    def test_sets_numpy_seed(self):
        try:
            import numpy as np
            set_random_seed(123)
            a1 = np.random.rand()
            set_random_seed(123)
            a2 = np.random.rand()
            assert a1 == a2
        except ImportError:
            pytest.skip("NumPy not available")


class TestPathHelpers:
    def test_get_config_path(self):
        p = get_config_path()
        assert str(p) == "config.yaml"

    def test_get_data_path(self):
        p = get_data_path()
        assert str(p) == "data"
