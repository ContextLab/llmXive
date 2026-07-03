import pytest
import importlib

# List of core packages expected from requirements.txt
REQUIRED_PACKAGES = [
    "numpy",
    "pandas",
    "scipy",
    "astropy",
    "requests",
    "pyyaml",
    "jsonschema",
    "pytest",
    "tqdm",
]

def test_required_packages_importable():
    """Verify that all required packages defined in requirements.txt are importable."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)

    assert not missing, f"Missing required packages: {missing}"

def test_astropy_version_constraint():
    """Verify astropy version is within expected range (>=6.0.0)."""
    import astropy
    version = tuple(map(int, astropy.__version__.split('.')[:2]))
    assert version >= (6, 0), f"astropy version {astropy.__version__} is too old (>=6.0.0 required)"

def test_numpy_version_constraint():
    """Verify numpy version is within expected range (>=1.26.0, <2.0.0)."""
    import numpy
    version = tuple(map(int, numpy.__version__.split('.')[:2]))
    assert version >= (1, 26), f"numpy version {numpy.__version__} is too old (>=1.26.0 required)"
    assert version < (2, 0), f"numpy version {numpy.__version__} is too new (<2.0.0 required)"