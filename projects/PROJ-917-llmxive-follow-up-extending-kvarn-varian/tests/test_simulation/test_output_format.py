"""
Unit tests for simulation output format validation.
"""
import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_json_output_valid():
    """
    Test that a valid JSON output can be parsed and contains required fields.
    """
    valid_json = """
    {
        "run_id": "run_001",
        "steps": 1000,
        "accumulated_kl": 5.23,
        "average_kl_per_step": 0.00523,
        "method": "sinkhorn",
        "latency_ms": 12.5
    }
    """
    
    data = json.loads(valid_json)
    assert "run_id" in data
    assert "accumulated_kl" in data
    assert isinstance(data["accumulated_kl"], float)
    assert data["steps"] > 0
