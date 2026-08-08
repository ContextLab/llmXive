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
    generate_ablation_dataset,
    main
)
from src.data.ablation_utils import calculate_token_length, calculate_syntactic_complexity, get_target_tokenizer

class TestTokenCounting:
    def test_count_tokens_basic(self):
        """Test that token counting works for basic strings."""
        tokenizer = get_target_tokenizer()
        text = "This is a test sentence."
        tokens = calculate_token_length(text, tokenizer)
        assert tokens > 0, "Token count should be positive"

    def test_count_tokens_empty(self):
        """Test that token counting returns 0 for empty string."""
        tokenizer = get_target_tokenizer()
        tokens = calculate_token_length("", tokenizer)
        assert tokens == 0, "Empty string should have 0 tokens"

class TestNeutralPlaceholderGeneration:
    def test_generate_neutral_placeholder_token_match(self):
        """Test that generated placeholder matches target token count."""
        original_text = "The calculation is incorrect because the variable was misdefined."
        tokenizer = get_target_tokenizer()
        target_tokens = calculate_token_length(original_text, tokenizer)
        target_complexity = calculate_syntactic_complexity(original_text)
        
        placeholder = generate_neutral_placeholder(target_tokens, target_complexity)
        placeholder_tokens = calculate_token_length(placeholder, tokenizer)
        
        # Allow a small margin of error (e.g., +/- 2 tokens)
        assert abs(placeholder_tokens - target_tokens) <= 2, \
            f"Token mismatch: target={target_tokens}, actual={placeholder_tokens}"

    def test_generate_neutral_placeholder_complexity_match(self):
        """Test that generated placeholder has similar syntactic complexity."""
        original_text = "The calculation is incorrect because the variable was misdefined."
        target_complexity = calculate_syntactic_complexity(original_text)
        target_tokens = calculate_token_length(original_text, get_target_tokenizer())
        
        placeholder = generate_neutral_placeholder(target_tokens, target_complexity)
        placeholder_complexity = calculate_syntactic_complexity(placeholder)
        
        # Allow 10% margin for complexity
        assert abs(placeholder_complexity - target_complexity) <= 0.1 * target_complexity, \
            f"Complexity mismatch: target={target_complexity}, actual={placeholder_complexity}"

class TestAblationTupleCreation:
    def test_create_ablation_tuple_replaces_critique(self):
        """Test that ablation tuple replaces critique with neutral text."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "5",
            "critique": "The answer is wrong. 2+2 is 4.",
            "revised_answer": "4"
        }
        
        ablation = create_ablation_tuple(dialogue)
        
        assert ablation['critique'] != dialogue['critique'], "Critique should be replaced"
        assert ablation['condition'] == 'ablation', "Condition should be 'ablation'"
        assert ablation['question'] == dialogue['question'], "Question should be unchanged"
        assert ablation['initial_answer'] == dialogue['initial_answer'], "Initial answer should be unchanged"
        assert ablation['revised_answer'] == dialogue['revised_answer'], "Revised answer should be unchanged"

    def test_create_ablation_tuple_token_match(self):
        """Test that ablation critique matches original token count."""
        dialogue = {
            "question": "What is 2+2?",
            "initial_answer": "5",
            "critique": "The answer is wrong. 2+2 is 4.",
            "revised_answer": "4"
        }
        
        ablation = create_ablation_tuple(dialogue)
        
        original_tokens = calculate_token_length(dialogue['critique'], get_target_tokenizer())
        ablation_tokens = calculate_token_length(ablation['critique'], get_target_tokenizer())
        
        # Allow small margin
        assert abs(ablation_tokens - original_tokens) <= 2, \
            f"Token mismatch: original={original_tokens}, ablation={ablation_tokens}"

class TestAblationDatasetGeneration:
    def test_generate_ablation_dataset_creates_file(self):
        """Test that dataset generation creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"
            
            # Create input file
            input_data = [
                {"question": "Q1", "initial_answer": "A1", "critique": "C1", "revised_answer": "RA1"},
                {"question": "Q2", "initial_answer": "A2", "critique": "C2", "revised_answer": "RA2"}
            ]
            
            with open(input_path, 'w') as f:
                for record in input_data:
                    f.write(json.dumps(record) + '\n')
            
            generate_ablation_dataset(str(input_path), str(output_path))
            
            assert output_path.exists(), "Output file should be created"
            
            # Verify content
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 2, "Should have 2 records"
            
            for line in lines:
                record = json.loads(line)
                assert 'condition' in record, "Each record should have condition"
                assert record['condition'] == 'ablation', "Condition should be 'ablation'"

    def test_generate_ablation_dataset_sample_size(self):
        """Test that sample_size parameter limits output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"
            
            # Create input file with 10 records
            input_data = [
                {"question": f"Q{i}", "initial_answer": f"A{i}", "critique": f"C{i}", "revised_answer": f"RA{i}"}
                for i in range(10)
            ]
            
            with open(input_path, 'w') as f:
                for record in input_data:
                    f.write(json.dumps(record) + '\n')
            
            generate_ablation_dataset(str(input_path), str(output_path), sample_size=3)
            
            with open(output_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 3, f"Should have 3 records, got {len(lines)}"