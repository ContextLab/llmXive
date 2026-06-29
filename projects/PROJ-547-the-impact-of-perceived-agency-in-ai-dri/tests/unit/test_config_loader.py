"""
Unit tests for ``code.config.config_loader``.
"""

import tempfile
from pathlib import Path

import pytest

# Import the module under test
from code.config.config_loader import load_config, ConfigLoader


SAMPLE_YAML = """
database:
  host: localhost
  port: 5432
  name: test_db
logging:
  level: INFO
  file: app.log
"""


def write_temp_yaml(content: str) -> Path:
    """
    Helper that writes *content* to a temporary file and returns its Path.
    """
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml", mode="w", encoding="utf-8")
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return Path(tmp.name)


def test_load_config_returns_expected_keys():
    yaml_path = write_temp_yaml(SAMPLE_YAML)

    cfg = load_config(yaml_path)

    # Expected top‑level keys
    assert set(cfg.keys()) == {"database", "logging"}
    # Nested checks
    assert cfg["database"]["host"] == "localhost"
    assert cfg["database"]["port"] == 5432
    assert cfg["logging"]["level"] == "INFO"


def test_config_loader_class_uses_base_dir():
    # Create a temporary directory to act as a mock ``configs`` folder
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)

        # Write a sample yaml inside this temporary configs directory
        yaml_file = tmp_dir_path / "my_config.yaml"
        yaml_file.write_text(SAMPLE_YAML, encoding="utf-8")

        loader = ConfigLoader(base_dir=tmp_dir_path)
        cfg = loader.load("my_config.yaml")

        assert "database" in cfg
        assert cfg["database"]["name"] == "test_db"


def test_load_config_raises_file_not_found():
    non_existent = Path("does_not_exist.yaml")
    with pytest.raises(FileNotFoundError):
        load_config(non_existent)


def test_load_config_invalid_yaml():
    # Write malformed YAML
    bad_yaml = "::: not a yaml :::"
    bad_path = write_temp_yaml(bad_yaml)

    with pytest.raises(yaml.YAMLError):
        load_config(bad_path)