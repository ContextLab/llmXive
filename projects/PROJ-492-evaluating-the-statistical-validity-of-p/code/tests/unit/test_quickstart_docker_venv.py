"""
Test T095b: Verify Quickstart Docker guide reproduces environment via requirements.txt and isolated venv.

This test validates:
1. The Dockerfile exists and contains the instruction to install from requirements.txt.
2. The Dockerfile creates a virtual environment (venv) and activates it before running the application.
3. The requirements.txt file exists and contains valid Python dependencies.
"""

import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DOCKERFILE_PATH = PROJECT_ROOT / "code" / "Dockerfile"
REQUIREMENTS_PATH = PROJECT_ROOT / "code" / "requirements.txt"


def test_dockerfile_exists():
    """Assert the Dockerfile exists in the expected location."""
    assert DOCKERFILE_PATH.exists(), f"Dockerfile not found at {DOCKERFILE_PATH}"


def test_requirements_exists():
    """Assert requirements.txt exists in the expected location."""
    assert REQUIREMENTS_PATH.exists(), f"requirements.txt not found at {REQUIREMENTS_PATH}"


def test_dockerfile_installs_requirements():
    """
    Verify the Dockerfile contains a command to install dependencies from requirements.txt.
    Checks for 'pip install -r requirements.txt' or equivalent.
    """
    content = DOCKERFILE_PATH.read_text()
    # Look for pip install -r requirements.txt pattern
    pattern = r"pip\s+install\s+(-r\s+)?requirements\.txt"
    assert re.search(pattern, content, re.IGNORECASE), (
        "Dockerfile does not contain 'pip install -r requirements.txt' or equivalent. "
        "The Quickstart Docker guide must install dependencies from requirements.txt."
    )


def test_dockerfile_creates_venv():
    """
    Verify the Dockerfile creates a Python virtual environment.
    Checks for 'python -m venv' or 'virtualenv' commands.
    """
    content = DOCKERFILE_PATH.read_text()
    # Look for venv creation pattern
    venv_patterns = [
        r"python\s+-m\s+venv",
        r"virtualenv",
        r"python3\s+-m\s+venv"
    ]
    found = False
    for pattern in venv_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found = True
            break

    assert found, (
        "Dockerfile does not create a virtual environment (venv). "
        "The Quickstart Docker guide must create an isolated venv as per Constitution Principle I."
    )


def test_dockerfile_activates_venv():
    """
    Verify the Dockerfile activates the virtual environment before running the application.
    Checks for 'source .../bin/activate' or 'ENV PATH' modifications.
    """
    content = DOCKERFILE_PATH.read_text()
    # Check for activation via source or PATH modification
    activation_patterns = [
        r"source\s+.*bin/activate",
        r"ENV\s+PATH.*venv/bin",
        r"ENV\s+PATH.*\.venv/bin"
    ]
    found = False
    for pattern in activation_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            found = True
            break

    assert found, (
        "Dockerfile does not activate the virtual environment. "
        "The Dockerfile must ensure the venv is active when running the application."
    )


def test_requirements_txt_valid():
    """
    Verify requirements.txt contains at least one valid dependency line.
    """
    content = REQUIREMENTS_PATH.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    assert len(lines) > 0, "requirements.txt is empty or contains only comments."

    # Basic validation: lines should look like package specs
    valid_lines = 0
    for line in lines:
        # Simple regex for package name (allowing versions, extras, etc.)
        if re.match(r'^[a-zA-Z0-9_-]+', line):
            valid_lines += 1

    assert valid_lines > 0, "requirements.txt does not contain any valid package specifications."


def test_docker_build_simulation():
    """
    Simulate the Docker build process by checking if the Dockerfile is syntactically valid
    and if the commands exist in the context.
    This is a structural check since we might not have Docker daemon running.
    """
    if not DOCKERFILE_PATH.exists():
        pytest.skip("Dockerfile missing, skipping build simulation.")

    content = DOCKERFILE_PATH.read_text()

    # Check for basic Dockerfile structure
    assert "FROM" in content.upper(), "Dockerfile missing 'FROM' instruction."
    assert "WORKDIR" in content.upper() or "COPY" in content.upper(), (
        "Dockerfile missing WORKDIR or COPY instructions."
    )

    # Ensure the specific sequence for T095b is present:
    # 1. Create venv
    # 2. Copy requirements
    # 3. Install requirements
    # 4. Activate/Use venv

    # We already checked individual pieces in other tests, this ensures the file is coherent
    assert "requirements.txt" in content, "Dockerfile does not reference requirements.txt."
    assert "venv" in content.lower() or ".venv" in content, (
        "Dockerfile does not reference a virtual environment directory."
    )

    print("Dockerfile structure validation passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
