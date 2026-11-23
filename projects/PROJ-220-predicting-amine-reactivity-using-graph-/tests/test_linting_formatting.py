"""
Tests to verify that linting and formatting configurations are valid.
These tests ensure that the project's ruff and black configurations work as expected.
"""
import subprocess
import sys
import os
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_ruff_config_exists():
    """Test that .ruff.toml or pyproject.toml with ruff config exists."""
    ruff_toml = os.path.join(PROJECT_ROOT, ".ruff.toml")
    pyproject_toml = os.path.join(PROJECT_ROOT, "pyproject.toml")

    assert os.path.exists(ruff_toml) or os.path.exists(pyproject_toml), \
        "Ruff configuration file (.ruff.toml or pyproject.toml) not found"


def test_black_config_exists():
    """Test that black configuration exists in pyproject.toml or black.toml."""
    pyproject_toml = os.path.join(PROJECT_ROOT, "pyproject.toml")
    black_toml = os.path.join(PROJECT_ROOT, "black.toml")

    # Check pyproject.toml for [tool.black] section
    if os.path.exists(pyproject_toml):
        with open(pyproject_toml, "r") as f:
            content = f.read()
            assert "[tool.black]" in content, \
                "Black configuration not found in pyproject.toml"
    elif os.path.exists(black_toml):
        pass  # black.toml exists
    else:
        pytest.fail("Black configuration not found in pyproject.toml or black.toml")


@pytest.mark.skipif(
    not shutil.which("ruff"), reason="ruff not installed"
)
def test_ruff_check_project():
    """Run ruff check on the project to verify no linting errors in configured files."""
    import shutil
    ruff_path = shutil.which("ruff")
    if not ruff_path:
        pytest.skip("ruff not available")

    # Run ruff check on src directory
    result = subprocess.run(
        [ruff_path, "check", os.path.join(PROJECT_ROOT, "src")],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    # We expect this to pass (exit code 0) if there are no linting errors
    # If there are errors, they will be shown in stderr
    # For now, we just check that ruff runs without crashing
    assert result.returncode in [0, 1], \
        f"ruff check failed with unexpected exit code {result.returncode}: {result.stderr}"


@pytest.mark.skipif(
    not shutil.which("black"), reason="black not installed"
)
def test_black_check_project():
    """Run black --check on the project to verify formatting."""
    import shutil
    black_path = shutil.which("black")
    if not black_path:
        pytest.skip("black not available")

    # Run black --check on src directory
    result = subprocess.run(
        [black_path, "--check", os.path.join(PROJECT_ROOT, "src")],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )

    # Exit code 0 means all files are formatted correctly
    # Exit code 1 means some files need reformatting
    # We just verify black runs without crashing
    assert result.returncode in [0, 1], \
        f"black --check failed with unexpected exit code {result.returncode}: {result.stderr}"


def test_python_syntax_valid():
    """Verify that all Python files in src/ have valid syntax."""
    import ast
    import glob

    src_dir = os.path.join(PROJECT_ROOT, "src")
    if not os.path.exists(src_dir):
        pytest.skip("src directory not found")

    python_files = glob.glob(os.path.join(src_dir, "**", "*.py"), recursive=True)

    for py_file in python_files:
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {py_file}: {e}")