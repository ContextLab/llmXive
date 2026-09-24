"""
Unit tests for T037b: Synthetic Unit-Test Dataset Generator
"""
import os
import tempfile
import pytest
from pathlib import Path
import subprocess
import sys

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_synthetic_dataset_generation(temp_output_dir):
    """Test that synthetic dataset generation produces expected output."""
    output_file = temp_output_dir / "mock_oxford_pets.parquet"
    
    # Run the synthetic dataset generator
    cmd = [
        sys.executable,
        "code/synthetic_unit_test_dataset.py",
        "--n-samples", "10",
        "--seed", "42",
        "--output", str(output_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check that the command succeeded
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    # Check that the output file was created
    assert output_file.exists(), f"Output file not created: {output_file}"
    
    # Check file is not empty
    assert output_file.stat().st_size > 0, "Output file is empty"

def test_synthetic_dataset_with_default_args(temp_output_dir):
    """Test synthetic dataset generation with default arguments."""
    output_file = temp_output_dir / "default_mock.parquet"
    
    # Run with minimal arguments (should use defaults)
    cmd = [
        sys.executable,
        "code/synthetic_unit_test_dataset.py",
        "--output", str(output_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert output_file.exists(), "Output file not created with default args"
    assert output_file.stat().st_size > 0, "Output file is empty with default args"

def test_synthetic_dataset_seed_reproducibility(temp_output_dir):
    """Test that same seed produces same output."""
    output_file_1 = temp_output_dir / "mock_1.parquet"
    output_file_2 = temp_output_dir / "mock_2.parquet"
    
    # Generate two datasets with same seed
    cmd1 = [
        sys.executable,
        "code/synthetic_unit_test_dataset.py",
        "--n-samples", "5",
        "--seed", "123",
        "--output", str(output_file_1)
    ]
    
    cmd2 = [
        sys.executable,
        "code/synthetic_unit_test_dataset.py",
        "--n-samples", "5",
        "--seed", "123",
        "--output", str(output_file_2)
    ]
    
    subprocess.run(cmd1, check=True)
    subprocess.run(cmd2, check=True)
    
    # Read and compare file contents
    with open(output_file_1, "rb") as f1, open(output_file_2, "rb") as f2:
        content1 = f1.read()
        content2 = f2.read()
        
    assert content1 == content2, "Same seed should produce identical output"

def test_synthetic_dataset_different_seeds(temp_output_dir):
    """Test that different seeds produce different output."""
    output_file_1 = temp_output_dir / "mock_seed1.parquet"
    output_file_2 = temp_output_dir / "mock_seed2.parquet"
    
    # Generate two datasets with different seeds
    cmd1 = [
        sys.executable,
        "code/synthetic_unit_test_dataset.py",
        "--n-samples", "5",
        "--seed", "100",
        "--output", str(output_file_1)
    ]
    
    cmd2 = [
        sys.executable,
        "code/synthetic_unit_test_dataset.py",
        "--n-samples", "5",
        "--seed", "200",
        "--output", str(output_file_2)
    ]
    
    subprocess.run(cmd1, check=True)
    subprocess.run(cmd2, check=True)
    
    # Read and compare file contents
    with open(output_file_1, "rb") as f1, open(output_file_2, "rb") as f2:
        content1 = f1.read()
        content2 = f2.read()
        
    assert content1 != content2, "Different seeds should produce different output"
