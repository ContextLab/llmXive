"""
Unit tests for static NCQ generation logic in base_zppo.py.

This module verifies that the static Negative Candidate-included Question (NCQ)
generation correctly includes all known failure modes for every step as defined
in the User Story 1 specification.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.loops.base_zppo import generate_static_ncq_prompt, StaticNCQGenerator
from code.config import get_config


class TestStaticNCQGeneration:
    """Test cases for static NCQ generation logic."""

    @pytest.fixture
    def sample_failure_modes(self):
        """Provide a list of sample failure modes for testing."""
        return [
            {"mode": "hallucination", "description": "Model invents facts"},
            {"mode": "logic_error", "description": "Incorrect deduction"},
            {"mode": "knowledge_gap", "description": "Missing domain knowledge"},
            {"mode": "attention_drift", "description": "Loses context focus"},
            {"mode": "confidence_mismatch", "description": "Over/under confident"}
        ]

    @pytest.fixture
    def sample_question(self):
        """Provide a sample question string."""
        return "What is the capital of France?"

    def test_generate_static_ncq_prompt_includes_all_modes(
        self, sample_failure_modes, sample_question
    ):
        """
        Verify that generate_static_ncq_prompt includes ALL provided failure modes
        in the resulting prompt string.
        """
        prompt = generate_static_ncq_prompt(sample_question, sample_failure_modes)

        assert isinstance(prompt, str)
        assert len(prompt) > 0

        # Check that the question is present
        assert sample_question in prompt

        # Check that every failure mode is present
        for mode_entry in sample_failure_modes:
            mode_str = mode_entry["mode"]
            desc_str = mode_entry["description"]
            assert mode_str in prompt, f"Failure mode '{mode_str}' missing from prompt"
            assert desc_str in prompt, f"Description '{desc_str}' missing from prompt"

    def test_static_ncq_generator_initialization(self):
        """
        Verify that StaticNCQGenerator initializes correctly with config and
        failure mode definitions.
        """
        config = get_config()
        generator = StaticNCQGenerator(config)

        assert generator.config is not None
        assert hasattr(generator, "failure_modes")
        assert hasattr(generator, "generate_prompt")

    def test_static_ncq_generator_output_consistency(
        self, sample_failure_modes, sample_question
    ):
        """
        Verify that the generator produces consistent output for the same inputs
        (deterministic behavior).
        """
        config = get_config()
        generator = StaticNCQGenerator(config)

        prompt1 = generator.generate_prompt(sample_question, sample_failure_modes)
        prompt2 = generator.generate_prompt(sample_question, sample_failure_modes)

        assert prompt1 == prompt2, "Static NCQ generation is not deterministic"

    def test_static_ncq_prompt_format_structure(
        self, sample_failure_modes, sample_question
    ):
        """
        Verify that the generated prompt follows the expected structural format:
        1. Contains the question
        2. Contains a section for negative candidates/failure modes
        3. Contains instructions for the student model
        """
        prompt = generate_static_ncq_prompt(sample_question, sample_failure_modes)

        # Basic structural checks
        assert "Question:" in prompt or sample_question in prompt
        assert "Negative Candidates" in prompt or "Failure Modes" in prompt
        assert "Student" in prompt or "Instruction" in prompt

    def test_empty_failure_modes_handling(self, sample_question):
        """
        Verify behavior when no failure modes are provided (edge case).
        The prompt should still be generated but without failure mode content.
        """
        prompt = generate_static_ncq_prompt(sample_question, [])

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert sample_question in prompt
        # Should not contain failure mode specific content
        assert "Negative Candidates" not in prompt or "No candidates" in prompt.lower()

    def test_large_failure_modes_list(self, sample_question):
        """
        Verify handling of a large list of failure modes to ensure scalability.
        """
        large_modes = [
            {"mode": f"mode_{i}", "description": f"Description for mode {i}"}
            for i in range(50)
        ]
        prompt = generate_static_ncq_prompt(sample_question, large_modes)

        assert isinstance(prompt, str)
        assert len(prompt) > 1000  # Should be substantial

        for mode_entry in large_modes:
            assert mode_entry["mode"] in prompt
            assert mode_entry["description"] in prompt

    def test_special_characters_in_failure_modes(self, sample_question):
        """
        Verify that special characters in failure modes do not break the prompt.
        """
        special_modes = [
            {"mode": "mode_&<>'\"", "description": "Test with <special> chars"},
            {"mode": "newline_mode", "description": "Test\nwith\nnewlines"},
            {"mode": "unicode_mode", "description": "Test with unicode: café, 日本語"}
        ]

        prompt = generate_static_ncq_prompt(sample_question, special_modes)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Basic sanity check that prompt is not empty or broken
        assert "Question" in prompt or sample_question in prompt

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
