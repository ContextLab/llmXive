"""
Environment and tooling tests to verify linting and formatting tools are configured correctly.
"""
import sys
import importlib
import subprocess
import pytest
import os

def test_python_version():
    """Verify Python version is 3.11 or higher."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"

def test_required_packages_installed():
    """Verify ruff and black are installed."""
    packages = ["ruff", "black"]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            # Check if installed via subprocess (some tools might be CLI only but not importable directly)
            # For ruff and black, they are importable or at least have CLI entry points.
            # We check CLI availability as a fallback.
            result = subprocess.run([sys.executable, "-m", pkg, "--version"], capture_output=True, text=True)
            assert result.returncode == 0, f"Package {pkg} is not installed or not accessible."

def test_package_versions():
    """Verify minimum versions of tools."""
    # Check Ruff version
    result = subprocess.run([sys.executable, "-m", "ruff", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "Ruff not found"
    version_str = result.stdout.split()[1]
    major, minor = map(int, version_str.split(".")[:2])
    assert (major, minor) >= (0, 3), f"Ruff 0.3.0+ required, got {version_str}"

    # Check Black version
    result = subprocess.run([sys.executable, "-m", "black", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "Black not found"
    version_str = result.stdout.split()[1]
    major, minor = map(int, version_str.split(".")[:2])
    assert (major, minor) >= (24, 3), f"Black 24.3.0+ required, got {version_str}"

def test_torch_cuda_available():
    """Verify torch is available (CUDA check is optional but good for environment sanity)."""
    import torch
    assert torch.__version__ is not None
    # We don't require CUDA for this specific project constraint (CPU-only runner),
    # but we ensure torch is importable.

def test_huggingface_hub():
    """Verify huggingface_hub is available."""
    import huggingface_hub
    assert huggingface_hub.__version__ is not None