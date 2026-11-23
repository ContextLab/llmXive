"""
Test suite to verify that all pinned dependencies in requirements.txt
are installed and importable.
"""
import importlib
import sys

# Mapping of package names to their primary importable modules
# Note: 'diffcp' might import as 'diffcp', 'torch' as 'torch', etc.
REQUIRED_MODULES = {
    "pybullet": "pybullet",
    "torch": "torch",
    "cvxpy": "cvxpy",
    "diffcp": "diffcp",
    "scipy": "scipy",
    "pandas": "pandas",
    "numpy": "numpy",
    "pytest": "pytest",
}

def test_all_dependencies_importable():
    """Ensure every dependency in requirements.txt can be imported."""
    missing = []
    for pkg_name, import_name in REQUIRED_MODULES.items():
        try:
            importlib.import_module(import_name)
        except ImportError as e:
            missing.append((pkg_name, str(e)))

    if missing:
        error_msg = "Missing or unimportable dependencies:\n"
        for pkg, err in missing:
            error_msg += f"  - {pkg}: {err}\n"
        raise AssertionError(error_msg)

def test_torch_cpu_available():
    """Verify that torch is available (CPU mode is sufficient for this project)."""
    import torch
    # Just checking import is enough for CPU, but we ensure it's not a stub
    assert torch.__version__ is not None
    # Ensure we can access at least one tensor operation
    x = torch.zeros(1)
    assert x.numel() == 1
