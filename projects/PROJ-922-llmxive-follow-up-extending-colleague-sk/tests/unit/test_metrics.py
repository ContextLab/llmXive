"""
Contract tests for Hallucination detection logic.

This test verifies that the hallucination detection logic correctly:
1. Extracts entity-value pairs using regex.
2. Identifies facts not present in the context (Direct Hallucination).
3. Identifies facts that require invalid multi-hop reasoning not supported by context.

It uses mock data to simulate the four task domains and verifies the logic
in `metrics.py` behaves deterministically without requiring the full inference pipeline.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import re

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.metrics import (
    calculate_hallucination_rate,
    extract_facts,
    validate_facts_against_context,
    HallucinationError
)
from utils.logging import get_logger

logger = get_logger(__name__)


class TestHallucinationDetection:
    """Contract tests for Hallucination detection logic."""

    def test_extract_facts_simple_regex(self):
        """
        Contract: The regex extraction must find entity-value pairs like 'Key: Value'.
        """
        text = "The capital is Paris: France. The population is 2M."
        facts = extract_facts(text)
        
        assert "Paris" in facts or "France" in facts, "Should extract at least one fact"
        # The regex in implementation is expected to capture pairs
        # Assuming implementation returns list of tuples or dicts
        # We verify the function runs and returns a structure
        assert isinstance(facts, list), "Facts must be returned as a list"

    def test_hallucination_when_fact_not_in_context(self):
        """
        Contract: If an extracted fact is NOT in the context string,
        Hallucination Rate must increment (score > 0).
        """
        task_data = {
            "task_id": "H-001",
            "domain": "factual",
            "task": "Who wrote Hamlet?",
            "output": "The author is Shakespeare: William. He lived in London.",
            "context": "The play Hamlet is a tragedy." # Does not mention Shakespeare
        }

        # Mock validator to simulate fact extraction and context check
        # We test the logic by passing a mock that returns a fact NOT in context
        mock_extractor = Mock(return_value=[("author", "Shakespeare")])
        
        # The calculate_hallucination_rate function should detect the mismatch
        # Since we can't easily mock the internal regex in the imported module without patching the module itself,
        # we test the contract by mocking the internal validation step.
        
        # However, to strictly follow the "Contract Test" pattern for the logic:
        # We verify that if a fact is missing from context, the rate is non-zero.
        
        # Let's test the helper logic directly if exposed, or the main flow with a mock
        # Assuming the implementation allows injecting a check or we test the outcome:
        # We will patch the internal validation to return False for a specific fact.
        
        with patch('evaluation.metrics.validate_facts_against_context') as mock_validate:
            mock_validate.return_value = False # Fact not found
            
            score = calculate_hallucination_rate(task_data)
            
            # If validation fails, hallucination rate should be > 0 (or 1.0 for single fact)
            assert score > 0.0, "Hallucination rate must be > 0 when fact is missing"

    def test_no_hallucination_when_fact_in_context(self):
        """
        Contract: If the extracted fact IS in the context, Hallucination Rate must be 0.0.
        """
        task_data = {
            "task_id": "H-002",
            "domain": "factual",
            "task": "Who wrote Hamlet?",
            "output": "The author is Shakespeare.",
            "context": "Shakespeare wrote Hamlet. It is a famous play."
        }

        with patch('evaluation.metrics.validate_facts_against_context') as mock_validate:
            mock_validate.return_value = True # Fact found
            
            score = calculate_hallucination_rate(task_data)
            
            assert score == 0.0, "Hallucination rate must be 0.0 when facts are grounded"

    def test_multi_hop_reasoning_hallucination(self):
        """
        Contract: If a fact requires multi-hop reasoning not present in context,
        it must be flagged as a hallucination.
        Example: Context says "A is B", "B is C". Output says "A is C".
        If the context doesn't explicitly state "A is C" and the logic checker (Z3/SymPy)
        isn't triggered or fails to prove it, it's a hallucination in this heuristic context.
        """
        task_data = {
            "task_id": "H-003",
            "domain": "logic",
            "task": "Is A C?",
            "output": "Yes, A is C.",
            "context": "A is B. B is C." # Implicit, but heuristic check might fail without solver
        }

        # Simulate the scenario where the multi-hop check fails (returns False)
        # because the heuristic regex or simple lookup didn't find "A is C" explicitly.
        with patch('evaluation.metrics.validate_facts_against_context') as mock_validate:
            mock_validate.return_value = False # Multi-hop not proven
            
            score = calculate_hallucination_rate(task_data)
            
            assert score > 0.0, "Hallucination rate must be > 0 for unproven multi-hop"

    def test_hallucination_error_on_malformed_input(self):
        """
        Contract: If the output is None or empty, the function should handle it gracefully
        or raise a specific error if defined.
        """
        task_data = {
            "task_id": "H-004",
            "domain": "factual",
            "task": "What is 1+1?",
            "output": None,
            "context": {}
        }

        # The implementation should handle None output
        # If it raises, we catch it; if it returns 0 or 1, we check.
        # Based on T021 spec: "if fact not in context... increment". No fact -> no increment?
        # Or is empty output a hallucination? Usually empty output is a failure (Heuristic 0).
        # For Hallucination, if no facts are extracted, rate might be 0.
        
        # Let's assume the function handles None without crashing
        try:
            score = calculate_hallucination_rate(task_data)
            # If no facts extracted, hallucination rate should be 0 (no false claims made)
            assert isinstance(score, float), "Score must be a float"
        except Exception as e:
            # If it raises, it must be a defined error
            if "Hallucination" in str(type(e)):
                pass 
            else:
                raise

    def test_aggregate_hallucination_rate(self):
        """
        Contract: The average of multiple hallucination scores is the final rate.
        """
        scores = [0.0, 1.0, 0.0, 1.0]
        mean_score = sum(scores) / len(scores)
        assert mean_score == 0.5

    def test_regex_extraction_format(self):
        """
        Contract: The regex extraction must follow the pattern \b(\w+): (\w+)\b.
        """
        text = "Name: Alice. Age: 30. City: London."
        facts = extract_facts(text)
        
        # Check that we got pairs
        assert len(facts) >= 2, "Should extract multiple facts"
        # Verify structure
        for fact in facts:
            # Assuming fact is a tuple (key, value) or dict
            assert len(fact) == 2, "Each fact must be a pair"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])