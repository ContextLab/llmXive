"""
Integration tests for T014: Self-critique generator.

Verifies:
1. Dialogue tuple schema compliance (contract test).
2. Degenerate dialogue truncation logic (n-gram overlap > 0.9).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.generate_dialogue import (
    generate_dialogue_tuple,
    parse_critique_json,
    compute_ngram_overlap
)
from src.utils.config import SocraticConfig

class TestDialogueGeneration:
    """Integration tests for the dialogue generation pipeline."""

    def test_validate_dialogue_schema(self):
        """
        Contract test: Assert JSONL records contain required fields.
        Based on T010 requirements.
        """
        # Mock model and tokenizer
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Mock the call_model function to return predictable JSON
        mock_critique = json.dumps({
            "confidence_score": 0.85,
            "reasoning_snippet": "The logic is flawed because...",
            "flaw_type": "logical_gap"
        })
        mock_revised = "The corrected answer is 42."
        
        # Patch the internal functions
        with patch('src.data.generate_dialogue.call_model') as mock_call:
            mock_call.side_effect = [mock_critique, mock_revised]
            
            with patch('src.data.generate_dialogue.compute_ngram_overlap', return_value=0.1):
                result = generate_dialogue_tuple(
                    question="What is 2+2?",
                    initial_answer="It is 5.",
                    model=mock_model,
                    tokenizer=mock_tokenizer,
                    config=SocraticConfig()
                )
        
        # Assertions
        assert result is not None, "Dialogue tuple should not be None"
        assert "question" in result
        assert "initial_answer" in result
        assert "critique" in result
        assert "revised_answer" in result
        
        critique = result["critique"]
        assert "confidence_score" in critique
        assert "reasoning_snippet" in critique
        
        # Verify types
        assert isinstance(result["question"], str)
        assert isinstance(result["initial_answer"], str)
        assert isinstance(critique["confidence_score"], (int, float))
        assert isinstance(critique["reasoning_snippet"], str)

    def test_degenerate_dialogue_truncation(self):
        """
        Integration test: Assert that n-gram overlap > 0.9 triggers
        DEGENERATE_DIALOGUE_TRUNCATED log and truncates the dialogue.
        Based on T011 requirements.
        """
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()
        
        # Create a critique that is almost identical to the answer (degenerate)
        initial_text = "The capital of France is Paris because it is the largest city."
        degenerate_critique = json.dumps({
            "confidence_score": 0.9,
            "reasoning_snippet": "The capital of France is Paris because it is the largest city.",
            "flaw_type": "repetition"
        })
        
        with patch('src.data.generate_dialogue.call_model') as mock_call:
            mock_call.return_value = degenerate_critique # Only called once for critique
            
            # Force high overlap
            with patch('src.data.generate_dialogue.compute_ngram_overlap', return_value=0.95):
                with patch('src.data.generate_dialogue.get_logger') as mock_logger:
                    result = generate_dialogue_tuple(
                        question="What is the capital of France?",
                        initial_answer=initial_text,
                        model=mock_model,
                        tokenizer=mock_tokenizer,
                        config=SocraticConfig()
                    )
        
        # Verify the result indicates degeneracy
        assert result is not None
        assert result.get("is_degenerate") is True
        assert result.get("overlap_score") > 0.9
        
        # Verify the revised answer is the same as initial (truncation)
        assert result.get("revised_answer") == initial_text
        
        # Verify the log event was triggered
        mock_logger.return_value.warning.assert_called()
        call_args = mock_logger.return_value.warning.call_args
        assert "DEGENERATE_DIALOGUE_TRUNCATED" in str(call_args)

    def test_parse_critique_json_variants(self):
        """
        Test parsing of various JSON formats in critique output.
        """
        # Valid JSON
        assert parse_critique_json('{"a": 1}') == {"a": 1}
        
        # JSON with markdown
        json_str = '```json\n{"a": 1}\n```'
        result = parse_critique_json(json_str)
        assert result == {"a": 1}
        
        # JSON with extra text
        json_str = 'Here is the result: {"a": 1} end.'
        result = parse_critique_json(json_str)
        assert result == {"a": 1}
        
        # Invalid JSON
        assert parse_critique_json('not json') is None
        assert parse_critique_json('{"unclosed": ') is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])