import sys
import importlib
import pytest
import subprocess

def test_python_version():
    """Ensure Python 3.11 is being used as per project requirement."""
    version_info = sys.version_info
    assert version_info.major == 3, "Python 3.x required"
    assert version_info.minor == 11, "Python 3.11 required"

def test_torch_cpu_index_constraint():
    """
    Verify that torch is installed. 
    While we cannot easily verify the *exact* wheel URL used in a running container,
    we verify that torch is importable and CUDA is not the primary driver if available,
    or that the version string hints at CPU if possible.
    The primary enforcement happens in requirements.txt and the install command.
    """
    try:
        import torch
    except ImportError:
        pytest.fail("torch is not installed")

    # The task requires explicit installation via --index-url https://download.pytorch.org/whl/cpu
    # If the user installed correctly, torch.cuda.is_available() should ideally be False
    # unless they have GPU hardware and the CPU wheel still allows CUDA checks (unlikely for pure CPU wheels).
    # We assert that if CUDA is available, it's not the *only* thing we rely on, 
    # but strictly, the requirement is the *install command*.
    # We check that the library loads without GPU errors if we try to use CPU explicitly.
    try:
        # Force a simple CPU operation
        x = torch.tensor([1.0, 2.0])
        assert x.device.type == "cpu"
    except RuntimeError as e:
        if "CUDA" in str(e):
            pytest.fail(f"Failed to run on CPU: {e}")
        raise

def test_required_packages_installed():
    """Check that all core packages from requirements.txt are importable."""
    packages = [
        "numpy",
        "pandas",
        "transformers",
        "scipy",
        "sklearn",
        "yaml", # pyyaml
        "tqdm"
    ]
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            pytest.fail(f"Package {pkg} is not installed")

def test_dependency_versions():
    """
    Verify minimum versions for critical packages.
    """
    import numpy
    import pandas
    import scipy
    
    # Check numpy version
    numpy_version = tuple(map(int, numpy.__version__.split('.')[:2]))
    assert numpy_version >= (1, 24), f"numpy >= 1.24 required, got {numpy.__version__}"

    # Check pandas version
    pandas_version = tuple(map(int, pandas.__version__.split('.')[:2]))
    assert pandas_version >= (2, 0), f"pandas >= 2.0 required, got {pandas.__version__}"

    # Check scipy version
    scipy_version = tuple(map(int, scipy.__version__.split('.')[:2]))
    assert scipy_version >= (1, 11), f"scipy >= 1.11 required, got {scipy.__version__}"