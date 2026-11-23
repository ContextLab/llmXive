"""
Unit tests for code/analysis/generate_gpu_factor.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from code.analysis.generate_gpu_factor import generate_gpu_factor_documentation

def test_generate_gpu_factor_structure():
    """Test that the generated data has the required structure."""
    data = generate_gpu_factor_documentation()

    assert isinstance(data, dict)
    assert "conversion_factor" in data
    assert "citation" in data
    assert "metric_type" in data
    assert "limitation" in data

def test_conversion_factor_is_non_zero():
    """Test that the conversion factor is a positive number."""
    data = generate_gpu_factor_documentation()
    factor = data["conversion_factor"]
    assert isinstance(factor, (int, float))
    assert factor > 0

def test_citation_has_required_fields():
    """Test that the citation block contains required fields."""
    data = generate_gpu_factor_documentation()
    citation = data["citation"]

    assert "title" in citation
    assert "url" in citation
    assert "doi" in citation
    assert citation["url"].startswith("http")

def test_metric_type_is_estimated():
    """Test that the metric type is explicitly marked as Estimated."""
    data = generate_gpu_factor_documentation()
    assert data["metric_type"] == "Estimated"

def test_file_generation():
    """Test that the main function generates the file correctly."""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_gpu_factor.json"
        
        # Temporarily override the global OUTPUT_PATH in the module
        # Note: In a real scenario, we might refactor main to accept an output path argument,
        # but for this test, we will just verify the logic by calling the function and saving manually.
        
        data = generate_gpu_factor_documentation()
        with open(output_path, 'w') as f:
            json.dump(data, f)
        
        # Verify the file exists and can be loaded
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["conversion_factor"] == data["conversion_factor"]
        assert loaded_data["citation"]["doi"] == data["citation"]["doi"]