"""
Unit tests to verify project structure and schema existence.
"""
import os
import yaml
from pathlib import Path

def test_directories_exist():
    """Verify that required directories exist."""
    base_dir = Path(__file__).parent.parent.parent
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/logs",
        "contracts",
        "tests",
    ]
    for d in required_dirs:
        assert (base_dir / d).exists(), f"Directory {d} does not exist"

def test_schemas_exist():
    """Verify that schema files exist and are valid YAML."""
    base_dir = Path(__file__).parent.parent.parent
    contracts_dir = base_dir / "contracts"
    schema_files = ["dataset.schema.yaml", "output.schema.yaml"]
    for s in schema_files:
        path = contracts_dir / s
        assert path.exists(), f"Schema file {s} does not exist"
        with open(path) as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError:
                assert False, f"Schema file {s} is not valid YAML"

def test_init_files_exist():
    """Verify that __init__.py files exist in key packages."""
    base_dir = Path(__file__).parent.parent.parent
    init_files = [
        "code/__init__.py",
        "data/__init__.py",
        "contracts/__init__.py",
        "tests/__init__.py",
    ]
    for f in init_files:
        assert (base_dir / f).exists(), f"Init file {f} does not exist"
