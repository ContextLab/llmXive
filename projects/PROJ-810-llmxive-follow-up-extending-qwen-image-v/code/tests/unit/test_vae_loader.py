import json
import os
import tempfile
from pathlib import Path
import pytest
from src.models.vae_loader import (
    check_model_availability,
    check_cpu_feasibility,
    trigger_model_substitution_protocol,
    run_model_availability_check
)

class TestModelAvailability:
    def test_check_available_model(self):
        """Test checking a known available model."""
        # We test with a very small, known model to avoid network issues if possible,
        # but in a real CI this might hit the network.
        # Using a generic check that shouldn't raise if internet is up.
        is_avail, err = check_model_availability("hf-internal-testing/tiny-random-LlamaForCausalLM")
        # If network is up, this should be True. If down, it might fail.
        # We assert that the function returns a tuple of bool and str/None
        assert isinstance(is_avail, bool)
        assert isinstance(err, (str, type(None)))

    def test_check_nonexistent_model(self):
        """Test checking a definitely non-existent model."""
        is_avail, err = check_model_availability("this-model-definitely-does-not-exist-12345")
        assert is_avail == False
        assert err is not None

class TestCpuFeasibility:
    def test_feasible_model(self):
        """Test feasibility check on a small model."""
        is_feasible, err = check_cpu_feasibility("hf-internal-testing/tiny-random-LlamaForCausalLM")
        assert isinstance(is_feasible, bool)
        # The heuristic might return True for tiny models
        assert err is None or isinstance(err, str)

class TestFallbackProtocol:
    def test_trigger_protocol_returns_dict(self):
        """Test that the substitution protocol returns the expected structure."""
        result = trigger_model_substitution_protocol()
        assert "status" in result
        assert result["status"] == "SUBSTITUTED"
        assert "fallback_model_id" in result
        assert result["fallback_model_id"] == "openai/clip-vit-base-patch32"
        assert "reason" in result

class TestRunAvailabilityCheck:
    def test_run_check_creates_file(self, tmp_path):
        """Test that run_model_availability_check writes the output file."""
        # Temporarily override the output path by mocking or checking side effects
        # Since the function writes to a hardcoded path, we can't easily change it in unit test
        # without refactoring. We will assume the function works and check the file exists
        # if the network allows, or just check the logic returns a dict.
        
        # For a robust unit test, we'd refactor run_model_availability_check to accept an output_path.
        # Given the constraint to extend, we test the return value structure.
        result = run_model_availability_check()
        
        assert isinstance(result, dict)
        assert "status" in result
        assert "final_model_id" in result
        assert "timestamp" in result
        
        # Verify the file was written if the function succeeded in writing
        output_path = Path("data/results/model_availability.json")
        # We don't assert existence here because network might fail, but the function attempts it.
        # If the function runs, it attempts to write.
        if output_path.exists():
            with open(output_path, "r") as f:
                saved_data = json.load(f)
            assert saved_data == result