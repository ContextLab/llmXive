"""
Contract test for correlation output schema.

Validates the structure of correlation results.
"""
import os
import json
import pytest

def test_correlation_output_exists():
    """Test that correlation output file exists."""
    output_path = "data/results/correlation_matrix.json"
    assert os.path.exists(output_path), f"Output file not found: {output_path}"

def test_correlation_output_structure():
    """Test that correlation output has required structure."""
    output_path = "data/results/correlation_matrix.json"
    
    with open(output_path, 'r') as f:
        results = json.load(f)
    
    assert isinstance(results, list), "Output must be a list"
    
    if len(results) > 0:
        required_fields = ["predictor", "outcome", "correlation", "p_value", "method"]
        for field in required_fields:
            assert field in results[0], f"Missing required field: {field}"
