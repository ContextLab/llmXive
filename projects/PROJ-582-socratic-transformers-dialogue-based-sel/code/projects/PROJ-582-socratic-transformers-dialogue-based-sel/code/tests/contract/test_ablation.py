"""
Contract tests for the ablation data generator.

These tests verify that the ablation transformation correctly replaces
critique text with neutral placeholders while preserving the structure
and token count characteristics.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.data.ablation import (
    count_tokens,
    generate_neutral_placeholder,
    create_ablation_tuple,
    generate_ablation_dataset
)


class TestTokenCounting:
    """Tests for token counting functionality."""

    def test_count_tokens_basic(self):
        """Test basic token counting with whitespace approximation."""
        text = "This is a simple test"
        count = count_tokens(text)
        assert count == 5  # 5 words

    def test_count_tokens_empty(self):
        """Test token counting with empty string."""
        count = count_tokens("")
        assert count == 0

    def test_count_tokens_with_tokenizer(self):
        """Test token counting with a mock tokenizer."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [101, 2023, 2003, 2001]  # 4 tokens
        
        text = "This is a test"
        count = count_tokens(text, mock_tokenizer)
        assert count == 4

        mock_tokenizer.encode.assert_called_once_with(text, add_special_tokens=False)


class TestNeutralPlaceholderGeneration:
    """Tests for neutral placeholder text generation."""

    def test_placeholder_length_approximation(self):
        """Test that placeholder approximates target token count."""
        target_tokens = 20
        placeholder = generate_neutral_placeholder(target_tokens)
        
        # Should be close to target (within 2 tokens)
        actual_tokens = count_tokens(placeholder)
        assert abs(actual_tokens - target_tokens) <= 2

    def test_placeholder_neutrality(self):
        """Test that placeholder text is neutral (doesn't contain critique-like content)."""
        placeholder = generate_neutral_placeholder(10)
        
        # Should not contain specific critique indicators
        assert "contradiction" not in placeholder.lower()
        assert "error" not in placeholder.lower()
        assert "incorrect" not in placeholder.lower()

    def test_placeholder_empty_target(self):
        """Test placeholder generation with zero target tokens."""
        placeholder = generate_neutral_placeholder(0)
        assert placeholder == ""


class TestAblationTupleCreation:
    """Tests for creating individual ablation tuples."""

    def test_ablation_preserves_structure(self):
        """Test that ablation preserves all original fields."""
        dialogue_tuple = {
            "question": "What is 2 + 2?",
            "initial_answer": "4",
            "critique": "The answer is correct but lacks explanation.",
            "revised_answer": "The answer is 4 because 2 + 2 = 4.",
            "metadata": {"source": "gsm8k"}
        }

        ablated = create_ablation_tuple(dialogue_tuple)

        # All original fields should be preserved
        assert ablated["question"] == dialogue_tuple["question"]
        assert ablated["initial_answer"] == dialogue_tuple["initial_answer"]
        assert ablated["revised_answer"] == dialogue_tuple["revised_answer"]
        assert ablated["metadata"] == dialogue_tuple["metadata"]

    def test_ablation_replaces_critique(self):
        """Test that critique is replaced with neutral placeholder."""
        dialogue_tuple = {
            "question": "Test question",
            "initial_answer": "Test answer",
            "critique": "This critique identifies specific logical errors.",
            "revised_answer": "Revised answer"
        }

        ablated = create_ablation_tuple(dialogue_tuple)

        # Critique should be different
        assert ablated["critique"] != dialogue_tuple["critique"]
        # But should be neutral
        assert "error" not in ablated["critique"].lower()

    def test_ablation_adds_metadata(self):
        """Test that ablation adds appropriate metadata fields."""
        dialogue_tuple = {
            "question": "Test",
            "initial_answer": "Answer",
            "critique": "Critique text",
            "revised_answer": "Revised"
        }

        ablated = create_ablation_tuple(dialogue_tuple)

        assert ablated["ablation_type"] == "neutral_placeholder"
        assert "original_critique_token_count" in ablated
        assert "ablated_critique_token_count" in ablated

    def test_ablation_missing_critique(self):
        """Test that missing critique raises ValueError."""
        dialogue_tuple = {
            "question": "Test",
            "initial_answer": "Answer",
            "revised_answer": "Revised"
        }

        with pytest.raises(ValueError, match="must contain a 'critique' field"):
            create_ablation_tuple(dialogue_tuple)


class TestAblationDatasetGeneration:
    """Tests for generating full ablation datasets."""

    def test_generate_ablation_dataset_basic(self):
        """Test basic dataset generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Create input data
            input_data = [
                {"question": "Q1", "initial_answer": "A1", "critique": "C1", "revised_answer": "R1"},
                {"question": "Q2", "initial_answer": "A2", "critique": "C2", "revised_answer": "R2"}
            ]

            with open(input_path, 'w') as f:
                for item in input_data:
                    f.write(json.dumps(item) + '\n')

            # Generate ablation dataset
            result = generate_ablation_dataset(
                dialogue_dataset_path=str(input_path),
                output_path=str(output_path)
            )

            # Verify results
            assert len(result) == 2
            assert all("ablation_type" in item for item in result)

            # Verify output file exists
            assert output_path.exists()

            # Verify output format
            with open(output_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 2

    def test_generate_ablation_dataset_sample_size(self):
        """Test dataset generation with sample size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Create larger input
            input_data = [
                {"question": f"Q{i}", "initial_answer": f"A{i}", "critique": f"C{i}", "revised_answer": f"R{i}"}
                for i in range(10)
            ]

            with open(input_path, 'w') as f:
                for item in input_data:
                    f.write(json.dumps(item) + '\n')

            # Generate with sample size
            result = generate_ablation_dataset(
                dialogue_dataset_path=str(input_path),
                output_path=str(output_path),
                sample_size=3
            )

            assert len(result) == 3

    def test_generate_ablation_dataset_missing_file(self):
        """Test that missing input file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            generate_ablation_dataset(
                dialogue_dataset_path="/nonexistent/path.jsonl",
                output_path="/tmp/output.jsonl"
            )

    def test_generate_ablation_dataset_invalid_json(self):
        """Test handling of invalid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Create input with invalid JSON
            with open(input_path, 'w') as f:
                f.write('{"question": "valid", "initial_answer": "a", "critique": "c", "revised_answer": "r"}\n')
                f.write('invalid json line\n')
                f.write('{"question": "valid2", "initial_answer": "a2", "critique": "c2", "revised_answer": "r2"}\n')

            # Should skip invalid lines and process valid ones
            result = generate_ablation_dataset(
                dialogue_dataset_path=str(input_path),
                output_path=str(output_path)
            )

            assert len(result) == 2

    def test_generate_ablation_dataset_missing_critique(self):
        """Test handling of tuples missing critique field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Create input with missing critique
            with open(input_path, 'w') as f:
                f.write('{"question": "valid", "initial_answer": "a", "critique": "c", "revised_answer": "r"}\n')
                f.write('{"question": "missing_critique", "initial_answer": "a", "revised_answer": "r"}\n')

            # Should skip invalid tuples and process valid ones
            result = generate_ablation_dataset(
                dialogue_dataset_path=str(input_path),
                output_path=str(output_path)
            )

            assert len(result) == 1