import sys
import importlib
import subprocess
import pytest
import platform
import pkg_resources

def test_python_version():
    """Verify Python 3.11 is used."""
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 11, f"Expected Python 3.11, got {sys.version}"

def test_required_packages_installed():
    """Verify all core dependencies are installed."""
    required = [
        "torch",
        "transformers",
        "accelerate",
        "peft",
        "scikit-learn",
        "scipy",
        "pandas",
        "numpy",
        "datasets",
        "tqdm",
        "yaml",
    ]
    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            pytest.fail(f"Package '{pkg}' is not installed.")

def test_package_versions():
    """Verify minimum versions for critical packages."""
    min_versions = {
        "torch": "2.3.0",
        "transformers": "4.40.0",
        "scikit-learn": "1.4.0",
        "pandas": "2.0.0",
    }
    for pkg, min_ver in min_versions.items():
        try:
            dist = pkg_resources.get_distribution(pkg)
            assert pkg_resources.parse_version(dist.version) >= pkg_resources.parse_version(min_ver), \
                f"{pkg} version {dist.version} is below minimum {min_ver}"
        except Exception as e:
            pytest.fail(f"Could not verify version for {pkg}: {e}")

def test_torch_cuda_available():
    """Ensure CUDA is NOT available (CPU-only constraint)."""
    import torch
    assert not torch.cuda.is_available(), "CUDA is available, but this project requires CPU-only execution."

def test_huggingface_hub():
    """Verify huggingface_hub is accessible."""
    try:
        from huggingface_hub import HfFolder
        # Just checking import and basic class availability
        assert HfFolder is not None
    except ImportError:
        pytest.fail("huggingface_hub is not properly installed or configured.")
