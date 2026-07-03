"""
Unit test to verify that all required dependencies in requirements.txt can be imported.
This ensures the environment setup is correct before running the pipeline.
"""
import importlib
import pytest

REQUIRED_PACKAGES = [
    "numpy",
    "scipy",
    "pandas",
    "torch",
    "torch_geometric",
    "ase",
    "statsmodels",
    "sklearn",
    "yaml",
]

@pytest.mark.parametrize("package_name", REQUIRED_PACKAGES)
def test_dependency_import(package_name):
    """Test that each required dependency can be imported."""
    try:
        importlib.import_module(package_name)
    except ImportError as e:
        pytest.fail(f"Failed to import required package '{package_name}': {e}")

def test_torch_geometric_installation():
    """Specific check for torch_geometric as it often has installation issues."""
    try:
        import torch_geometric
        assert torch_geometric.__version__ is not None
    except ImportError:
        pytest.fail("torch_geometric is not installed correctly.")