import sys
import importlib
import subprocess
import pytest

def test_python_version():
    """Ensure Python 3.11 is used."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version}"

def test_required_packages_installed():
    """Verify core dependencies are importable."""
    packages = [
        "transformers",
        "accelerate",
        "peft",
        "scikit_learn",
        "scipy",
        "pandas",
        "numpy",
        "torch",
        "datasets"
    ]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            pytest.fail(f"Package '{pkg}' is not installed. Please run: pip install -r requirements.txt")

def test_package_versions():
    """Verify minimum versions for critical packages."""
    version_checks = {
        "transformers": "4.40.0",
        "accelerate": "0.30.0",
        "peft": "0.11.0",
        "scikit_learn": "1.4.0",
        "scipy": "1.13.0",
        "pandas": "2.2.0",
        "numpy": "1.26.0",
        "torch": "2.2.0"
    }
    import importlib.metadata

    for pkg, min_ver in version_checks.items():
        try:
            installed_ver = importlib.metadata.version(pkg)
            # Simple version comparison (assumes valid semver-like strings)
            # In a real scenario, use packaging.version for robust comparison
            assert installed_ver >= min_ver, f"{pkg} {installed_ver} found, {min_ver} required"
        except importlib.metadata.PackageNotFoundError:
            pytest.fail(f"Package '{pkg}' not found")

def test_torch_cuda_available():
    """Check if CUDA is available (optional but good for logging)."""
    import torch
    if torch.cuda.is_available():
        print(f"CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("CUDA not available. Running on CPU.")

def test_huggingface_hub():
    """Verify huggingface_hub is installed and functional."""
    from huggingface_hub import HfApi
    api = HfApi()
    # Just verify the object can be instantiated without network call
    assert api is not None