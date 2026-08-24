import subprocess
import sys
import os

def test_linting_config_exists():
    """Verify that linting configuration files exist."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    assert os.path.exists(os.path.join(project_root, "code", ".flake8")), \
        "flake8 config file missing"
    assert os.path.exists(os.path.join(project_root, "pyproject.toml")), \
        "pyproject.toml missing"
    
    with open(os.path.join(project_root, "pyproject.toml"), "r") as f:
        content = f.read()
        assert "[tool.black]" in content, "black config missing in pyproject.toml"
        assert "[tool.isort]" in content, "isort config missing in pyproject.toml"

def test_linting_module_imports():
    """Verify that linting_config module can be imported and has required functions."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
    from linting_config import run_flake8, run_black, run_isort, run_all_checks, fix_all
    
    assert callable(run_flake8)
    assert callable(run_black)
    assert callable(run_isort)
    assert callable(run_all_checks)
    assert callable(fix_all)

def test_requirements_includes_linting_tools():
    """Verify that requirements.txt includes linting dependencies."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req_path = os.path.join(project_root, "requirements.txt")
    
    assert os.path.exists(req_path), "requirements.txt not found"
    
    with open(req_path, "r") as f:
        content = f.read().lower()
        assert "flake8" in content, "flake8 not in requirements.txt"
        assert "black" in content, "black not in requirements.txt"
        assert "isort" in content, "isort not in requirements.txt"