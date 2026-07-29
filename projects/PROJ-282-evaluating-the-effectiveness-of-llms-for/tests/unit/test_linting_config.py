import pytest
import os
import toml

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml must exist at project root"

def test_black_config_exists():
    """Verify Black configuration is present in pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "black" in config["tool"], "black configuration missing in pyproject.toml"
    
    # Verify standard settings
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "line-length must be configured for black"
    assert black_config["line-length"] == 88, "line-length should be 88"

def test_ruff_config_exists():
    """Verify Ruff configuration is present in pyproject.toml."""
    with open("pyproject.toml", "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "tool section missing in pyproject.toml"
    assert "ruff" in config["tool"], "ruff configuration missing in pyproject.toml"
    
    # Verify standard settings
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "line-length must be configured for ruff"
    assert ruff_config["line-length"] == 88, "line-length should be 88"

def test_precommit_config_exists():
    """Verify .pre-commit-config.yaml exists and contains black and ruff."""
    assert os.path.exists(".pre-commit-config.yaml"), ".pre-commit-config.yaml must exist"
    
    import yaml
    with open(".pre-commit-config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    repos = config.get("repos", [])
    hook_ids = []
    for repo in repos:
        for hook in repo.get("hooks", []):
            hook_ids.append(hook.get("id"))
    
    assert "black" in hook_ids, "black hook must be in .pre-commit-config.yaml"
    assert "ruff" in hook_ids, "ruff hook must be in .pre-commit-config.yaml"