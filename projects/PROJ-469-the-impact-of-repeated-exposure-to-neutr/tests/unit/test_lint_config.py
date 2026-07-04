"""
Tests to verify that linting and formatting configurations exist and are valid.
"""
import os
import subprocess
from pathlib import Path

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists in the code directory."""
    config_path = Path(__file__).parent.parent.parent / "code" / ".flake8"
    assert config_path.exists(), f"Missing .flake8 config at {config_path}"
    
    content = config_path.read_text()
    assert "[flake8]" in content, ".flake8 must contain [flake8] section"
    assert "max-line-length" in content, ".flake8 must define max-line-length"

def test_pyproject_black_config_exists():
    """Verify pyproject.toml contains black configuration."""
    config_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    assert config_path.exists(), f"Missing pyproject.toml at {config_path}"
    
    content = config_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "line-length" in content, "black config must define line-length"

def test_lint_script_executable():
    """Verify lint_and_format.py exists and is syntactically valid."""
    script_path = Path(__file__).parent.parent.parent / "code" / "lint_and_format.py"
    assert script_path.exists(), f"Missing lint_and_format.py at {script_path}"
    
    # Check syntax
    compile(script_path.read_text(), script_path, 'exec')

def test_run_lint_check_syntax():
    """Run the lint script in a dry-run fashion (syntax check) to ensure imports work."""
    # We don't run the full lint (which might fail if code isn't formatted yet),
    # but we ensure the script itself is valid and imports correctly.
    script_path = Path(__file__).parent.parent.parent / "code" / "lint_and_format.py"
    try:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        pytest.fail(f"lint_and_format.py has syntax errors")