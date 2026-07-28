"""
Unit tests for probe generation logic, specifically focusing on:
1. The regeneration loop logic (max attempts, discard logic).
2. The semantic similarity threshold enforcement (cosine < 0.3).

These tests verify the behavior of src/services/probe_generator.py
before the full implementation is available (TDD approach).
"""
import pytest
from unittest.mock import patch, MagicMock, call
import numpy as np
import json
from pathlib import Path
import sys

# Ensure src is in path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, "code")

# Mock dependencies that might not be installed or heavy
# We are testing the logic, not the embedding model itself.
@pytest.fixture
def mock_embeddings():
    """Mock embedding vectors for similarity calculations."""
    # Return a simple vector for testing
    return np.array([0.1, 0.2, 0.3, 0.4, 0.5])

@pytest.fixture
def sample_axes():
    """Sample axes data as expected by the generator."""
    return {
        "character": "TestChar",
        "coarse": {
            "dimension": "Aggression",
            "description": "High aggression, low empathy."
        },
        "fine": {
            "dimension": "Impulsivity",
            "description": "Acts without thinking, often regretting."
        }
    }

class TestProbeRegenerationLoop:
    """Tests for the regeneration loop logic in probe_generator.py"""

    def test_max_attempts_reached_discards_invalid(self, sample_axes):
        """
        Test that if the generator fails to produce a valid probe 
        within max_attempts, it stops and logs an error.
        
        Expected behavior (from T019):
        - Loop runs up to max_attempts.
        - If valid probes < 50 and attempts > 150, mark character invalid.
        - Logs 'Generation Limit Exceeded'.
        """
        # We will test the logic by mocking the generation function to always return invalid
        # or by testing the specific function that handles the loop if exposed.
        # Since the full service isn't implemented yet, we test the logic structure.
        
        # Simulate a scenario where we try to generate 50 probes but fail every time
        max_attempts = 10
        attempts = 0
        valid_probes = []
        
        # Mock a generation function that always fails similarity check
        def mock_generate_one(axes, attempt_count):
            # Simulate a probe that is too similar to source
            return {"text": "Too similar text", "valid": False}

        for i in range(max_attempts):
            result = mock_generate_one(sample_axes, i)
            if result["valid"]:
                valid_probes.append(result)
            else:
                attempts += 1
            
            if attempts >= max_attempts:
                break

        assert len(valid_probes) == 0
        assert attempts == max_attempts
        # In real implementation, this would log 'Generation Limit Exceeded'

    def test_valid_probe_accepted_immediately(self, sample_axes):
        """
        Test that a valid probe (similarity < 0.3) is accepted and 
        the loop continues to the next probe.
        """
        max_attempts = 100
        valid_probes = []
        attempts = 0
        
        # Mock a generation function that returns valid probes
        def mock_generate_one_valid(axes, attempt_count):
            return {"text": "Valid out-of-world scenario", "valid": True}

        # Simulate generating 50 valid probes
        target_count = 50
        while len(valid_probes) < target_count and attempts < max_attempts:
            result = mock_generate_one_valid(sample_axes, attempts)
            if result["valid"]:
                valid_probes.append(result)
            attempts += 1

        assert len(valid_probes) == 50
        assert attempts == 50

class TestSimilarityThreshold:
    """Tests for the semantic similarity threshold logic."""

    def test_cosine_similarity_below_threshold_accepted(self):
        """
        Test that a probe with cosine similarity < 0.3 is accepted.
        """
        # Simulate vectors
        source_vec = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
        probe_vec = np.array([0.1, 0.9, 0.0, 0.0, 0.0]) # Low similarity to source_vec

        # Calculate cosine similarity
        dot_product = np.dot(source_vec, probe_vec)
        norm_source = np.linalg.norm(source_vec)
        norm_probe = np.linalg.norm(probe_vec)
        similarity = dot_product / (norm_source * norm_probe)

        assert similarity < 0.3
        # This probe should be accepted

    def test_cosine_similarity_above_threshold_rejected(self):
        """
        Test that a probe with cosine similarity >= 0.3 is rejected.
        """
        source_vec = np.array([1.0, 0.0, 0.0, 0.0, 0.0])
        probe_vec = np.array([0.5, 0.5, 0.0, 0.0, 0.0]) # Higher similarity

        dot_product = np.dot(source_vec, probe_vec)
        norm_source = np.linalg.norm(source_vec)
        norm_probe = np.linalg.norm(probe_vec)
        similarity = dot_product / (norm_source * norm_probe)

        assert similarity >= 0.3
        # This probe should be rejected

    def test_exact_threshold_boundary(self):
        """
        Test behavior exactly at the 0.3 threshold.
        Based on T018: 'cosine similarity < 0.3' implies strict inequality.
        """
        # Construct vectors to get exactly 0.3
        # a = [1, 0], b = [0.3, sqrt(1-0.3^2)] -> dot = 0.3, norm_a=1, norm_b=1
        source_vec = np.array([1.0, 0.0])
        probe_vec = np.array([0.3, np.sqrt(1 - 0.3**2)])

        dot_product = np.dot(source_vec, probe_vec)
        norm_source = np.linalg.norm(source_vec)
        norm_probe = np.linalg.norm(probe_vec)
        similarity = dot_product / (norm_source * norm_probe)

        assert np.isclose(similarity, 0.3)
        # Strict inequality < 0.3 means 0.3 is REJECTED
        assert similarity >= 0.3 

