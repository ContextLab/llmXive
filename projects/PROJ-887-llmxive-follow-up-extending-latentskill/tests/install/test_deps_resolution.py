"""
Test to verify that all required dependencies are installed and importable.
This test ensures that the `pip install -r requirements.txt` command (T002b)
successfully resolved all version conflicts and installed the necessary packages.
"""
import importlib
import sys
import pytest

REQUIRED_PACKAGES = [
  ("torch", "torch"),
  ("numpy", "numpy"),
  ("scikit-learn", "sklearn"),
  ("sentence-transformers", "sentence_transformers"),
  ("transformers", "transformers"),
  ("pandas", "pandas"),
  ("scipy", "scipy"),
  ("llama-cpp-python", "llama_cpp"),
  ("pytest", "pytest"),
  ("faiss-cpu", "faiss"),
]

@pytest.mark.parametrize("pkg_name, import_name", REQUIRED_PACKAGES)
def test_package_importable(pkg_name, import_name):
    """Verify that each required package can be imported."""
    try:
        importlib.import_module(import_name)
    except ImportError as e:
        pytest.fail(f"Package '{pkg_name}' (import name: '{import_name}') is not installed or cannot be imported: {e}")

def test_version_compatibility_torch_and_cuda():
    """
    Basic check to ensure torch is installed. 
    Note: We do not enforce CUDA here as the project targets CPU-only free-tier CI,
    but we ensure the core library is present.
    """
    import torch
    # If torch is installed, this passes.
    assert torch.__version__ is not None
    
def test_faiss_cpu_available():
    """Verify faiss-cpu is specifically available."""
    import faiss
    # Ensure we are using the CPU version if possible, though import usually suffices for verification
    assert hasattr(faiss, 'IndexFlatL2')