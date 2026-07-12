"""
Unit tests for the seeds.py module.

Tests verify that:
1. Global seeds are set correctly.
2. Deterministic behavior is achieved across runs.
3. Task-specific seeds are generated correctly.
"""
import os
import random
import numpy as np

# Mock torch and cv2 if not available to prevent import errors in test env
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Mock torch for testing
    class MockTorch:
        def manual_seed(self, x): pass
        def cuda_manual_seed_all(self, x): pass
        class backends:
            class cudnn:
                deterministic = False
                benchmark = False
            class mkl:
                @staticmethod
                def is_available(): return False
    torch = MockTorch()

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    # Mock cv2
    class MockCv2:
        @staticmethod
        def setNumThreads(x): pass
    cv2 = MockCv2()

import pytest
from utils.seeds import set_global_seed, generate_seed_from_hash, set_seed_for_task

def test_set_global_seed_sets_python_seed():
    set_global_seed(123)
    assert random.randint(0, 1000) == random.randint(0, 1000)  # Should be same if reset
    
    # Reset and check again
    random.seed(123)
    val1 = random.randint(0, 1000)
    random.seed(123)
    val2 = random.randint(0, 1000)
    assert val1 == val2

def test_set_global_seed_sets_numpy_seed():
    set_global_seed(456)
    arr1 = np.random.rand(5)
    np.random.seed(456)
    arr2 = np.random.rand(5)
    assert np.array_equal(arr1, arr2)

def test_generate_seed_from_hash():
    seed1 = generate_seed_from_hash("task_a")
    seed2 = generate_seed_from_hash("task_a")
    seed3 = generate_seed_from_hash("task_b")
    
    assert seed1 == seed2
    assert seed1 != seed3
    assert isinstance(seed1, int)

def test_set_seed_for_task():
    seed = set_seed_for_task("test_task", base_seed=999)
    assert isinstance(seed, int)
    assert seed > 0

def test_environment_variable_set():
    set_global_seed(789)
    assert os.environ.get('PYTHONHASHSEED') == '789'