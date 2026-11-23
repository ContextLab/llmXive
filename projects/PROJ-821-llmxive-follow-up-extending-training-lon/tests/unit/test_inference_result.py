"""Unit tests for the InferenceResult entity."""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.inference.inference_result import InferenceResult


class TestInferenceResult:
    """Test cases for InferenceResult dataclass."""

    def test_creation(self):
        """Test that InferenceResult can be instantiated with correct attributes."""
        result = InferenceResult(
            sample_id="s1",
            retrieved_value="val",
            is_correct=True,
            inference_time_ms=100.0,
            peak_memory_mb=512.0
        )
        assert result.sample_id == "s1"
        assert result.retrieved_value == "val"
        assert result.is_correct is True
        assert result.inference_time_ms == 100.0
        assert result.peak_memory_mb == 512.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = InferenceResult(
            sample_id="s2",
            retrieved_value="test",
            is_correct=False,
            inference_time_ms=200.5,
            peak_memory_mb=1024.5
        )
        d = result.to_dict()
        assert d["sample_id"] == "s2"
        assert d["is_correct"] is False
        assert d["inference_time_ms"] == 200.5

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "sample_id": "s3",
            "retrieved_value": "needle",
            "is_correct": True,
            "inference_time_ms": 300.0,
            "peak_memory_mb": 2048.0
        }
        result = InferenceResult.from_dict(data)
        assert result.sample_id == "s3"
        assert result.is_correct is True

    def test_serialization_roundtrip(self):
        """Test JSON serialization and deserialization."""
        original = InferenceResult(
            sample_id="s4",
            retrieved_value="data",
            is_correct=True,
            inference_time_ms=123.45,
            peak_memory_mb=768.12
        )
        json_str = original.to_json()
        restored = InferenceResult.from_json(json_str)
        
        assert restored.sample_id == original.sample_id
        assert restored.retrieved_value == original.retrieved_value
        assert restored.is_correct == original.is_correct
        assert abs(restored.inference_time_ms - original.inference_time_ms) < 0.01
        assert abs(restored.peak_memory_mb - original.peak_memory_mb) < 0.01

    def test_save_and_load_jsonl(self):
        """Test saving to and loading from a JSONL file."""
        result = InferenceResult(
            sample_id="s5",
            retrieved_value="save_test",
            is_correct=False,
            inference_time_ms=50.0,
            peak_memory_mb=256.0
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "results.jsonl"
            
            # Save
            result.save_to_file(file_path)
            assert file_path.exists()

            # Load and verify
            with open(file_path, "r") as f:
                line = f.readline()
                loaded = InferenceResult.from_json(line)
            
            assert loaded.sample_id == result.sample_id
            assert loaded.is_correct == result.is_correct

    def test_repr(self):
        """Test string representation."""
        result = InferenceResult(
            sample_id="s6",
            retrieved_value="repr_test",
            is_correct=True,
            inference_time_ms=10.0,
            peak_memory_mb=100.0
        )
        rep = repr(result)
        assert "s6" in rep
        assert "True" in rep
        assert "10.0" in rep
        assert "100.0" in rep

    def test_invalid_dict_key(self):
        """Test that missing keys raise an error during from_dict."""
        data = {
            "sample_id": "s7",
            "retrieved_value": "val",
            # Missing is_correct
            "inference_time_ms": 100.0,
            "peak_memory_mb": 100.0
        }
        with pytest.raises(KeyError):
            InferenceResult.from_dict(data)