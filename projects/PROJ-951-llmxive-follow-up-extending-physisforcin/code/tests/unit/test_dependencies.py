import pytest
import sys
import importlib

def test_torch_cpu_only():
    """Verify torch is installed and CUDA is not detected."""
    try:
        import torch
    except ImportError:
        pytest.fail("PyTorch not installed")
    
    assert not torch.cuda.is_available(), "CUDA should not be available for this project"

def test_pybullet_import():
    """Verify pybullet can be imported."""
    try:
        import pybullet
    except ImportError:
        pytest.fail("PyBullet not installed")

def test_mujoco_import():
    """Verify mujoco can be imported."""
    try:
        import mujoco
    except ImportError:
        pytest.fail("MuJoCo not installed")

def test_diffusers_import():
    """Verify diffusers can be imported."""
    try:
        import diffusers
    except ImportError:
        pytest.fail("Diffusers not installed")

def test_transformers_import():
    """Verify transformers can be imported."""
    try:
        import transformers
    except ImportError:
        pytest.fail("Transformers not installed")

def test_sklearn_import():
    """Verify scikit-learn can be imported."""
    try:
        import sklearn
    except ImportError:
        pytest.fail("Scikit-learn not installed")

def test_opencv_import():
    """Verify opencv-python can be imported."""
    try:
        import cv2
    except ImportError:
        pytest.fail("OpenCV not installed")

def test_pandas_import():
    """Verify pandas can be imported."""
    try:
        import pandas
    except ImportError:
        pytest.fail("Pandas not installed")

def test_numpy_import():
    """Verify numpy can be imported."""
    try:
        import numpy
    except ImportError:
        pytest.fail("NumPy not installed")

def test_requests_import():
    """Verify requests can be imported."""
    try:
        import requests
    except ImportError:
        pytest.fail("Requests not installed")

def test_datasets_import():
    """Verify datasets can be imported."""
    try:
        import datasets
    except ImportError:
        pytest.fail("Datasets not installed")

def test_requirements_file_exists():
    """Verify requirements.txt exists in code directory."""
    from pathlib import Path
    # Check relative to test location (code/tests/unit/) -> ../../requirements.txt
    req_path = Path(__file__).parent.parent.parent / 'requirements.txt'
    assert req_path.exists(), f"requirements.txt not found at {req_path}"