"""
Unit test to verify that linting and formatting configurations are valid.
This test ensures that the project's pyproject.toml and .pre-commit-config.yaml
are syntactically valid and contain the expected tool configurations.
"""
import os
import toml
import yaml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
PYPROJECT_PATH = os.path.join(PROJECT_ROOT, "pyproject.toml")
PRE_COMMIT_PATH = os.path.join(PROJECT_ROOT, ".pre-commit-config.yaml")

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists."""
    assert os.path.exists(PYPROJECT_PATH), "pyproject.toml must exist"

def test_pyproject_toml_valid():
    """Verify pyproject.toml is valid TOML."""
    with open(PYPROJECT_PATH, "r") as f:
        try:
            data = toml.load(f)
            assert "tool" in data
            assert "black" in data["tool"], "Black configuration missing in pyproject.toml"
            assert "ruff" in data["tool"], "Ruff configuration missing in pyproject.toml"
        except Exception as e:
            pytest.fail(f"pyproject.toml is invalid TOML: {e}")

def test_pre_commit_config_exists():
    """Verify .pre-commit-config.yaml exists."""
    assert os.path.exists(PRE_COMMIT_PATH), ".pre-commit-config.yaml must exist"

def test_pre_commit_config_valid():
    """Verify .pre-commit-config.yaml is valid YAML and contains required hooks."""
    with open(PRE_COMMIT_PATH, "r") as f:
        try:
            data = yaml.safe_load(f)
            assert "repos" in data, "repos key missing in .pre-commit-config.yaml"
            
            hook_names = set()
            for repo in data["repos"]:
                for hook in repo.get("hooks", []):
                    hook_names.add(hook["id"])
            
            assert "black" in hook_names, "Black hook missing in .pre-commit-config.yaml"
            assert "ruff" in hook_names, "Ruff hook missing in .pre-commit-config.yaml"
        except Exception as e:
            pytest.fail(f".pre-commit-config.yaml is invalid YAML: {e}")