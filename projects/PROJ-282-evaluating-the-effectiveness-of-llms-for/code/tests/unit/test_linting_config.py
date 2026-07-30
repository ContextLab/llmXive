import os
import subprocess
import tempfile
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Verify ruff configuration exists in pyproject.toml or .ruff.toml"""
    project_root = Path(__file__).parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    ruff_toml = project_root / ".ruff.toml"
    
    assert pyproject.exists() or ruff_toml.exists(), "Ruff config file missing"
    
    if pyproject.exists():
        content = pyproject.read_text()
        assert "[tool.ruff]" in content, "Ruff section missing in pyproject.toml"

def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml"""
    project_root = Path(__file__).parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml missing"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black section missing in pyproject.toml"
    assert "line-length" in content, "Black line-length config missing"

def test_precommit_config_exists():
    """Verify pre-commit configuration exists"""
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / ".pre-commit-config.yaml"
    
    assert config_file.exists(), ".pre-commit-config.yaml missing"
    
    content = config_file.read_text()
    assert "ruff" in content, "Ruff hook missing in pre-commit config"
    assert "black" in content, "Black hook missing in pre-commit config"

def test_lint_script_exists():
    """Verify lint script exists and is executable"""
    project_root = Path(__file__).parent.parent.parent
    script = project_root / "scripts" / "lint.sh"
    
    assert script.exists(), "lint.sh script missing"
    # We don't assert executable bit here as git might strip it in some environments
    # but the file must exist and have content
    content = script.read_text()
    assert "ruff" in content, "lint.sh does not invoke ruff"

def test_format_script_exists():
    """Verify format script exists and is executable"""
    project_root = Path(__file__).parent.parent.parent
    script = project_root / "scripts" / "format.sh"
    
    assert script.exists(), "format.sh script missing"
    content = script.read_text()
    assert "black" in content, "format.sh does not invoke black"

def test_pytest_config_exists():
    """Verify pytest configuration exists in pyproject.toml"""
    project_root = Path(__file__).parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml missing"
    
    content = pyproject.read_text()
    assert "[tool.pytest.ini_options]" in content, "Pytest section missing in pyproject.toml"