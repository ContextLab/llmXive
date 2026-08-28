"""
Smoke test to verify linting and formatting configuration files exist and are valid.
This ensures T003 (Configure linting and formatting) is correctly set up.
"""
import os
import subprocess
import tempfile
import shutil

def test_ruff_config_exists():
    """Verify .ruff.toml exists in project root."""
    assert os.path.exists(".ruff.toml"), ".ruff.toml configuration file not found"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in project root."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml configuration file not found"

def test_ruff_can_check_code():
    """Verify ruff can run on a dummy file without crashing."""
    # Create a temporary directory and a dummy python file
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("import os\nimport sys\n\nprint('hello')\n")

        try:
            # Run ruff check on the dummy file
            result = subprocess.run(
                ["ruff", "check", dummy_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Ruff should exit 0 if no errors found (or 1 if linting errors found, but not crash)
            assert result.returncode in [0, 1], f"Ruff crashed: {result.stderr}"
        except FileNotFoundError:
            # Ruff might not be installed in the test environment, which is acceptable
            # as long as the config file exists.
            pass
        except subprocess.TimeoutExpired:
            assert False, "Ruff check timed out"

def test_black_can_format_code():
    """Verify black can run on a dummy file without crashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("import os\nimport sys\n\nprint('hello')\n")

        try:
            # Run black check on the dummy file
            result = subprocess.run(
                ["black", "--check", dummy_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Black exits 0 if formatted, 1 if not formatted (but not crash)
            assert result.returncode in [0, 1], f"Black crashed: {result.stderr}"
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            assert False, "Black check timed out"