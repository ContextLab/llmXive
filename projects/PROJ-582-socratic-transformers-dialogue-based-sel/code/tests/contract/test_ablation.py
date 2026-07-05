"""
Contract tests for the ablation data generator (T015).

These tests verify that the ablation process correctly neutralizes critique text
while preserving token length and schema integrity (FR-007).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.data.ablation import (
    create_ablation_tuple,
    generate_ablation_dataset,
    generate_neutral_placeholder
)


class TestAblationTupleCreation:
    """Tests for the core ablation transformation logic."""

    def test_critique_neutralization(self):
        """Verify that critique reasoning is replaced with neutral text."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "4",
            "critique": {
                "confidence_score": 0.9,
                "reasoning_snippet": "This is a simple addition problem with a clear correct answer.",
                "reasoning_type": "verification"
            },
            "revised_answer": "4"
        }

        # Use a mock tokenizer for consistent testing
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5, 6, 7, 8]  # 8 tokens
        mock_tokenizer.decode.side_effect = lambda tokens: " ".join(["neutral"] * len(tokens))

        ablated = create_ablation_tuple(dialogue, mock_tokenizer)

        assert "critique" in ablated
        assert "reasoning_snippet" in ablated["critique"]
        # The snippet should be different from original
        assert ablated["critique"]["reasoning_snippet"] != dialogue["critique"]["reasoning_snippet"]
        # But it should contain neutral text
        assert "neutral" in ablated["critique"]["reasoning_snippet"]
        assert ablated["critique"].get("ablation_applied") is True

    def test_token_length_preservation(self):
        """Verify that the neutral text matches the original token count."""
        dialogue = {
            "question": "Test question",
            "initial_answer": "Test answer",
            "critique": {
                "confidence_score": 0.5,
                "reasoning_snippet": "Short",
                "reasoning_type": "check"
            },
            "revised_answer": "Test answer"
        }

        mock_tokenizer = MagicMock()
        # Simulate "Short" being 2 tokens
        mock_tokenizer.encode.return_value = [1, 2]
        mock_tokenizer.decode.side_effect = lambda tokens: " ".join(["neutral"] * len(tokens))

        ablated = create_ablation_tuple(dialogue, mock_tokenizer)

        # Check that original length was recorded
        assert "original_length_tokens" in ablated["critique"]
        assert ablated["critique"]["original_length_tokens"] == 2

    def test_missing_critique_field(self):
        """Verify behavior when critique field is missing."""
        dialogue = {
            "question": "Test",
            "initial_answer": "Answer",
            "revised_answer": "Answer"
        }

        ablated = create_ablation_tuple(dialogue, None)

        # Should return as-is without crashing
        assert "critique" not in ablated

    def test_empty_reasoning_snippet(self):
        """Verify behavior when reasoning snippet is empty."""
        dialogue = {
            "question": "Test",
            "initial_answer": "Answer",
            "critique": {
                "confidence_score": 0.5,
                "reasoning_snippet": "",
                "reasoning_type": "check"
            },
            "revised_answer": "Answer"
        }

        ablated = create_ablation_tuple(dialogue, None)

        # Should preserve the empty snippet
        assert ablated["critique"]["reasoning_snippet"] == ""


class TestAblationDatasetGeneration:
    """Tests for the full dataset generation pipeline."""

    def test_full_pipeline(self):
        """Test the complete generation of an ablation dataset from JSONL."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f_in:
            sample_data = [
                {
                    "question": "Q1",
                    "initial_answer": "A1",
                    "critique": {
                        "confidence_score": 0.8,
                        "reasoning_snippet": "This is a detailed critique of the answer.",
                        "reasoning_type": "analysis"
                    },
                    "revised_answer": "A1_revised"
                },
                {
                    "question": "Q2",
                    "initial_answer": "A2",
                    "critique": {
                        "confidence_score": 0.6,
                        "reasoning_snippet": "Another critique here.",
                        "reasoning_type": "verification"
                    },
                    "revised_answer": "A2_revised"
                }
            ]
            for item in sample_data:
                f_in.write(json.dumps(item) + '\n')
            input_path = f_in.name

        # Create temporary output path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f_out:
            output_path = f_out.name

        try:
            # Mock tokenizer for testing
            mock_tokenizer = MagicMock()
            mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
            mock_tokenizer.decode.side_effect = lambda tokens: " ".join(["neutral"] * len(tokens))

            result = generate_ablation_dataset(
                input_path=input_path,
                output_path=output_path,
                tokenizer=mock_tokenizer,
                sample_size=2
            )

            # Verify results
            assert len(result) == 2
            assert os.path.exists(output_path)

            # Verify output file content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2

                first_item = json.loads(lines[0])
                assert "critique" in first_item
                assert first_item["critique"].get("ablation_applied") is True
                assert first_item["critique"]["reasoning_snippet"] != "This is a detailed critique of the answer."

        finally:
            # Cleanup
            os.unlink(input_path)
            os.unlink(output_path)

    def test_sample_size_limit(self):
        """Verify that sample_size limits the number of processed records."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f_in:
            for i in range(10):
                f_in.write(json.dumps({
                    "question": f"Q{i}",
                    "initial_answer": f"A{i}",
                    "critique": {"confidence_score": 0.5, "reasoning_snippet": "Critique", "reasoning_type": "x"},
                    "revised_answer": f"A{i}"
                }) + '\n')
            input_path = f_in.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f_out:
            output_path = f_out.name

        try:
            mock_tokenizer = MagicMock()
            mock_tokenizer.encode.return_value = [1]
            mock_tokenizer.decode.side_effect = lambda tokens: "neutral"

            result = generate_ablation_dataset(
                input_path=input_path,
                output_path=output_path,
                tokenizer=mock_tokenizer,
                sample_size=3
            )

            assert len(result) == 3

        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_file_not_found(self):
        """Verify that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            generate_ablation_dataset(
                input_path="nonexistent/path.jsonl",
                output_path="output.jsonl"
            )


class TestNeutralPlaceholderGeneration:
    """Tests for the neutral text generation logic."""

    def test_placeholder_with_tokenizer(self):
        """Test placeholder generation using a tokenizer."""
        mock_tokenizer = MagicMock()
        # Simulate encoding "Hello world" as 2 tokens
        mock_tokenizer.encode.return_value = [1, 2]
        mock_tokenizer.decode.side_effect = lambda tokens: " ".join(["neutral"] * len(tokens))

        result = generate_neutral_placeholder("Hello world", 2, mock_tokenizer)

        assert "neutral" in result

    def test_placeholder_without_tokenizer(self):
        """Test placeholder generation without a tokenizer (fallback)."""
        result = generate_neutral_placeholder("Hello world", 5, None)

        # Should contain neutral words
        assert "neutral" in result
        # Rough check on length
        assert len(result.split()) >= 5