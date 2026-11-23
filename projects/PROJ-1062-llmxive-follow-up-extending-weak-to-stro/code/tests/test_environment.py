import sys
import importlib
import subprocess
import pytest
import platform
import pkg_resources
from pathlib import Path

def test_python_version():
    """Test that Python version meets requirements (3.9+)."""
    current_version = platform.python_version_tuple()
    major, minor = int(current_version[0]), int(current_version[1])
    assert (major, minor) >= (3, 9), f"Python 3.9+ required, found {major}.{minor}"

def test_required_packages_installed():
    """Test that all required packages from requirements.txt are installed."""
    required_packages = [
        'transformers',
        'datasets',
        'torch',
        'bitsandbytes',
        'scikit-learn',
        'scipy',
        'pandas',
        'numpy',
        'statsmodels',
        'pyyaml',
        'ruff',
        'black'
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    assert len(missing) == 0, f"Missing packages: {missing}"

def test_package_versions():
    """Test specific version constraints (e.g., bitsandbytes==0.43.0)."""
    # bitsandbytes version check
    try:
        import bitsandbytes
        version = bitsandbytes.__version__
        assert version == "0.43.0", f"bitsandbytes version mismatch. Expected 0.43.0, found {version}"
    except ImportError:
        pytest.fail("bitsandbytes is not installed")
    
    # torch version check (minimum)
    try:
        import torch
        version = tuple(map(int, torch.__version__.split('+')[0].split('.')[:2]))
        assert version >= (2, 1), f"torch >= 2.1.0 required, found {torch.__version__}"
    except ImportError:
        pytest.fail("torch is not installed")

def test_torch_cpu_only():
    """Test that torch is available (CUDA check is informational for this project)."""
    try:
        import torch
        # The project requires CPU-only execution capability, but doesn't strictly forbid CUDA hardware.
        # We just ensure torch is importable and functional.
        x = torch.zeros(1)
        assert x.item() == 0.0
    except ImportError:
        pytest.fail("torch is not installed")

def test_huggingface_hub():
    """Test that huggingface_hub is available (required by datasets/transformers)."""
    try:
        import huggingface_hub
    except ImportError:
        pytest.fail("huggingface_hub is not installed")

def test_requirements_txt_exists():
    """Test that requirements.txt exists in the project root."""
    requirements_path = Path("requirements.txt")
    assert requirements_path.exists(), "requirements.txt not found in project root"

def test_setup_env_script_exists():
    """Test that code/setup_env.py exists."""
    setup_script = Path("code/setup_env.py")
    assert setup_script.exists(), "code/setup_env.py not found"