"""
Contract tests for the ablation data generator (T015).

These tests verify that the ablation process correctly replaces critiques
with neutral placeholders of equivalent token length.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest
import tiktoken

from src.data.ablation import (
    count_tokens,
    generate_neutral_placeholder,
    create_ablation_tuple,
    generate_ablation_dataset
)


class TestTokenCounting:
    """Tests for the count_tokens function."""

    def test_count_tokens_empty_string(self):
        """Empty string should return 0 tokens."""
        assert count_tokens("") == 0
        assert count_tokens(None) == 0  # type: ignore

    def test_count_tokens_simple_text(self):
        """Simple text should return a positive token count."""
        text = "The quick brown fox jumps over the lazy dog."
        count = count_tokens(text)
        assert count > 0

    def test_count_tokens_consistency(self):
        """Token count should be consistent for the same text."""
        text = "This is a test string for token counting."
        count1 = count_tokens(text)
        count2 = count_tokens(text)
        assert count1 == count2


class TestNeutralPlaceholderGeneration:
    """Tests for the generate_neutral_placeholder function."""

    def test_placeholder_length_match(self):
        """Placeholder should have approximately the same token count as input."""
        original_text = "This is a specific critique about the reasoning process."
        token_count = count_tokens(original_text)
        placeholder = generate_neutral_placeholder(token_count)
        
        placeholder_count = count_tokens(placeholder)
        # Allow small variance due to tokenization boundaries
        assert abs(placeholder_count - token_count) <= 2

    def test_placeholder_neutrality(self):
        """Placeholder should not contain specific semantic content."""
        token_count = 10
        placeholder = generate_neutral_placeholder(token_count)
        
        # The placeholder should not contain words from the original critique
        # that would imply specific reasoning guidance
        assert "reasoning" not in placeholder.lower()
        assert "logic" not in placeholder.lower()
        assert "error" not in placeholder.lower()

    def test_placeholder_zero_tokens(self):
        """Zero token count should return empty string."""
        placeholder = generate_neutral_placeholder(0)
        assert placeholder == ""


class TestAblationTupleCreation:
    """Tests for the create_ablation_tuple function."""

    @pytest.fixture
    def valid_dialogue_tuple(self):
        """Provide a valid dialogue tuple for testing."""
        return {
            'question': "What is 2 + 2?",
            'initial_answer': "The answer is 4.",
            'critique': "The reasoning is correct but lacks explanation.",
            'revised_answer': "The answer is 4 because 2 plus 2 equals 4."
        }

    def test_ablation_tuple_structure(self, valid_dialogue_tuple):
        """Ablation tuple should have all required keys."""
        ablation = create_ablation_tuple(valid_dialogue_tuple)
        
        required_keys = {'question', 'initial_answer', 'critique', 'revised_answer', 'ablation_metadata'}
        assert required_keys.issubset(ablation.keys())

    def test_ablation_preserves_non_critique_fields(self, valid_dialogue_tuple):
        """Non-critique fields should remain unchanged."""
        ablation = create_ablation_tuple(valid_dialogue_tuple)
        
        assert ablation['question'] == valid_dialogue_tuple['question']
        assert ablation['initial_answer'] == valid_dialogue_tuple['initial_answer']
        assert ablation['revised_answer'] == valid_dialogue_tuple['revised_answer']

    def test_ablation_replaces_critique(self, valid_dialogue_tuple):
        """Critique should be replaced with a placeholder."""
        ablation = create_ablation_tuple(valid_dialogue_tuple)
        
        original_critique = valid_dialogue_tuple['critique']
        ablation_critique = ablation['critique']
        
        assert ablation_critique != original_critique
        assert len(ablation_critique) > 0  # Placeholder should not be empty

    def test_ablation_metadata_included(self, valid_dialogue_tuple):
        """Ablation metadata should be included."""
        ablation = create_ablation_tuple(valid_dialogue_tuple)
        
        assert 'ablation_metadata' in ablation
        assert 'original_critique_length' in ablation['ablation_metadata']
        assert 'ablation_type' in ablation['ablation_metadata']
        assert ablation['ablation_metadata']['ablation_type'] == 'neutral_placeholder'

    def test_ablation_invalid_input(self):
        """Invalid input should raise ValueError."""
        invalid_tuple = {'question': "Test", 'initial_answer': "Test"}
        
        with pytest.raises(ValueError):
            create_ablation_tuple(invalid_tuple)


class TestAblationDatasetGeneration:
    """Tests for the generate_ablation_dataset function."""

    @pytest.fixture
    def sample_dialogue_data(self):
        """Provide sample dialogue data for testing."""
        return [
            {
                'question': "Question 1",
                'initial_answer': "Answer 1",
                'critique': "Critique 1",
                'revised_answer': "Revised 1"
            },
            {
                'question': "Question 2",
                'initial_answer': "Answer 2",
                'critique': "Critique 2",
                'revised_answer': "Revised 2"
            },
            {
                'question': "Question 3",
                'initial_answer': "Answer 3",
                'critique': "Critique 3",
                'revised_answer': "Revised 3"
            }
        ]

    def test_generate_ablation_dataset_basic(self, sample_dialogue_data):
        """Basic dataset generation should work correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as infile:
            for item in sample_dialogue_data:
                infile.write(json.dumps(item) + '\n')
            input_path = infile.name

        output_path = input_path.replace('.jsonl', '_ablation.jsonl')

        try:
            count = generate_ablation_dataset(input_path, output_path)
            
            assert count == len(sample_dialogue_data)
            assert os.path.exists(output_path)

            # Verify output content
            with open(output_path, 'r') as outfile:
                lines = outfile.readlines()
                assert len(lines) == len(sample_dialogue_data)

                for line in lines:
                    ablation_tuple = json.loads(line)
                    assert 'ablation_metadata' in ablation_tuple
                    assert ablation_tuple['ablation_metadata']['ablation_type'] == 'neutral_placeholder'

        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_generate_ablation_dataset_max_samples(self, sample_dialogue_data):
        """Max samples limit should be respected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as infile:
            for item in sample_dialogue_data:
                infile.write(json.dumps(item) + '\n')
            input_path = infile.name

        output_path = input_path.replace('.jsonl', '_ablation.jsonl')

        try:
            max_samples = 2
            count = generate_ablation_dataset(input_path, output_path, max_samples=max_samples)
            
            assert count == max_samples

            with open(output_path, 'r') as outfile:
                lines = outfile.readlines()
                assert len(lines) == max_samples

        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_generate_ablation_dataset_invalid_json(self, sample_dialogue_data):
        """Invalid JSON lines should be skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as infile:
            for item in sample_dialogue_data:
                infile.write(json.dumps(item) + '\n')
            # Add an invalid line
            infile.write("this is not valid json\n")
            input_path = infile.name

        output_path = input_path.replace('.jsonl', '_ablation.jsonl')

        try:
            count = generate_ablation_dataset(input_path, output_path)
            
            # Should process valid lines and skip invalid ones
            assert count == len(sample_dialogue_data)

            with open(output_path, 'r') as outfile:
                lines = outfile.readlines()
                assert len(lines) == len(sample_dialogue_data)

        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_generate_ablation_dataset_file_not_found(self):
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            generate_ablation_dataset("nonexistent_file.jsonl", "output.jsonl")