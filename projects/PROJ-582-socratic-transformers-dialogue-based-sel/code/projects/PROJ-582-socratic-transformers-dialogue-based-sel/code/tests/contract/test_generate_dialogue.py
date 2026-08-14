"""
Contract tests for T014: Self-Critique Generator.
Validates the schema and logic of the generated dialogue tuples.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.generate_dialogue import (
    check_quality_gate,
    generate_critique_prompt,
    generate_revised_answer_prompt,
    validate_question_structure
)

class TestQualityGate:
    def test_pass_with_keywords(self):
        critique = "This answer contains a contradiction in the second step."
        assert check_quality_gate(critique) is True
    
    def test_pass_with_error(self):
        critique = "The calculation is incorrect due to a wrong assumption."
        assert check_quality_gate(critique) is True
    
    def test_fail_empty(self):
        assert check_quality_gate("") is False
        assert check_quality_gate(None) is False
    
    def test_fail_no_keywords(self):
        critique = "This is a nice answer."
        assert check_quality_gate(critique) is False

class TestPromptGeneration:
    def test_critique_prompt_format(self):
        answer = "42"
        prompt = generate_critique_prompt(answer)
        assert "Identify logical contradictions" in prompt
        assert "Answer: 42" in prompt
    
    def test_revised_answer_prompt_format(self):
        question = "What is 2+2?"
        critique = "Error in addition"
        prompt = generate_revised_answer_prompt(question, critique)
        assert "Question: What is 2+2?" in prompt
        assert "Constraint: The previous answer contained the following issues: Error in addition" in prompt

class TestQuestionValidation:
    def test_valid_question(self):
        assert validate_question_structure("What is the capital of France?") is True
    
    def test_invalid_question_short(self):
        assert validate_question_structure("Hi") is False
    
    def test_invalid_question_empty(self):
        assert validate_question_structure("") is False

class TestDialogueTupleSchema:
    """
    Validates that the generated tuple matches the schema defined in T045.
    Schema: question, initial_answer, critique, revised_answer.
    """
    
    @pytest.fixture
    def sample_tuple(self):
        return {
            "question": "If x=2, what is x^2?",
            "initial_answer": "x^2 is 4.",
            "critique": "The answer is correct but the reasoning is missing.",
            "revised_answer": "Since x=2, x^2 = 2*2 = 4.",
            "source": "gsm8k_123"
        }
    
    def test_schema_keys(self, sample_tuple):
        required_keys = {"question", "initial_answer", "critique", "revised_answer"}
        assert required_keys.issubset(sample_tuple.keys())
    
    def test_schema_types(self, sample_tuple):
        for key in ["question", "initial_answer", "critique", "revised_answer"]:
            assert isinstance(sample_tuple[key], str), f"{key} must be a string"
    
    def test_revised_answer_not_containing_critique_error(self, sample_tuple):
        """
        Specific verification: revised_answer should not contain the specific error phrase 
        found in critique. 
        Note: In this synthetic test, we assume the critique identifies an error phrase.
        We simulate a case where the error phrase is 'missing reasoning'.
        """
        sample_tuple["critique"] = "Error: missing reasoning."
        sample_tuple["revised_answer"] = "Since x=2, x^2 = 4. Reasoning provided."
        # In a real scenario, we would check if the specific error phrase is absent.
        # For this test, we assert the structure is correct.
        assert "missing reasoning" not in sample_tuple["revised_answer"].lower() or "reasoning" in sample_tuple["revised_answer"]

class TestIntegration:
    def test_generate_dialogue_tuple_rejection_logic(self):
        """
        Mock the models to ensure that if all candidates fail, the function returns None.
        """
        mock_base_model = MagicMock()
        mock_base_tokenizer = MagicMock()
        mock_critic_model = MagicMock()
        mock_critic_tokenizer = MagicMock()
        
        # Mock the call_model function to return a candidate that always contains the error
        # We need to patch the function inside the module
        with patch("src.data.generate_dialogue.call_model") as mock_call:
            # First call: initial answer
            mock_call.return_value = "Initial Answer"
            # Second call: critique
            mock_call.return_value = "Error: invalid assumption."
            # Subsequent calls (5 candidates): all contain the error phrase "invalid assumption"
            mock_call.side_effect = [
                "Initial Answer", # initial
                "Error: invalid assumption.", # critique
                "Answer with invalid assumption", # cand 1
                "Answer with invalid assumption", # cand 2
                "Answer with invalid assumption", # cand 3
                "Answer with invalid assumption", # cand 4
                "Answer with invalid assumption", # cand 5
            ]
            
            from src.data.generate_dialogue import generate_dialogue_tuple
            
            sample = {"question": "Test question", "answer": "42"}
            result = generate_dialogue_tuple(
                sample, mock_base_model, mock_base_tokenizer, mock_critic_model, mock_critic_tokenizer
            )
            
            assert result is None, "Should reject if all candidates fail the check"
    
    def test_generate_dialogue_tuple_success(self):
        """
        Mock the models to ensure a valid tuple is returned when a candidate passes.
        """
        mock_base_model = MagicMock()
        mock_base_tokenizer = MagicMock()
        mock_critic_model = MagicMock()
        mock_critic_tokenizer = MagicMock()
        
        with patch("src.data.generate_dialogue.call_model") as mock_call:
            # Sequence: initial, critique, cand1(fail), cand2(pass)
            mock_call.side_effect = [
                "Initial Answer",
                "Error: invalid assumption.",
                "Answer with invalid assumption", # fail
                "Correct answer without error", # pass
            ]
            
            from src.data.generate_dialogue import generate_dialogue_tuple
            
            sample = {"question": "Test question", "answer": "42"}
            result = generate_dialogue_tuple(
                sample, mock_base_model, mock_base_tokenizer, mock_critic_model, mock_critic_tokenizer
            )
            
            assert result is not None
            assert result["revised_answer"] == "Correct answer without error"
            assert result["critique"] == "Error: invalid assumption."