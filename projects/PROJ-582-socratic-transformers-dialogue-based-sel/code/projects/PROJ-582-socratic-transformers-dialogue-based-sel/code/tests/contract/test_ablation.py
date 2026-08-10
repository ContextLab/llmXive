"""
Contract tests for the ablation module (T015b).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Import the module under test
from src.data.ablation import create_ablation_tuple, generate_neutral_placeholder, generate_ablation_dataset
from src.data.ablation_utils import get_target_tokenizer

@pytest.fixture
def sample_dialogue_tuple():
    return {
        "question": "What is 2 + 2?",
        "initial_answer": "5",
        "critique": "The calculation is incorrect. 2 plus 2 equals 4, not 5. There is a contradiction in the arithmetic.",
        "revised_answer": "4"
    }

@pytest.fixture
def tokenizer():
    # Mock tokenizer to avoid heavy loading in unit tests, or load a small one if needed
    # For strict contract testing, we mock the encoding behavior to ensure logic flow
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.side_effect = lambda text, add_special_tokens: [100] * (len(text.split()) + 1) # Simplified mock
    mock_tokenizer.decode.side_effect = lambda tokens, skip_special_tokens: " ".join(["TOKEN"] * len(tokens))
    return mock_tokenizer

class TestNeutralPlaceholderGeneration:
    def test_placeholder_generates_string(self, tokenizer):
        result = generate_neutral_placeholder(10, 1.0, tokenizer)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_placeholder_token_count_approximation(self, tokenizer):
        # Mock encode to return a predictable list
        tokenizer.encode.return_value = [1] * 10
        tokenizer.decode.return_value = "a b c d e f g h i j"
        result = generate_neutral_placeholder(10, 1.0, tokenizer)
        # The function attempts to match token count
        assert len(result) > 0

class TestAblationTupleCreation:
    def test_ablation_creates_copy(self, sample_dialogue_tuple, tokenizer):
        tokenizer.encode.return_value = [1, 2, 3, 4, 5]
        tokenizer.decode.return_value = "neutral text"
        ablation = create_ablation_tuple(sample_dialogue_tuple, tokenizer)
        assert ablation is not sample_dialogue_tuple
        assert ablation["question"] == sample_dialogue_tuple["question"]
        assert ablation["initial_answer"] == sample_dialogue_tuple["initial_answer"]
        assert ablation["revised_answer"] == sample_dialogue_tuple["revised_answer"]

    def test_ablation_replaces_critique(self, sample_dialogue_tuple, tokenizer):
        original_critique = sample_dialogue_tuple["critique"]
        tokenizer.encode.return_value = [1, 2, 3]
        tokenizer.decode.return_value = "neutral"
        ablation = create_ablation_tuple(sample_dialogue_tuple, tokenizer)
        assert ablation["critique"] != original_critique
        assert "neutral" in ablation["critique"] or len(ablation["critique"]) > 0

    def test_ablation_adds_type_field(self, sample_dialogue_tuple, tokenizer):
        tokenizer.encode.return_value = [1, 2, 3]
        tokenizer.decode.return_value = "neutral"
        ablation = create_ablation_tuple(sample_dialogue_tuple, tokenizer)
        assert "ablation_type" in ablation
        assert ablation["ablation_type"] == "neutral_placeholder_token_complexity_match"

class TestAblationDatasetGeneration:
    def test_generate_dataset_creates_file(self, sample_dialogue_tuple, tokenizer):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Write input
            with open(input_path, 'w') as f:
                f.write(json.dumps(sample_dialogue_tuple) + '\n')

            # Mock the tokenizer functions used inside generate_ablation_dataset
            with patch('src.data.ablation.get_target_tokenizer', return_value=tokenizer):
                count = generate_ablation_dataset(str(input_path), str(output_path))

            assert count == 1
            assert output_path.exists()

            with open(output_path, 'r') as f:
                result_line = f.readline()
                result = json.loads(result_line)
                assert "ablation_type" in result
                assert result["critique"] != sample_dialogue_tuple["critique"]

    def test_generate_dataset_handles_empty_file(self, tokenizer):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Write empty file
            with open(input_path, 'w') as f:
                pass

            with patch('src.data.ablation.get_target_tokenizer', return_value=tokenizer):
                count = generate_ablation_dataset(str(input_path), str(output_path))

            assert count == 0
            assert output_path.exists()
            assert output_path.stat().st_size == 0