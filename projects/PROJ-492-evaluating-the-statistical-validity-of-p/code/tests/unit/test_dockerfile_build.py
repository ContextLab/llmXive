"""
Test to verify that the Dockerfile exists and contains the expected base image configuration.
Note: Actual Docker image building is typically done in CI (GitHub Actions) or manually.
This test ensures the artifact is present and syntactically correct for the build process.
"""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCKERFILE_PATH = PROJECT_ROOT / "Dockerfile"

def test_dockerfile_exists():
    """Verify that the Dockerfile exists at the project root."""
    assert DOCKERFILE_PATH.exists(), f"Dockerfile not found at {DOCKERFILE_PATH}"

def test_dockerfile_cpu_base_image():
    """Verify that the Dockerfile uses a CPU-compatible base image (no GPU specific tags)."""
    content = DOCKERFILE_PATH.read_text()
    
    # Check for a standard CPU-compatible base image
    # We expect 'python:3.10-slim' or similar, NOT 'nvidia/cuda' or specific GPU tags
    assert "FROM python:" in content, "Dockerfile must start with a Python base image"
    assert "nvidia" not in content.lower(), "Dockerfile should not reference NVIDIA/GPU images"
    assert "cuda" not in content.lower(), "Dockerfile should not reference CUDA images"

def test_dockerfile_syntax_validity():
    """
    Verify that the Dockerfile has valid syntax by attempting a dry-run build or parsing.
    Since we might not have Docker daemon in all test environments, we check for common syntax errors.
    """
    content = DOCKERFILE_PATH.read_text()
    lines = content.splitlines()
    
    # Basic sanity checks
    assert len(lines) > 0, "Dockerfile is empty"
    
    # Check that FROM is present and near the top
    from_found = False
    for line in lines[:5]:
        if line.strip().startswith("FROM "):
            from_found = True
            break
    
    assert from_found, "Dockerfile must contain a FROM instruction"

def test_dockerfile_builds_locally():
    """
    Attempt to build the Docker image locally to ensure it works.
    This test requires Docker to be installed and running.
    Skips if Docker is not available.
    """
    if not DOCKERFILE_PATH.exists():
        pytest.skip("Dockerfile does not exist")

    try:
        # Try to build the image with a random tag
        tag = "proj492-test-build"
        result = subprocess.run(
            ["docker", "build", "-t", tag, "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            pytest.fail(f"Docker build failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        
        # Clean up the test image
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
    except FileNotFoundError:
        pytest.skip("Docker is not installed or not in PATH")
    except subprocess.TimeoutExpired:
        pytest.fail("Docker build timed out")
