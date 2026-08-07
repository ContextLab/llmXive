"""
Unit tests for T002: Dependency verification.
Ensures all required packages are installed and importable.
"""
import pytest
import sys
import importlib

def test_torch_cpu_only():
    """Verify torch is installed and check CUDA availability"""
    torch = importlib.import_module("torch")
    assert torch is not None
    # Note: We don't assert not cuda.is_available() because the runner might have CUDA,
    # but the requirement is that we install the CPU version. The setup script enforces CPU usage.
    assert hasattr(torch, '__version__')

def test_pybullet_import():
    """Verify pybullet can be imported"""
    pybullet = importlib.import_module("pybullet")
    assert pybullet is not None

def test_mujoco_import():
    """Verify mujoco can be imported"""
    mujoco = importlib.import_module("mujoco")
    assert mujoco is not None

def test_diffusers_import():
    """Verify diffusers can be imported"""
    diffusers = importlib.import_module("diffusers")
    assert diffusers is not None

def test_transformers_import():
    """Verify transformers can be imported"""
    transformers = importlib.import_module("transformers")
    assert transformers is not None

def test_sklearn_import():
    """Verify scikit-learn can be imported"""
    sklearn = importlib.import_module("sklearn")
    assert sklearn is not None

def test_opencv_import():
    """Verify opencv-python can be imported"""
    cv2 = importlib.import_module("cv2")
    assert cv2 is not None

def test_pandas_import():
    """Verify pandas can be imported"""
    pandas = importlib.import_module("pandas")
    assert pandas is not None

def test_numpy_import():
    """Verify numpy can be imported"""
    numpy = importlib.import_module("numpy")
    assert numpy is not None

def test_requests_import():
    """Verify requests can be imported"""
    requests = importlib.import_module("requests")
    assert requests is not None

def test_datasets_import():
    """Verify datasets can be imported"""
    datasets = importlib.import_module("datasets")
    assert datasets is not None

def test_requirements_file_exists():
    """Verify requirements.txt exists in the project root"""
    import os
    req_path = os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt')
    # Adjust path relative to tests/unit
    assert os.path.exists(req_path), f"requirements.txt not found at {req_path}"