"""
Contract tests for ablation data generation (T015).

These tests verify that the ablation generator correctly replaces
critique text with neutral placeholders of equivalent token length.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ablation import (
    count_tokens,
    generate_neutral_placeholder,
    create_ablation_tuple,
    generate_ablation_dataset
)


class TestAblationTupleCreation:
    """Tests for create_ablation_tuple function."""

    def test_ablation_replaces_reasoning(self):
        """Verify that reasoning_snippet is replaced with placeholder."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "4",
            "critique": {
                "confidence_score": 0.9,
                "reasoning_snippet": "The sum of 2 and 2 is clearly 4 based on basic arithmetic."
            },
            "revised_answer": "4"
        }

        ablated = create_ablation_tuple(dialogue)

        assert ablated["critique"]["reasoning_snippet"] != dialogue["critique"]["reasoning_snippet"]
        assert ablated["critique"]["is_ablated"] is True
        assert "original_token_count" in ablated["critique"]

    def test_ablation_preserves_other_fields(self):
        """Verify that non-critique fields are preserved."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "4",
            "critique": {
                "confidence_score": 0.9,
                "reasoning_snippet": "Some reasoning here."
            },
            "revised_answer": "4"
        }

        ablated = create_ablation_tuple(dialogue)

        assert ablated["question"] == dialogue["question"]
        assert ablated["initial_answer"] == dialogue["initial_answer"]
        assert ablated["revised_answer"] == dialogue["revised_answer"]
        assert ablated["critique"]["confidence_score"] == dialogue["critique"]["confidence_score"]

    def test_ablation_handles_missing_critique(self):
        """Verify graceful handling of missing critique field."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "4",
            "revised_answer": "4"
        }

        ablated = create_ablation_tuple(dialogue)

        # Should return unchanged when critique is missing
        assert ablated == dialogue

    def test_ablation_handles_empty_reasoning(self):
        """Verify graceful handling of empty reasoning_snippet."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "4",
            "critique": {
                "confidence_score": 0.9,
                "reasoning_snippet": ""
            },
            "revised_answer": "4"
        }

        ablated = create_ablation_tuple(dialogue)

        # Should return unchanged when reasoning is empty
        assert ablated["critique"]["reasoning_snippet"] == ""


class TestAblationDatasetGeneration:
    """Tests for generate_ablation_dataset function."""

    def test_generates_jsonl_output(self):
        """Verify that output is valid JSONL format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as infile:
            infile.write(json.dumps({
                "question": "Q1",
                "initial_answer": "A1",
                "critique": {"confidence_score": 0.8, "reasoning_snippet": "Reasoning 1"},
                "revised_answer": "A1_revised"
            }) + '\n')
            infile.write(json.dumps({
                "question": "Q2",
                "initial_answer": "A2",
                "critique": {"confidence_score": 0.9, "reasoning_snippet": "Reasoning 2"},
                "revised_answer": "A2_revised"
            }) + '\n')
            input_path = infile.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as outfile:
            output_path = outfile.name

        try:
            stats = generate_ablation_dataset(input_path, output_path)

            # Verify output file exists and has content
            assert Path(output_path).exists()
            assert stats["total_processed"] == 2
            assert stats["successful_ablations"] == 2

            # Verify each line is valid JSON
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                for line in lines:
                    parsed = json.loads(line.strip())
                    assert "critique" in parsed
                    assert "is_ablated" in parsed["critique"]

        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_respects_sample_size(self):
        """Verify that sample_size limit is respected."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as infile:
            for i in range(10):
                infile.write(json.dumps({
                    "question": f"Q{i}",
                    "initial_answer": f"A{i}",
                    "critique": {"confidence_score": 0.8, "reasoning_snippet": f"Reasoning {i}"},
                    "revised_answer": f"A{i}_revised"
                }) + '\n')
            input_path = infile.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as outfile:
            output_path = outfile.name

        try:
            stats = generate_ablation_dataset(input_path, output_path, sample_size=3)

            assert stats["total_processed"] == 3
            assert stats["successful_ablations"] == 3

            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3

        finally:
            os.unlink(input_path)
            os.unlink(output_path)


class TestNeutralPlaceholderGeneration:
    """Tests for generate_neutral_placeholder function."""

    def test_placeholder_is_neutral(self):
        """Verify that placeholder text is neutral/non-informative."""
        original = "The model's reasoning contains a logical fallacy in step 3."
        placeholder = generate_neutral_placeholder(original, target_token_count=10)

        # Placeholder should not contain specific references to the original content
        assert "logical fallacy" not in placeholder.lower()
        assert "step 3" not in placeholder
        assert "model" not in placeholder.lower() or "model" in placeholder.lower() and "further" in placeholder.lower()

    def test_placeholder_approximates_token_count(self):
        """Verify that placeholder has approximately the target token count."""
        original = "This is a test sentence with several words."
        target_tokens = 8  # Approximate

        placeholder = generate_neutral_placeholder(original, target_tokens)

        # The placeholder should be non-empty and reasonable length
        assert len(placeholder) > 0
        assert len(placeholder.split()) > 0

    def test_placeholder_without_tokenizer(self):
        """Verify placeholder generation works without tokenizer."""
        original = "Some reasoning text here."
        placeholder = generate_neutral_placeholder(original, target_token_count=5, tokenizer=None)

        assert len(placeholder) > 0
        assert isinstance(placeholder, str)

class TestTokenCounting:
    """Tests for count_tokens function."""

    def test_count_tokens_basic(self):
        """Verify basic token counting."""
        text = "This is a test."
        count = count_tokens(text)
        assert count > 0

    def test_count_tokens_empty(self):
        """Verify empty string returns 0 or reasonable count."""
        text = ""
        count = count_tokens(text)
        assert count >= 0

    def test_count_tokens_with_mock_tokenizer(self):
        """Verify token counting with a mock tokenizer."""
        text = "Hello world"

        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = [1, 2, 3]  # 3 tokens

        count = count_tokens(text, mock_tokenizer)
        assert count == 3