"""
Test T095b: Verify Quickstart Docker guide reproduces environment via requirements.txt and isolated venv.

This test validates:
1. The Dockerfile exists and contains the command to install from requirements.txt.
2. The Dockerfile creates an isolated virtual environment (venv).
3. The requirements.txt file exists and is non-empty.
4. The Dockerfile syntax is valid (basic check).
"""
import os
import re
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DOCKERFILE_PATH = PROJECT_ROOT / "code" / "Dockerfile"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
QUICKSTART_PATH = PROJECT_ROOT / "docs" / "README_QUICKSTART.md"

def test_dockerfile_exists():
    """Verify Dockerfile exists at the expected location."""
    assert DOCKERFILE_PATH.exists(), f"Dockerfile not found at {DOCKERFILE_PATH}"

def test_requirements_exists_and_non_empty():
    """Verify requirements.txt exists and is not empty."""
    assert REQUIREMENTS_PATH.exists(), f"requirements.txt not found at {REQUIREMENTS_PATH}"
    assert REQUIREMENTS_PATH.stat().st_size > 0, "requirements.txt is empty"

def test_dockerfile_installs_requirements():
    """Verify Dockerfile runs `pip install -r requirements.txt`."""
    content = DOCKERFILE_PATH.read_text()
    # Look for pip install command referencing requirements.txt
    pattern = r'pip\s+install\s+.*-r\s+requirements\.txt'
    assert re.search(pattern, content, re.IGNORECASE), (
        "Dockerfile must contain a command to install dependencies from requirements.txt"
    )

def test_dockerfile_creates_venv():
    """Verify Dockerfile creates an isolated virtual environment."""
    content = DOCKERFILE_PATH.read_text()
    # Check for venv creation commands (python -m venv or virtualenv)
    venv_patterns = [
        r'python\s+-m\s+venv',
        r'virtualenv',
        r'RUN\s+.*venv',
        r'RUN\s+.*virtualenv'
    ]
    
    found_venv = any(re.search(pattern, content, re.IGNORECASE) for pattern in venv_patterns)
    
    assert found_venv, (
        "Dockerfile must create an isolated virtual environment (venv) before installing dependencies. "
        "Expected to find 'python -m venv' or 'virtualenv' command."
    )

def test_dockerfile_venv_usage():
    """Verify the Dockerfile uses the created venv (activates or sets PATH)."""
    content = DOCKERFILE_PATH.read_text()
    
    # Check for activation or PATH modification to use venv
    usage_patterns = [
        r'source\s+.*bin/activate',
        r'\.\/.*bin/activate',
        r'ENV\s+PATH=.*venv/bin',
        r'PATH=.*venv/bin',
        r'python3\s+-m\s+venv.*&&.*source',
        r'RUN\s+.*venv.*&&.*source'
    ]
    
    found_usage = any(re.search(pattern, content, re.IGNORECASE) for pattern in usage_patterns)
    
    # If we found venv creation, we should also see it being used or activated
    # unless the CMD/ENTRYPOINT explicitly calls the python inside venv
    venv_creation = any(re.search(p, content, re.IGNORECASE) for p in [r'python\s+-m\s+venv', r'virtualenv'])
    
    if venv_creation:
        # Check if CMD/ENTRYPOINT uses the venv python explicitly
        explicit_python = re.search(r'(CMD|ENTRYPOINT).*venv/bin/python', content, re.IGNORECASE)
        if not found_usage and not explicit_python:
            pytest.fail(
                "Dockerfile creates a venv but does not activate it or use its python explicitly. "
                "Add 'source venv/bin/activate' or set ENV PATH to include venv/bin."
            )

def test_quickstart_references_docker_and_venv():
    """Verify Quickstart guide mentions Docker and venv/requirements."""
    if not QUICKSTART_PATH.exists():
        pytest.skip("Quickstart guide not found; skipping reference check.")
    
    content = QUICKSTART_PATH.read_text()
    
    has_docker = "docker" in content.lower()
    has_requirements = "requirements.txt" in content
    has_venv = "venv" in content.lower() or "virtualenv" in content.lower()
    
    assert has_docker, "Quickstart guide should mention Docker usage."
    assert has_requirements, "Quickstart guide should mention requirements.txt."
    # Note: venv mention is optional in text if Dockerfile handles it, but good to have
    
def test_dockerfile_syntax_valid():
    """Basic check for Dockerfile syntax validity (non-empty, has FROM)."""
    content = DOCKERFILE_PATH.read_text()
    assert "FROM" in content.upper(), "Dockerfile must have a FROM instruction."
    assert len(content.strip()) > 0, "Dockerfile is empty."