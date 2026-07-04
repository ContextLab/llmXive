import pytest
import numpy as np
import os
import tempfile
import struct
from pathlib import Path
from decimal import Decimal, getcontext

# Import the functions to test
from benchmarks.reference import (
    decimal_matmul,
    decimal_softmax,
    decimal_layernorm,
    generate_reference_tensor,
    save_tensor_to_binary,
    run_reference_benchmarks
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_decimal_matmul_basic():
    """Test basic matrix multiplication with decimal precision."""
    # Create simple test matrices
    A = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    B = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    
    result = decimal_matmul(A, B)
    
    # Expected result: [[19.0, 22.0], [43.0, 50.0]]
    expected = np.array([[19.0, 22.0], [43.0, 50.0]], dtype=np.float32)
    
    np.testing.assert_array_almost_equal(result, expected, decimal=5)

def test_decimal_softmax_basic():
    """Test basic softmax with decimal precision."""
    X = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
    
    result = decimal_softmax(X)
    
    # Softmax should sum to 1.0
    assert np.abs(np.sum(result) - 1.0) < 1e-5
    
    # Values should be positive
    assert np.all(result > 0)

def test_decimal_layernorm_basic():
    """Test basic layer normalization with decimal precision."""
    X = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32)
    gamma = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    beta = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    
    result = decimal_layernorm(X, gamma, beta)
    
    # Mean of each row should be 0 (approximately)
    # Due to normalization
    for i in range(X.shape[0]):
        row_mean = np.mean(result[i])
        assert np.abs(row_mean) < 1e-3

def test_save_and_load_tensor(temp_dir):
    """Test saving and loading tensors."""
    tensor = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    output_path = os.path.join(temp_dir, 'test_tensor.bin')
    
    save_tensor_to_binary(tensor, output_path, 'matmul')
    
    assert os.path.exists(output_path)
    
    # Verify file size (header + data)
    file_size = os.path.getsize(output_path)
    expected_size = 3 * 4 + 4 * 4  # 3 ints header + 4 floats
    assert file_size == expected_size

def test_generate_reference_tensor_matmul(temp_dir):
    """Test generating reference tensor for matmul."""
    # Create input files
    input_path = os.path.join(temp_dir, 'input')
    os.makedirs(input_path)
    
    # Create A and B matrices
    A = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    B = np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)
    
    # Save as binary
    n, k = A.shape
    m = B.shape[1]
    
    # Create header: N, K, M
    header = struct.pack('iii', n, k, m)
    
    with open(os.path.join(input_path, 'test_matmul.bin'), 'wb') as f:
        f.write(header)
        f.write(A.tobytes())
        f.write(B.tobytes())
    
    # Generate reference
    result = generate_reference_tensor(os.path.join(input_path, 'test_matmul.bin'), 'matmul')
    
    # Verify dimensions
    assert result.shape == (n, m)
    
    # Verify values (approximately)
    expected = np.array([[19.0, 22.0], [43.0, 50.0]], dtype=np.float32)
    np.testing.assert_array_almost_equal(result, expected, decimal=5)

def test_run_reference_benchmarks(temp_dir):
    """Test running full reference benchmarks."""
    input_path = os.path.join(temp_dir, 'input')
    output_path = os.path.join(temp_dir, 'output')
    os.makedirs(input_path)
    os.makedirs(output_path)
    
    # Create a simple matmul input
    A = np.array([[1.0, 2.0]], dtype=np.float32)
    B = np.array([[3.0], [4.0]], dtype=np.float32)
    
    n, k = A.shape
    m = B.shape[1]
    header = struct.pack('iii', n, k, m)
    
    with open(os.path.join(input_path, 'test_matmul.bin'), 'wb') as f:
        f.write(header)
        f.write(A.tobytes())
        f.write(B.tobytes())
    
    # Create config
    configs = [
        {
            'config_id': 'test_matmul',
            'kernel_type': 'matmul',
            'tensor_file': 'test_matmul.bin'
        }
    ]
    
    # Run benchmarks
    run_reference_benchmarks(input_path, output_path, configs)
    
    # Verify output
    output_file = os.path.join(output_path, 'test_matmul_reference.bin')
    assert os.path.exists(output_file)

def test_decimal_precision():
    """Test that decimal precision is set correctly."""
    from decimal import getcontext
    # The reference module should have set precision to 154 (512 bits)
    assert getcontext().prec >= 150