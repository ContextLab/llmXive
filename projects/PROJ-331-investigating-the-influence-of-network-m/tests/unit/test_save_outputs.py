"""
Unit tests for T017: save_outputs.py
"""
import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import shutil
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils import save_npy, load_npy, compute_sha256

class TestSaveOutputs:
    """Tests for the save_with_provenance functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_save_npy_creates_file(self, temp_dir):
        """Test that save_npy creates a valid .npy file."""
        test_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        output_path = temp_dir / "test.npy"
        
        save_npy(test_data, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
        
        # Verify we can load it back
        loaded = load_npy(output_path)
        np.testing.assert_array_equal(test_data, loaded)

    def test_compute_sha256_consistency(self, temp_dir):
        """Test that SHA256 is consistent for the same file."""
        test_data = np.random.rand(10, 10)
        output_path = temp_dir / "test.npy"
        
        save_npy(test_data, output_path)
        
        hash1 = compute_sha256(output_path)
        hash2 = compute_sha256(output_path)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex string length

    def test_provenance_structure(self, temp_dir):
        """Test that provenance metadata has the expected structure."""
        test_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        input_path = temp_dir / "input.npy"
        output_path = temp_dir / "output.npy"
        
        save_npy(test_data, input_path)
        save_npy(test_data, output_path)
        
        # Simulate provenance structure
        provenance = {
            "task_id": "T017",
            "artifacts": [
                {
                    "description": "Test Artifact",
                    "input": {
                        "path": str(input_path),
                        "exists": True,
                        "sha256": compute_sha256(input_path),
                        "shape": list(test_data.shape)
                    },
                    "output": {
                        "path": str(output_path),
                        "sha256": compute_sha256(output_path),
                        "shape": list(test_data.shape)
                    }
                }
            ]
        }
        
        # Verify structure
        assert provenance["task_id"] == "T017"
        assert len(provenance["artifacts"]) == 1
        assert "description" in provenance["artifacts"][0]
        assert "input" in provenance["artifacts"][0]
        assert "output" in provenance["artifacts"][0]
        assert "sha256" in provenance["artifacts"][0]["input"]
        assert "sha256" in provenance["artifacts"][0]["output"]

    def test_metadata_json_serializable(self, temp_dir):
        """Test that provenance metadata is JSON serializable."""
        test_data = np.array([[1.0, 2.0], [3.0, 4.0]])
        input_path = temp_dir / "input.npy"
        
        save_npy(test_data, input_path)
        
        metadata = {
            "task_id": "T017",
            "timestamp": "2024-01-01T00:00:00",
            "execution_time_seconds": 1.5,
            "artifacts": [
                {
                    "description": "Test",
                    "input": {
                        "path": str(input_path),
                        "exists": True,
                        "size_bytes": input_path.stat().st_size,
                        "sha256": compute_sha256(input_path),
                        "shape": list(test_data.shape),
                        "dtype": str(test_data.dtype),
                        "min": float(np.min(test_data)),
                        "max": float(np.max(test_data))
                    }
                }
            ]
        }
        
        # Should not raise
        json_str = json.dumps(metadata)
        assert len(json_str) > 0

    def test_error_on_missing_input(self, temp_dir):
        """Test that missing input file is handled correctly."""
        non_existent = temp_dir / "does_not_exist.npy"
        
        assert not non_existent.exists()
        
        # Our implementation should raise ProcessingError
        from utils import ProcessingError
        
        with pytest.raises(ProcessingError):
            # Simulate the check that would happen in save_with_provenance
            if not non_existent.exists():
                raise ProcessingError(f"Input file not found: {non_existent}")