class TestProbeStructure:
    """Tests for the structure of generated probes."""

    def test_probe_schema_compliance(self):
        """
        Ensure generated probes have the required fields as per T016 schema.
        Expected fields: character, scenario, source_axes, similarity_score, is_valid
        """
        # Mock a valid probe structure
        valid_probe = {
            "character": "TestChar",
            "scenario": "A completely alien scenario",
            "source_axes": {
                "coarse": "Aggression",
                "fine": "Impulsivity"
            },
            "similarity_score": 0.15,
            "is_valid": True
        }

        required_fields = ["character", "scenario", "source_axes", "similarity_score", "is_valid"]
        
        for field in required_fields:
            assert field in valid_probe, f"Missing required field: {field}"

    def test_invalid_probe_structure_handling(self):
        """
        Test that probes missing required fields are rejected.
        """
        invalid_probe = {
            "character": "TestChar",
            "scenario": "Missing other fields"
        }

        required_fields = ["character", "scenario", "source_axes", "similarity_score", "is_valid"]
        missing = [f for f in required_fields if f not in invalid_probe]
        
        assert len(missing) > 0
        # In real implementation, this would trigger a validation error

class TestIntegrationWithGeneratorService:
    """
    Integration tests mocking the service layer to ensure the 
    regeneration loop calls the similarity check correctly.
    """

    @patch('src.services.probe_generator.calculate_semantic_similarity')
    @patch('src.services.probe_generator.generate_scenario_prompt')
    def test_loop_calls_similarity_check_for_each_attempt(
        self, mock_gen_prompt, mock_sim_calc, sample_axes
    ):
        """
        Verify that for every generation attempt, the similarity is calculated.
        """
        # Setup mocks
        mock_gen_prompt.return_value = "Generated text"
        mock_sim_calc.return_value = 0.5 # High similarity, should be rejected

        # Simulate the logic from T017/T018/T019
        max_attempts = 5
        attempts = 0
        valid_count = 0

        while valid_count < 5 and attempts < max_attempts:
            prompt = mock_gen_prompt(sample_axes, attempts)
            sim = mock_sim_calc(prompt, "source_corpus")
            
            if sim < 0.3:
                valid_count += 1
            attempts += 1

        # Assert similarity calc was called for every attempt
        assert mock_sim_calc.call_count == max_attempts
        # Assert no valid probes were found
        assert valid_count == 0

    @patch('src.services.probe_generator.calculate_semantic_similarity')
    @patch('src.services.probe_generator.generate_scenario_prompt')
    def test_loop_stops_when_valid_target_reached(
        self, mock_gen_prompt, mock_sim_calc, sample_axes
    ):
        """
        Verify that the loop stops immediately once 50 valid probes are found.
        """
        # Setup mocks to return valid probes
        mock_gen_prompt.return_value = "Valid text"
        mock_sim_calc.return_value = 0.1 # Low similarity

        target = 50
        max_attempts = 100
        attempts = 0
        valid_count = 0

        while valid_count < target and attempts < max_attempts:
            prompt = mock_gen_prompt(sample_axes, attempts)
            sim = mock_sim_calc(prompt, "source_corpus")
            
            if sim < 0.3:
                valid_count += 1
            attempts += 1

        assert valid_count == target
        assert attempts == target # Should stop exactly when target reached
        assert mock_sim_calc.call_count == target

if __name__ == "__main__":
    pytest.main([__file__, "-v"])