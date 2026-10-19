"""
code/tests/test_setup_env.py
----------------------------

Unit‑test for ``code/setup/setup_env.py``.

The test verifies three functional requirements (FR‑001):

1. The virtual environment directory ``.venv`` is created.
2. All packages declared in ``requirements.txt`` can be imported from the
   freshly created environment (we check a representative package – ``pandas``).
3. The requirements file validates against the JSON‑schema contract.

The test cleans up the temporary virtual environment after execution so it
does not interfere with subsequent runs.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

import pytest

# Import the module under test
from setup.setup_env import (
    DEFAULT_VENV_PATH,
    create_virtualenv,
    install_requirements,
    validate_requirements_schema,
)

@pytest.fixture(scope="function")
def clean_venv():
    """Ensure a fresh ``.venv`` directory for each test."""
    venv_path = DEFAULT_VENV_PATH
    if venv_path.exists():
        shutil.rmtree(venv_path)
    yield venv_path
    # Teardown – remove the virtual environment after the test
    if venv_path.exists():
        shutil.rmtree(venv_path)

def _python_executable(venv_path: Path) -> Path:
    """Return the path to the ``python`` binary inside the venv."""
    if (venv_path / "bin" / "python").exists():
        return venv_path / "bin" / "python"
    return venv_path / "Scripts" / "python.exe"

def test_virtualenv_creation_and_package_installation(clean_venv):
    """
    1. Create the virtual environment.
    2. Install the pinned dependencies.
    3. Verify that a known package (pandas) can be imported from the venv.
    """
    # Step 1 – create the environment
    create_virtualenv(clean_venv)

    assert clean_venv.is_dir(), "Virtual environment directory was not created"

    # Step 2 – install requirements
    install_requirements(clean_venv)

    # Step 3 – try importing a package from the newly created environment
    python_bin = _python_executable(clean_venv)
    result = subprocess.run(
        [str(python_bin), "-c", "import pandas; print(pandas.__version__)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Importing pandas failed: {result.stderr}"
    # The version string is printed; we just assert that something was output.
    assert result.stdout.strip(), "Pandas version output is empty"

def test_requirements_schema_validation():
    """
    Ensure that ``requirements.txt`` conforms to the contract schema.
    The function under test raises if validation fails, so a successful
    return indicates compliance.
    """
    # No exception → validation passed
    validate_requirements_schema()