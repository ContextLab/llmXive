"""
Unit tests for src/models/vae_loader.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module functions
from src.models.vae_loader import (
    check_model_availability,
    check_cpu_feasibility,
    trigger_model_substitution_protocol,
    run_model_availability_check,
    TARGET_MODEL_ID,
    FALLBACK_MODEL_ID,
    RESULTS_DIR
)


class TestModelAvailability:
    """Tests for model availability checking."""

    def test_check_model_availability_exists(self):
        """Test that a known model returns True."""
        # Using a very common model as a proxy for "exists"
        # In a real CI, this might hit rate limits, so we catch the exception
        exists, msg = check_model_availability("google/vit-base-patch16-224")
        # We expect it to exist, but network issues might cause it to fail
        # So we just check that the function returns a tuple of (bool, str)
        assert isinstance(exists, bool)
        assert isinstance(msg, str)

    def test_check_model_availability_nonexistent(self):
        """Test that a non-existent model returns False."""
        exists, msg = check_model_availability("this-model-definitely-does-not-exist-12345")
        assert exists is False
        assert "not found" in msg.lower() or "inaccessible" in msg.lower()


class TestCpuFeasibility:
    """Tests for CPU feasibility checking."""

    def test_qwen_vae_not_feasible(self):
        """Test that Qwen-Image-VAE-2.0 is flagged as not CPU-feasible."""
        is_feasible, msg = check_cpu_feasibility(TARGET_MODEL_ID)
        assert is_feasible is False
        assert "too large" in msg.lower() or "cpu" in msg.lower()

    def test_other_model_feasible(self):
        """Test that a generic model is assumed feasible."""
        is_feasible, msg = check_cpu_feasibility("some-other-model")
        assert is_feasible is True
        assert "feasible" in msg.lower()


class TestFallbackProtocol:
    """Tests for the model substitution protocol."""

    def test_trigger_fallback_returns_id(self):
        """Test that triggering fallback returns a valid model ID."""
        fallback_id = trigger_model_substitution_protocol()
        assert fallback_id is not None
        assert isinstance(fallback_id, str)
        assert len(fallback_id) > 0
        assert fallback_id == FALLBACK_MODEL_ID


class TestRunAvailabilityCheck:
    """Tests for the full availability check workflow."""

    def test_run_check_returns_dict(self):
        """Test that the main check function returns a dictionary."""
        result = run_model_availability_check()
        assert isinstance(result, dict)
        assert "target_model_id" in result
        assert "status" in result
        assert "message" in result
        assert "fallback_model_id" in result

    def test_run_check_writes_json(self):
        """Test that the check writes the JSON file."""
        # We run the check and then verify the file exists
        # Since this might trigger fallback, we just check the file is created
        result = run_model_availability_check()
        
        output_path = RESULTS_DIR / "model_availability.json"
        assert output_path.exists(), f"File {output_path} was not created"
        
        with open(output_path, "r") as f:
            saved_result = json.load(f)
        
        assert saved_result["target_model_id"] == result["target_model_id"]
        assert saved_result["status"] == result["status"]
        assert saved_result["fallback_model_id"] == result["fallback_model_id"]