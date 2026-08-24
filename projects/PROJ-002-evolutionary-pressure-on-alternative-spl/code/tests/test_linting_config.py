import os
import subprocess
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), ".flake8 configuration file is missing"
    assert flake8_path.is_file(), ".flake8 is not a file"

def test_black_config_exists():
    """Verify Black configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml is missing"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length" in content, "Black line-length setting missing"

def test_pre_commit_config_exists():
    """Verify pre-commit configuration file exists."""
    precommit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert precommit_path.exists(), ".pre-commit-config.yaml is missing"
    assert precommit_path.is_file(), ".pre-commit-config.yaml is not a file"

def test_requirements_includes_linting_tools():
    """Verify linting tools are listed in requirements.txt."""
    requirements_path = PROJECT_ROOT / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt is missing"
    
    content = requirements_path.read_text().lower()
    assert "flake8" in content, "flake8 not in requirements.txt"
    assert "black" in content, "black not in requirements.txt"
    assert "pre-commit" in content, "pre-commit not in requirements.txt"

def test_pyproject_toml_structure():
    """Verify pyproject.toml has required sections."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    
    required_sections = [
        "[build-system]",
        "[project]",
        "[tool.black]",
        "[tool.pytest.ini_options]"
    ]
    
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"

def test_pre_commit_hooks_valid():
    """Verify pre-commit configuration is valid YAML and references valid repos."""
    precommit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    
    try:
        import yaml
        with open(precommit_path) as f:
            config = yaml.safe_load(f)
        
        assert "repos" in config, "pre-commit config missing 'repos' key"
        assert isinstance(config["repos"], list), "'repos' must be a list"
        
        for repo in config["repos"]:
            assert "repo" in repo, "Repository entry missing 'repo' key"
            assert "hooks" in repo, f"Repository {repo.get('repo')} missing 'hooks' key"
    except ImportError:
        pytest.skip("PyYAML not installed")

def test_black_config_settings():
    """Verify Black has specific configuration settings."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    
    assert "line-length = 88" in content, "Black line-length should be 88"
    assert "target-version" in content, "Black target-version setting missing"

def test_flake8_config_settings():
    """Verify flake8 has specific configuration settings."""
    flake8_path = PROJECT_ROOT / ".flake8"
    content = flake8_path.read_text()
    
    assert "max-line-length" in content, "flake8 max-line-length setting missing"
    assert "extend-ignore" in content, "flake8 extend-ignore setting missing"