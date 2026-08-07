"""
Unit tests for T002: Verify CPU-only dependencies are installed and working.
"""
import pytest
import sys
import importlib

def test_torch_cpu_only():
    """Test that PyTorch is available and running on CPU."""
    torch = importlib.import_module('torch')
    
    # Check CUDA availability
    assert not torch.cuda.is_available(), "CUDA should not be available in this CPU-only environment."
    
    # Test basic CPU tensor creation
    x = torch.zeros(1, 1, device='cpu')
    assert x.device.type == 'cpu', "Tensor should be on CPU device."

def test_pybullet_import():
    """Test that PyBullet can be imported."""
    pybullet = importlib.import_module('pybullet')
    assert pybullet is not None, "PyBullet module should be importable."

def test_mujoco_import():
    """Test that MuJoCo can be imported."""
    mujoco = importlib.import_module('mujoco')
    assert mujoco is not None, "MuJoCo module should be importable."

def test_diffusers_import():
    """Test that Diffusers can be imported."""
    diffusers = importlib.import_module('diffusers')
    assert diffusers is not None, "Diffusers module should be importable."

def test_transformers_import():
    """Test that Transformers can be imported."""
    transformers = importlib.import_module('transformers')
    assert transformers is not None, "Transformers module should be importable."

def test_sklearn_import():
    """Test that Scikit-learn can be imported."""
    sklearn = importlib.import_module('sklearn')
    assert sklearn is not None, "Scikit-learn module should be importable."

def test_opencv_import():
    """Test that OpenCV can be imported."""
    cv2 = importlib.import_module('cv2')
    assert cv2 is not None, "OpenCV module should be importable."

def test_pandas_import():
    """Test that Pandas can be imported."""
    pandas = importlib.import_module('pandas')
    assert pandas is not None, "Pandas module should be importable."

def test_numpy_import():
    """Test that NumPy can be imported."""
    numpy = importlib.import_module('numpy')
    assert numpy is not None, "NumPy module should be importable."

def test_requests_import():
    """Test that Requests can be imported."""
    requests = importlib.import_module('requests')
    assert requests is not None, "Requests module should be importable."

def test_datasets_import():
    """Test that HuggingFace Datasets can be imported."""
    datasets = importlib.import_module('datasets')
    assert datasets is not None, "Datasets module should be importable."

def test_requirements_file_exists():
    """Test that requirements.txt exists in the code directory."""
    import os
    code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    requirements_path = os.path.join(code_dir, 'requirements.txt')
    assert os.path.exists(requirements_path), "requirements.txt should exist in the code directory."