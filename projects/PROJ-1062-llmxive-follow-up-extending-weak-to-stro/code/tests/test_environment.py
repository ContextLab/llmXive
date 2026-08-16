import sys
import importlib
import subprocess
import pytest

def test_python_version():
    """Verify Python 3.11+ is used."""
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version}"

def test_required_packages_installed():
    """Verify all required packages are importable."""
    required_packages = [
        "torch",
        "transformers",
        "accelerate",
        "peft",
        "bitsandbytes",
        "pandas",
        "numpy",
        "scipy",
        "scikit-learn",
        "huggingface_hub",
        "yaml",
        "tqdm",
        "matplotlib",
        "seaborn",
    ]
    missing = []
    for pkg in required_packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        raise ImportError(f"Missing required packages: {missing}")

def test_package_versions():
    """Verify minimum versions for critical packages."""
    import importlib.metadata

    checks = [
        ("torch", "2.1.0"),
        ("transformers", "4.36.0"),
        ("pandas", "2.1.0"),
        ("numpy", "1.24.0"),
        ("scipy", "1.11.0"),
        ("scikit-learn", "1.3.0"),
    ]

    for pkg_name, min_ver in checks:
        try:
            version = importlib.metadata.version(pkg_name)
            # Simple version comparison (assumes PEP 440 compatible)
            from packaging.version import parse
            if parse(version) < parse(min_ver):
                raise AssertionError(
                    f"{pkg_name} version {version} < required {min_ver}"
                )
        except importlib.metadata.PackageNotFoundError:
            pytest.fail(f"{pkg_name} not installed")

def test_torch_cuda_available():
    """Log CUDA availability (optional for CPU-only runner)."""
    import torch
    cuda_available = torch.cuda.is_available()
    # Just log, don't fail if not available since we target CPU
    print(f"PyTorch CUDA available: {cuda_available}")

def test_huggingface_hub():
    """Verify huggingface_hub is functional."""
    from huggingface_hub import hf_hub_download, HfApi
    # Just verify import and basic attribute access
    assert hasattr(HfApi, "list_repo_files")
    print("huggingface_hub verified")
