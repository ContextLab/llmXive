"""
Contract tests for the ablation data generator.

These tests verify that the ablation generation logic correctly replaces
critique text with neutral placeholders of equivalent token length.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.ablation import (
    generate_neutral_placeholder,
    create_ablation_tuple,
    generate_ablation_dataset
)
from src.data.ablation_utils import get_target_tokenizer, calculate_token_count


@pytest.fixture
def sample_dialogue_tuple():
    """Provide a sample dialogue tuple for testing."""
    return {
        "question": "What is 2 + 2?",
        "initial_answer": "The answer is 4.",
        "critique": "This answer is correct but lacks explanation of the reasoning process.",
        "revised_answer": "The answer is 4. This is because 2 + 2 equals 4 in basic arithmetic."
    }


@pytest.fixture
def tokenizer():
    """Provide a tokenizer for testing."""
    # We'll mock the tokenizer to avoid loading the full model in tests
    mock_tokenizer = MagicMock()
    
    # Mock encode to return a simple token sequence
    def mock_encode(text, add_special_tokens=False):
        # Simple mock: split by spaces and count
        tokens = text.split()
        return list(range(len(tokens)))
    
    mock_tokenizer.encode = mock_encode
    
    # Mock decode to return the original text
    def mock_decode(token_ids, skip_special_tokens=False):
        return " ".join([f"token_{i}" for i in token_ids])
    
    mock_tokenizer.decode = mock_decode
    
    return mock_tokenizer


class TestNeutralPlaceholderGeneration:
    """Tests for the neutral placeholder generation logic."""

    def test_generate_placeholder_matches_token_count(self, tokenizer):
        """Test that the generated placeholder matches the original token count."""
        original_critique = "This is a test critique with multiple words."
        
        placeholder = generate_neutral_placeholder(original_critique, tokenizer)
        
        original_count = calculate_token_count(original_critique, tokenizer)
        placeholder_count = calculate_token_count(placeholder, tokenizer)
        
        # Allow for +/- 1 token difference
        assert abs(original_count - placeholder_count) <= 1
        
    def test_generate_placeholder_empty_input(self, tokenizer):
        """Test that empty input returns empty output."""
        placeholder = generate_neutral_placeholder("", tokenizer)
        assert placeholder == ""
        
    def test_generate_placeholder_non_empty(self, tokenizer):
        """Test that non-empty input produces non-empty output."""
        original_critique = "Test critique."
        placeholder = generate_neutral_placeholder(original_critique, tokenizer)
        assert len(placeholder) > 0


class TestAblationTupleCreation:
    """Tests for the ablation tuple creation logic."""

    def test_create_ablation_tuple_replaces_critique(self, sample_dialogue_tuple, tokenizer):
        """Test that the critique is replaced with a placeholder."""
        ablation_tuple = create_ablation_tuple(sample_dialogue_tuple, tokenizer)
        
        assert ablation_tuple['question'] == sample_dialogue_tuple['question']
        assert ablation_tuple['initial_answer'] == sample_dialogue_tuple['initial_answer']
        assert ablation_tuple['revised_answer'] == sample_dialogue_tuple['revised_answer']
        assert ablation_tuple['critique'] != sample_dialogue_tuple['critique']
        assert len(ablation_tuple['critique']) > 0
        
    def test_create_ablation_tuple_preserves_metadata(self, sample_dialogue_tuple, tokenizer):
        """Test that metadata about token counts is preserved."""
        ablation_tuple = create_ablation_tuple(sample_dialogue_tuple, tokenizer)
        
        assert 'original_critique_length' in ablation_tuple
        assert 'original_token_count' in ablation_tuple
        assert 'placeholder_token_count' in ablation_tuple
        
    def test_create_ablation_tuple_token_match(self, sample_dialogue_tuple, tokenizer):
        """Test that placeholder token count matches original within tolerance."""
        ablation_tuple = create_ablation_tuple(sample_dialogue_tuple, tokenizer)
        
        original_count = ablation_tuple['original_token_count']
        placeholder_count = ablation_tuple['placeholder_token_count']
        
        assert abs(original_count - placeholder_count) <= 1
        
    def test_create_ablation_tuple_invalid_input(self, tokenizer):
        """Test that invalid input raises an error."""
        with pytest.raises(ValueError):
            create_ablation_tuple({}, tokenizer)
            
        with pytest.raises(ValueError):
            create_ablation_tuple(None, tokenizer)


class TestAblationDatasetGeneration:
    """Tests for the ablation dataset generation logic."""

    def test_generate_ablation_dataset_creates_output(self, sample_dialogue_tuple, tokenizer):
        """Test that the dataset generation creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"
            
            # Write sample input
            with open(input_path, 'w') as f:
                f.write(json.dumps(sample_dialogue_tuple) + '\n')
            
            # Mock the tokenizer loading
            with patch('src.data.ablation.get_target_tokenizer', return_value=tokenizer):
                count = generate_ablation_dataset(str(input_path), str(output_path))
            
            assert count == 1
            assert output_path.exists()
            
            # Verify output content
            with open(output_path, 'r') as f:
                output_data = json.loads(f.read())
            
            assert 'critique' in output_data
            assert output_data['critique'] != sample_dialogue_tuple['critique']

    def test_generate_ablation_dataset_multiple_samples(self, sample_dialogue_tuple, tokenizer):
        """Test processing multiple samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"
            
            # Write multiple samples
            with open(input_path, 'w') as f:
                for i in range(5):
                    f.write(json.dumps(sample_dialogue_tuple) + '\n')
            
            # Mock the tokenizer loading
            with patch('src.data.ablation.get_target_tokenizer', return_value=tokenizer):
                count = generate_ablation_dataset(str(input_path), str(output_path))
            
            assert count == 5
            assert output_path.exists()
            
            # Verify output has 5 lines
            with open(output_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 5