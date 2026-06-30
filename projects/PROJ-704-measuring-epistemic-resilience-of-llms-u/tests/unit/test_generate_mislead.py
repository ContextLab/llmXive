"""
Unit tests for T016: generate_mislead.py
Verifies the injection logic and output structure.
"""
import json
import random
import sys
from pathlib import Path
import pytest

# Add project root to path if running directly
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_mislead import inject_false_claim, FALSE_CLAIMS

class TestInjectionLogic:
    def test_inject_claim_appends_to_stem(self):
        """Test that the false claim is appended to the stem."""
        stem = "What is the capital of France?"
        options = ["Paris", "London", "Berlin", "Madrid"]
        claim = "However, new evidence suggests it is London."
        
        result = inject_false_claim(stem, options, claim)
        
        assert stem in result
        assert claim in result
        assert result.startswith(stem)
        # Check that they are concatenated with a space
        assert f"{stem} {claim}" == result
    
    def test_inject_claim_preserves_options_reference(self):
        """Test that the injection function accepts options (even if not used in this simple impl)."""
        stem = "Question?"
        options = ["A", "B"]
        claim = "Claim."
        
        result = inject_false_claim(stem, options, claim)
        assert "A" not in result  # Options are not injected into the stem in this logic
        assert claim in result
    
    def test_inject_claim_varies_with_claim(self):
        """Test that different claims produce different stems."""
        stem = "Base question."
        options = ["A"]
        
        claim1 = "Claim one."
        claim2 = "Claim two."
        
        res1 = inject_false_claim(stem, options, claim1)
        res2 = inject_false_claim(stem, options, claim2)
        
        assert res1 != res2
        assert claim1 in res1
        assert claim2 in res2

class TestFalseClaimsPool:
    def test_false_claims_not_empty(self):
        """Ensure the pool of false claims is populated."""
        assert len(FALSE_CLAIMS) > 0
    
    def test_false_claims_are_strings(self):
        """Ensure all claims are strings."""
        for claim in FALSE_CLAIMS:
            assert isinstance(claim, str)
            assert len(claim) > 0

class TestOutputStructure:
    """
    Tests the structure of the output JSONL file.
    Since we cannot easily run the full script in a unit test without mocking I/O,
    we test the logic that constructs the object here.
    """
    def test_construct_mislead_item(self):
        """Simulate the construction of a mislead item."""
        # Simulate an input item
        input_item = {
            "id": "12345",
            "question": "What is 2+2?",
            "options": ["3", "4", "5", "6"],
            "cop": 1  # Index of '4'
        }
        
        # Simulate logic from process_dataset
        stem = input_item["question"]
        options = input_item["options"]
        correct_index = input_item["cop"]
        original_answer_key = chr(65 + correct_index)
        
        # Inject (using a fixed claim for test)
        false_claim = "However, math has changed."
        new_stem = inject_false_claim(stem, options, false_claim)
        
        output_item = {
            "id": input_item["id"],
            "original_stem": stem,
            "injected_claim": false_claim,
            "mislead_stem": new_stem,
            "options": options,
            "correct_answer_key": original_answer_key,
            "correct_answer_index": correct_index,
            "source": "medmcqa",
            "validation_status": "pending",
            "injection_method": "append_claim"
        }
        
        # Assertions
        assert output_item["id"] == "12345"
        assert output_item["original_stem"] == "What is 2+2?"
        assert output_item["injected_claim"] == "However, math has changed."
        assert "However, math has changed." in output_item["mislead_stem"]
        assert output_item["correct_answer_key"] == "B"
        assert output_item["correct_answer_index"] == 1
        assert output_item["validation_status"] == "pending"
        assert "A" not in output_item["mislead_stem"] # Options not injected into stem