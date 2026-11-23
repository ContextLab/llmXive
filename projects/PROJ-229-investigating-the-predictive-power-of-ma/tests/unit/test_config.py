"""
Unit tests for the configuration management module.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path

# Import the module under test
from code.config import (
    load_config,
    get_config,
    save_config_template,
    _deep_merge,
    get_api_key,
    get_random_seed,
    get_memory_limit_gb,
    get_time_limit_hours,
    DEFAULT_CONFIG_TEMPLATE,
)

class TestDeepMerge:
    def test_simple_merge(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        base = {"api": {"key": "old", "timeout": 10}}
        override = {"api": {"key": "new", "rate": 5}}
        result = _deep_merge(base, override)
        assert result == {"api": {"key": "new", "timeout": 10, "rate": 5}}

    def test_override_entire_subdict(self):
        base = {"api": {"key": "old"}}
        override = {"api": "string_value"}
        result = _deep_merge(base, override)
        assert result == {"api": "string_value"}

class TestConfigLoading:
    def test_load_config_from_file(self):
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"project": {"seed": 123}}, f)
            temp_path = f.name

        try:
            config = load_config(Path(temp_path))
            assert config["project"]["seed"] == 123
            assert config["api"]["materials_project"]["timeout"] == 30  # Default
        finally:
            os.unlink(temp_path)

    def test_load_config_merges_with_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"constraints": {"max_memory_gb": 16.0}}, f)
            temp_path = f.name

        try:
            config = load_config(Path(temp_path))
            assert config["constraints"]["max_memory_gb"] == 16.0
            assert config["project"]["name"] == "investigating-the-predictive-power-of-ma"  # Default
        finally:
            os.unlink(temp_path)

    def test_load_config_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_config(Path("non_existent_file.yaml"))

class TestConfigAccessors:
    def setup_method(self):
        # Reset cache for isolated tests
        import code.config
        code.config._config_cache = None

    def test_get_random_seed(self):
        # Load a config with a specific seed
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"project": {"seed": 999}}, f)
            temp_path = f.name

        try:
            load_config(Path(temp_path))
            assert get_random_seed() == 999
        finally:
            os.unlink(temp_path)
            import code.config
            code.config._config_cache = None

    def test_get_memory_limit_gb(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"constraints": {"max_memory_gb": 5.5}}, f)
            temp_path = f.name

        try:
            load_config(Path(temp_path))
            assert get_memory_limit_gb() == 5.5
        finally:
            os.unlink(temp_path)
            import code.config
            code.config._config_cache = None

    def test_get_time_limit_hours(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"constraints": {"max_time_hours": 2.5}}, f)
            temp_path = f.name

        try:
            load_config(Path(temp_path))
            assert get_time_limit_hours() == 2.5
        finally:
            os.unlink(temp_path)
            import code.config
            code.config._config_cache = None

    def test_get_api_key_success(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "api": {
                    "materials_project": {"api_key": "test_key_123"}
                }
            }, f)
            temp_path = f.name

        try:
            load_config(Path(temp_path))
            assert get_api_key("materials_project") == "test_key_123"
        finally:
            os.unlink(temp_path)
            import code.config
            code.config._config_cache = None

    def test_get_api_key_missing_service(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"api": {}}, f)
            temp_path = f.name

        try:
            load_config(Path(temp_path))
            with pytest.raises(KeyError):
                get_api_key("non_existent_service")
        finally:
            os.unlink(temp_path)
            import code.config
            code.config._config_cache = None

    def test_get_api_key_empty_value(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({
                "api": {
                    "materials_project": {"api_key": ""}
                }
            }, f)
            temp_path = f.name

        try:
            load_config(Path(temp_path))
            with pytest.raises(ValueError):
                get_api_key("materials_project")
        finally:
            os.unlink(temp_path)
            import code.config
            code.config._config_cache = None

class TestSaveConfigTemplate:
    def test_save_config_template_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_config.yaml"
            save_config_template(output_path)

            assert output_path.exists()
            with open(output_path, "r") as f:
                content = yaml.safe_load(f)

            assert "project" in content
            assert "api" in content
            assert content["project"]["seed"] == 42