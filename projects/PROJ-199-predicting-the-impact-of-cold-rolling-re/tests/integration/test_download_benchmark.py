"""
Integration test for T018c: Download and verify benchmark dataset.

This test ensures that the benchmark dataset is correctly generated/ downloaded,
saved to the expected location, and contains the required fields.
"""
import os
import sys
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download_benchmark import download_or_generate_benchmark, BENCHMARK_OUTPUT_PATH
from data.generate_benchmark import validate_benchmark_data

REQUIRED_FIELDS = {"Material", "Reduction", "Brass", "Copper", "S", "Goss"}

@pytest.fixture
def temp_output_path():
    """Create a temporary file path for testing to avoid polluting the real data directory."""
    temp_dir = Path(tempfile.mkdtemp())
    path = temp_dir / "test_benchmark_data.json"
    yield path
    shutil.rmtree(temp_dir)

def test_benchmark_generation_structure(temp_output_path):
    """Test that the benchmark data generation produces the correct structure."""
    # Mock the path for the test
    import data.download_benchmark as mod
    original_path = mod.BENCHMARK_OUTPUT_PATH
    mod.BENCHMARK_OUTPUT_PATH = temp_output_path

    try:
        success = download_or_generate_benchmark()
        assert success, "Benchmark generation/download failed."
        assert temp_output_path.exists(), "Benchmark file was not created."

        # Load and verify content
        with open(temp_output_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), "Benchmark data must be a list of samples."
        assert len(data) > 0, "Benchmark data must not be empty."

        # Check fields in first sample
        first_sample = data[0]
        assert isinstance(first_sample, dict), "Each sample must be a dictionary."
        assert REQUIRED_FIELDS.issubset(set(first_sample.keys())), \
            f"Missing required fields. Expected: {REQUIRED_FIELDS}, Found: {set(first_sample.keys())}"

        # Validate using the project's validation function
        assert validate_benchmark_data(temp_output_path), "Validation function returned False."

    finally:
        # Restore original path
        mod.BENCHMARK_OUTPUT_PATH = original_path

def test_benchmark_data_values():
    """Test that the generated benchmark data contains realistic values."""
    # Ensure the real benchmark file exists (from previous successful run or generation)
    if not BENCHMARK_OUTPUT_PATH.exists():
        # If it doesn't exist, run the generation first
        assert download_or_generate_benchmark(), "Failed to generate benchmark data for test."

    with open(BENCHMARK_OUTPUT_PATH, 'r') as f:
        data = json.load(f)

    for sample in data:
        # Check materials
        assert sample["Material"] in ["Al", "Cu", "Ni"], f"Invalid material: {sample['Material']}"

        # Check reduction is numeric
        assert isinstance(sample["Reduction"], (int, float)), f"Reduction must be numeric: {sample['Reduction']}"

        # Check volume fractions are between 0 and 1
        for comp in ["Brass", "Copper", "S", "Goss"]:
            val = sample[comp]
            assert isinstance(val, (int, float)), f"{comp} must be numeric: {val}"
            assert 0.0 <= val <= 1.0, f"{comp} value {val} out of range [0, 1]"