"""
code/tests/test_setup_env.py
----------------------------

Unit‑test for `code/setup/setup_env.py`.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import pytest

# Ensure 'code' directory is in sys.path so we can import from setup.setup_env
# This file is at <root>/code/tests/test_setup_env.py
# We need to add <root>/code to sys.path
current_file_path = Path(__file__).resolve()
code_dir = current_file_path.parents[1] # parents[0] is tests/, parents[1] is code/
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup.setup_env import (
    DEFAULT_VENV_PATH,
    create_virtualenv,
    install_requirements,
    validate_requirements_schema,
)

@pytest.fixture(scope="function")
def clean_venv():
    """Ensure a fresh `.venv` directory for each test."""
    venv_path = DEFAULT_VENV_PATH
    if venv_path.exists():
        shutil.rmtree(venv_path)
    yield venv_path
    if venv_path.exists():
        shutil.rmtree(venv_path)

def _python_executable(venv_path: Path) -> Path:
    """Return the path to the `python` binary inside the venv."""
    if (venv_path / "bin" / "python").exists():
        return venv_path / "bin" / "python"
    return venv_path / "Scripts" / "python.exe"

def test_virtualenv_creation_and_package_installation(clean_venv):
    """
    1. Create the virtual environment.
    2. Install the pinned dependencies.
    3. Verify that a known package (pandas) can be imported from the venv.
    """
    create_virtualenv(clean_venv)
    assert clean_venv.is_dir(), "Virtual environment directory was not created"

    install_requirements(clean_venv)

    python_bin = _python_executable(clean_venv)
    result = subprocess.run(
        [str(python_bin), "-c", "import pandas; print(pandas.__version__)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Importing pandas failed: {result.stderr}"
    assert result.stdout.strip(), "Pandas version output is empty"

def test_requirements_schema_validation():
    """
    Ensure that `requirements.txt` conforms to the contract schema.
    """
    # No exception -> validation passed
    validate_requirements_schema()