"""
Tests for the lint check runner.
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_config_exists():
    """Verify that ruff configuration exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"
    
    content = pyproject.read_text()
    assert "[tool.ruff]" in content, "ruff configuration must be present"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "black configuration must be present"

def test_run_lint_checks_module_exists():
    """Verify that the run_lint_checks module exists."""
    code_dir = Path(__file__).parent.parent / "code"
    lint_script = code_dir / "run_lint_checks.py"
    assert lint_script.exists(), "run_lint_checks.py must exist"

def test_run_lint_checks_importable():
    """Verify that run_lint_checks can be imported."""
    code_dir = Path(__file__).parent.parent / "code"
    sys.path.insert(0, str(code_dir))
    try:
        import run_lint_checks
        assert hasattr(run_lint_checks, "run_command")
        assert hasattr(run_lint_checks, "main")
    finally:
        sys.path.remove(str(code_dir))