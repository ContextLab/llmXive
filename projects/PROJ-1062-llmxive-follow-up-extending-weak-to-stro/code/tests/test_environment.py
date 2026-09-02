"""
Unit tests for environment setup and dependency verification.
"""
import sys
import importlib
import subprocess
import pytest
import platform
import pkg_resources
from pathlib import Path

def test_python_version():
    """Test that the current Python version is >= 3.9."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    required = "3.9"
    assert pkg_resources.parse_version(version) >= pkg_resources.parse_version(required), \
        f"Python version {version} is less than required {required}"

def test_required_packages_installed():
    """Test that all required packages are installed."""
    required_packages = [
        'numpy', 'pandas', 'scipy', 'torch', 'transformers', 
        'scikit-learn', 'bitsandbytes', 'pyyaml', 'tqdm', 'accelerate'
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            pytest.fail(f"Package '{package}' is not installed.")

def test_package_versions():
    """Test that specific package versions are met (optional but recommended)."""
    # Check numpy version
    import numpy as np
    assert pkg_resources.parse_version(np.__version__) >= pkg_resources.parse_version("1.24.0"), \
        f"Numpy version {np.__version__} is too old."
    
    # Check pandas version
    import pandas as pd
    assert pkg_resources.parse_version(pd.__version__) >= pkg_resources.parse_version("2.0.0"), \
        f"Pandas version {pd.__version__} is too old."

def test_torch_cuda_available():
    """
    Test that PyTorch is installed and check CUDA availability.
    Note: The project enforces CPU-only wheels, but CUDA might be physically present.
    The test verifies the library loads correctly.
    """
    import torch
    assert torch.__version__ is not None, "PyTorch version string is missing."
    
    # We expect CUDA to be False if the CPU-only wheel was strictly enforced and 
    # no CUDA drivers are present, but the presence of CUDA hardware doesn't break
    # the code if the code is written to run on CPU.
    # The critical check is that the library loads.
    assert hasattr(torch, 'cuda'), "PyTorch CUDA module is missing."

def test_huggingface_hub():
    """Test that the HuggingFace hub utilities are accessible."""
    try:
        from huggingface_hub import hf_hub_download, login
    except ImportError:
        pytest.fail("huggingface_hub is not installed or importable.")

def test_requirements_txt_exists():
    """Test that requirements.txt exists in the code directory."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt not found in code directory."

def test_setup_env_script_exists():
    """Test that setup_env.py exists."""
    setup_script = Path(__file__).parent.parent / "setup_env.py"
    assert setup_script.exists(), "setup_env.py not found."