"""
Unit tests for static NCQ generation logic in base_zppo.py.

Tests the StaticNCQGenerator class to ensure:
1. Correct construction of NCQ prompts with negative candidates
2. Proper handling of candidate pools
3. Correct formatting of question, ground truth, and negative candidates
4. Edge cases (empty candidates, single candidate, etc.)
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from loops.base_zppo import StaticNCQGenerator
from data.generators import set_seed, get_seed


class TestStaticNCQGenerator:
    """Test suite for StaticNCQGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Initialize with deterministic seed for reproducibility
        set_seed(42)
        self.generator = StaticNCQGenerator()

    def test_initialization(self):
        """Test that StaticNCQGenerator initializes correctly."""
        assert self.generator is not None
        assert hasattr(self.generator, 'generate_ncq_prompt')

    def test_generate_ncq_prompt_basic(self):
        """Test basic NCQ prompt generation with standard inputs."""
        question = "What is the capital of France?"
        ground_truth = "Paris"
        negative_candidates = ["London", "Berlin", "Madrid"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        # Verify prompt contains all required elements
        assert question in prompt
        assert ground_truth in prompt
        assert "London" in prompt
        assert "Berlin" in prompt
        assert "Madrid" in prompt

        # Verify structure
        assert "Question:" in prompt
        assert "Ground Truth:" in prompt
        assert "Negative Candidates:" in prompt

    def test_generate_ncq_prompt_single_candidate(self):
        """Test NCQ generation with a single negative candidate."""
        question = "What is 2+2?"
        ground_truth = "4"
        negative_candidates = ["5"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        assert question in prompt
        assert ground_truth in prompt
        assert "5" in prompt
        assert "Negative Candidates:" in prompt

    def test_generate_ncq_prompt_empty_candidates(self):
        """Test NCQ generation with no negative candidates."""
        question = "What is the sky color?"
        ground_truth = "Blue"
        negative_candidates = []

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        assert question in prompt
        assert ground_truth in prompt
        # Should still have the section header even if empty
        assert "Negative Candidates:" in prompt
        # Should indicate empty or have appropriate placeholder
        assert "None" in prompt or "[]" in prompt

    def test_generate_ncq_prompt_many_candidates(self):
        """Test NCQ generation with many negative candidates."""
        question = "Which planet is closest to the Sun?"
        ground_truth = "Mercury"
        negative_candidates = [f"Planet_{i}" for i in range(50)]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        assert question in prompt
        assert ground_truth in prompt
        # Verify all candidates are present
        for candidate in negative_candidates:
            assert candidate in prompt

    def test_generate_ncq_prompt_format_consistency(self):
        """Test that prompt format is consistent across multiple generations."""
        question = "Test question"
        ground_truth = "Test answer"
        candidates = ["Wrong1", "Wrong2"]

        prompt1 = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )

        prompt2 = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )

        assert prompt1 == prompt2, "Prompt generation should be deterministic"

    def test_generate_ncq_prompt_special_characters(self):
        """Test NCQ generation with special characters in inputs."""
        question = "What is the value of π (pi)?"
        ground_truth = "3.14159"
        negative_candidates = ["2.718", "1.618", "0.577"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        assert "π" in prompt or "pi" in prompt
        assert "3.14159" in prompt
        assert "2.718" in prompt
        assert "1.618" in prompt
        assert "0.577" in prompt

    def test_generate_ncq_prompt_multiline_candidates(self):
        """Test NCQ generation with multiline negative candidates."""
        question = "Select the correct option"
        ground_truth = "Option A"
        negative_candidates = [
            "Option B\nwith extra line",
            "Option C\nAnother line",
            "Option D"
        ]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        assert question in prompt
        assert ground_truth in prompt
        # Verify multiline candidates are included
        assert "Option B" in prompt
        assert "with extra line" in prompt
        assert "Option C" in prompt

    def test_generate_ncq_prompt_candidate_ordering(self):
        """Test that candidate order is preserved in prompt."""
        question = "Which is correct?"
        ground_truth = "First"
        # Create candidates in specific order
        candidates = ["Third", "First", "Second", "Fourth"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )

        # Find positions of candidates in prompt
        positions = {c: prompt.find(c) for c in candidates}
        
        # Verify order is preserved (Third before First before Second before Fourth)
        assert positions["Third"] < positions["First"]
        assert positions["First"] < positions["Second"]
        assert positions["Second"] < positions["Fourth"]

    def test_generate_ncq_prompt_no_duplicates(self):
        """Test that duplicate candidates are handled appropriately."""
        question = "Which is correct?"
        ground_truth = "A"
        # Include duplicates
        candidates = ["B", "C", "B", "D", "C"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )

        # All candidates should appear (duplicates included as per input)
        assert candidates.count("B") == prompt.count("B")
        assert candidates.count("C") == prompt.count("C")

    def test_generate_ncq_prompt_unicode_support(self):
        """Test NCQ generation with unicode characters."""
        question = "What is 日本語の 'hello'?"
        ground_truth = "こんにちは"
        negative_candidates = ["你好", "안녕하세요", "مرحبا"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=negative_candidates
        )

        assert "日本語" in prompt
        assert "こんにちは" in prompt
        assert "你好" in prompt
        assert "안녕하세요" in prompt
        assert "مرحبا" in prompt

    def test_generate_ncq_prompt_long_text(self):
        """Test NCQ generation with very long question and candidates."""
        long_question = "This is a very long question that contains " * 50
        long_ground_truth = "This is the correct answer that is also quite long " * 20
        long_candidates = [f"Wrong answer number {i} with extra text " * 10 for i in range(5)]

        prompt = self.generator.generate_ncq_prompt(
            question=long_question,
            ground_truth=long_ground_truth,
            negative_candidates=long_candidates
        )

        assert long_question in prompt
        assert long_ground_truth in prompt
        for candidate in long_candidates:
            assert candidate in prompt

    def test_generate_ncq_prompt_numeric_candidates(self):
        """Test NCQ generation with numeric candidates."""
        question = "What is the result?"
        ground_truth = "42"
        negative_candidates = [1, 2.5, 100, -5, 0]

        # Convert to strings for the generator
        str_candidates = [str(c) for c in negative_candidates]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=str_candidates
        )

        assert "42" in prompt
        for candidate in str_candidates:
            assert candidate in prompt

    def test_generate_ncq_prompt_whitespace_handling(self):
        """Test NCQ generation with various whitespace patterns."""
        question = "  Question with spaces  "
        ground_truth = "  Answer with spaces  "
        candidates = ["  Wrong 1  ", "Wrong 2", "  Wrong 3"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )

        # Whitespace should be preserved
        assert "  Question with spaces  " in prompt
        assert "  Answer with spaces  " in prompt
        assert "  Wrong 1  " in prompt
        assert "Wrong 2" in prompt
        assert "  Wrong 3" in prompt

    def test_generate_ncq_prompt_structure_validation(self):
        """Test that the generated prompt follows the expected structure."""
        question = "Test question"
        ground_truth = "Test answer"
        candidates = ["Wrong1", "Wrong2"]

        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )

        lines = prompt.split('\n')
        
        # Check for required sections
        has_question_section = any("Question:" in line for line in lines)
        has_ground_truth_section = any("Ground Truth:" in line for line in lines)
        has_candidates_section = any("Negative Candidates:" in line for line in lines)
        
        assert has_question_section, "Prompt must contain Question section"
        assert has_ground_truth_section, "Prompt must contain Ground Truth section"
        assert has_candidates_section, "Prompt must contain Negative Candidates section"

    def test_generate_ncq_prompt_with_task_metadata(self):
        """Test NCQ generation including task metadata."""
        question = "What is the capital?"
        ground_truth = "City"
        candidates = ["Not City"]
        
        # The generator should handle basic inputs correctly
        # Metadata handling would be part of the loop, not the generator itself
        prompt = self.generator.generate_ncq_prompt(
            question=question,
            ground_truth=ground_truth,
            negative_candidates=candidates
        )
        
        assert len(prompt) > 0
        assert isinstance(prompt, str)