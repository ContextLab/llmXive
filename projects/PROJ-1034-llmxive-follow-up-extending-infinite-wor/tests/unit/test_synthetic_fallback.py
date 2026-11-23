"""
Unit tests for the synthetic fallback mechanism (T015b).
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
# Assuming the project structure is src/data/synthetic_fallback.py
# and tests are at tests/unit/
import sys
from pathlib import Path

# Add parent directory to path to allow imports if running from tests/
# In a real environment, this should be handled by PYTHONPATH or setup.py
src_path = Path(__file__).resolve().parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from data.synthetic_fallback import generate_synthetic_fallback_dataset, flag_power_limited_status


class TestSyntheticFallback:
    """Tests for the fallback data generation logic."""

    def test_generates_valid_json_structure(self, tmp_path):
        """Test that the generated file is valid JSON with expected keys."""
        output_path = str(tmp_path / "test_fallback.json")
        
        result = generate_synthetic_fallback_dataset(output_path, steps=10)
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify JSON structure
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "records" in data
        assert data["metadata"]["source"] == "synthetic_fallback"
        assert data["metadata"]["power_limited"] is True
        assert len(data["records"]) == 10

    def test_records_have_required_fields(self, tmp_path):
        """Test that each record contains all required metric fields."""
        output_path = str(tmp_path / "test_fallback.json")
        
        generate_synthetic_fallback_dataset(output_path, steps=5)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        required_fields = [
            "time_step", "step_type", "model", 
            "coherence_score", "diversity_score", "step_latency",
            "physics_valid", "power_limited_flag"
        ]
        
        for record in data["records"]:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
            
            # Verify step_type is 'deferred'
            assert record["step_type"] == "deferred"
            
            # Verify power_limited_flag is True
            assert record["power_limited_flag"] is True

    def test_deterministic_with_seed(self, tmp_path):
        """Test that the same seed produces the same output."""
        output_path_1 = str(tmp_path / "test_fallback_1.json")
        output_path_2 = str(tmp_path / "test_fallback_2.json")
        
        seed = 12345
        
        generate_synthetic_fallback_dataset(output_path_1, steps=10, seed=seed)
        generate_synthetic_fallback_dataset(output_path_2, steps=10, seed=seed)
        
        with open(output_path_1, 'r') as f:
            data_1 = json.load(f)
        with open(output_path_2, 'r') as f:
            data_2 = json.load(f)
        
        # Compare first few records
        for r1, r2 in zip(data_1["records"], data_2["records"]):
            assert r1["coherence_score"] == r2["coherence_score"]
            assert r1["diversity_score"] == r2["diversity_score"]

    def test_flag_power_limited_updates_status(self, tmp_path):
        """Test that the status log is correctly updated."""
        status_path = str(tmp_path / "status.json")
        fallback_path = str(tmp_path / "fallback.json")
        
        # Create a dummy fallback file first
        generate_synthetic_fallback_dataset(fallback_path, steps=1)
        
        # Create an initial status log
        initial_status = {"status": "running", "timestamp": "2023-01-01T00:00:00"}
        with open(status_path, 'w') as f:
            json.dump(initial_status, f)
        
        # Apply the flag
        flag_power_limited_status(status_path, fallback_path)
        
        # Read and verify
        with open(status_path, 'r') as f:
            updated_status = json.load(f)
        
        assert updated_status["power_limited"] is True
        assert updated_status["status"] == "completed_fallback"
        assert updated_status["fallback_dataset_path"] == fallback_path
        assert "Power-Limited" in updated_status.get("message", "")

    def test_creates_directories_if_missing(self, tmp_path):
        """Test that the function creates necessary directories."""
        deep_path = str(tmp_path / "deep" / "nested" / "output.json")
        
        result = generate_synthetic_fallback_dataset(deep_path, steps=1)
        
        assert os.path.exists(deep_path)
        
        status_path = str(tmp_path / "deep" / "nested" / "status.json")
        flag_power_limited_status(status_path, deep_path)
        
        assert os.path.exists(status_path)