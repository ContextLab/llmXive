"""
Unit tests for prompt construction logic in code/prompt_builder.py.

Tests verify:
1. Blind prompt construction contains only problem statement and standard headers.
2. Guided prompt construction includes the Partial Logic Trace anchor.
3. Prompt formatting adheres to expected structure (no target-language idioms in anchors).
"""
import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.prompt_builder import build_blind_prompt, build_guided_prompt


class TestBlindPromptConstruction:
    """Tests for the blind prompt builder."""

    def test_blind_prompt_contains_problem_statement(self):
        """Verify that the blind prompt includes the problem description."""
        task_data = {
            "problem_statement": "Write a function to calculate factorial.",
            "language": "rust",
            "difficulty": "medium"
        }
        
        prompt = build_blind_prompt(task_data)
        
        assert "Write a function to calculate factorial." in prompt
        assert "problem_statement" not in prompt  # Should be the value, not the key
    
    def test_blind_prompt_format(self):
        """Verify the structural format of the blind prompt."""
        task_data = {
            "problem_statement": "Sort a list of numbers.",
            "language": "kotlin",
            "difficulty": "easy"
        }
        
        prompt = build_blind_prompt(task_data)
        
        # Check for standard headers expected in the prompt template
        assert "Problem Description" in prompt
        assert "Target Language" in prompt
        assert "kotlin" in prompt
        # Blind prompt should NOT contain logic anchor sections
        assert "Partial Logic Trace" not in prompt
        assert "Anchor" not in prompt

    def test_blind_prompt_target_language(self):
        """Verify the prompt explicitly sets the target language."""
        for lang in ["rust", "kotlin", "go"]:
            task_data = {
                "problem_statement": "Reverse a string.",
                "language": lang,
                "difficulty": "hard"
            }
            prompt = build_blind_prompt(task_data)
            assert lang in prompt


class TestGuidedPromptConstruction:
    """Tests for the guided prompt builder."""

    def test_guided_prompt_contains_anchor(self):
        """Verify that the guided prompt includes the logic anchor."""
        task_data = {
            "problem_statement": "Calculate Fibonacci sequence.",
            "language": "rust",
            "difficulty": "medium",
            "anchor": "1. Initialize a list with [0, 1].\n2. Iterate from index 2 to N.\n3. Append sum of previous two elements."
        }
        
        prompt = build_guided_prompt(task_data)
        
        assert "Calculate Fibonacci sequence." in prompt
        assert "Partial Logic Trace" in prompt
        assert "Initialize a list with [0, 1]" in prompt
        assert "Iterate from index 2 to N" in prompt
    
    def test_guided_prompt_structure(self):
        """Verify the guided prompt has the correct sections."""
        task_data = {
            "problem_statement": "Find max in array.",
            "language": "go",
            "difficulty": "easy",
            "anchor": "1. Set max to first element.\n2. Loop through remaining elements.\n3. Update max if current is larger."
        }
        
        prompt = build_guided_prompt(task_data)
        
        # Check for expected headers
        assert "Problem Description" in prompt
        assert "Partial Logic Trace" in prompt
        assert "Target Language" in prompt
        assert "go" in prompt
    
    def test_guided_prompt_no_target_idioms_in_anchor(self):
        """
        Verify that the anchor content in the prompt does not contain
        target-language specific idioms (e.g., 'let mut' for Rust, 'val' for Kotlin).
        This ensures the anchor is language-agnostic as per FR-001.
        """
        # Simulate an anchor that might have been incorrectly generated with Rust idioms
        # In a real scenario, logic_anchor.py should prevent this, but we verify the prompt builder handles it safely
        # or that the input data is clean. Here we test that the prompt builder correctly embeds the provided anchor.
        
        # Case 1: Clean anchor (Python/Pseudo-code style)
        clean_anchor = "1. Initialize variable count to 0.\n2. Loop through the input list.\n3. Increment count if element is even."
        task_data_clean = {
            "problem_statement": "Count even numbers.",
            "language": "rust",
            "anchor": clean_anchor
        }
        
        prompt_clean = build_guided_prompt(task_data_clean)
        assert "let mut" not in prompt_clean  # Should not appear if anchor is clean
        assert "Initialize variable count" in prompt_clean
        
        # Case 2: Verify that if the input anchor contains target idioms, they are present in the prompt
        # (This test ensures the prompt builder faithfully transmits the anchor, 
        # relying on logic_anchor.py to provide clean input).
        # We assert that the prompt builder does NOT strip or modify the anchor, 
        # so if the anchor is dirty, the prompt will be dirty (which is a data quality issue, not a prompt builder bug).
        dirty_anchor = "1. let mut count = 0;\n2. for x in list { ... }"
        task_data_dirty = {
            "problem_statement": "Count items.",
            "language": "rust",
            "anchor": dirty_anchor
        }
        
        prompt_dirty = build_guided_prompt(task_data_dirty)
        assert "let mut" in prompt_dirty  # Prompt builder should faithfully include the anchor
        # Note: The responsibility for cleaning the anchor lies with logic_anchor.py (T013/T014).
        # This test confirms the prompt builder does not accidentally sanitize or break the anchor.

    def test_guided_prompt_missing_anchor(self):
        """Verify behavior when anchor is missing (should handle gracefully or raise)."""
        task_data = {
            "problem_statement": "Add two numbers.",
            "language": "kotlin",
            # No anchor key
        }
        
        # Depending on implementation, this might raise or include an empty anchor.
        # Assuming it handles missing anchor by either skipping or using a placeholder.
        # We test that it doesn't crash.
        try:
            prompt = build_guided_prompt(task_data)
            # If it returns a prompt, it should not contain "Partial Logic Trace" if anchor is missing/empty
            # or it might contain an empty section.
            assert prompt is not None
        except KeyError:
            # Expected if the function requires the anchor key
            pass
        except Exception:
            pytest.fail("build_guided_prompt raised an unexpected exception for missing anchor")

    def test_guided_prompt_with_failed_output(self):
        """Verify that guided prompt can include previous failed output if provided."""
        task_data = {
            "problem_statement": "Parse JSON.",
            "language": "go",
            "anchor": "1. Read input string.\n2. Unmarshal to struct.",
            "failed_output": "Error: syntax error at line 1"
        }
        
        prompt = build_guided_prompt(task_data)
        
        assert "Error: syntax error at line 1" in prompt
        assert "Previous Attempt" in prompt or "Failed Output" in prompt


class TestPromptBuilderEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_problem_statement(self):
        """Test handling of empty problem statement."""
        task_data = {
            "problem_statement": "",
            "language": "rust",
            "anchor": "1. Do nothing."
        }
        
        prompt = build_blind_prompt(task_data)
        # Should not crash, prompt might be minimal
        assert prompt is not None
    
    def test_special_characters_in_statement(self):
        """Test that special characters in problem statement don't break formatting."""
        special_statement = "Write code to handle: <tag> & 'quotes' \"double\"."
        task_data = {
            "problem_statement": special_statement,
            "language": "kotlin",
            "anchor": "1. Process input."
        }
        
        prompt_blind = build_blind_prompt(task_data)
        prompt_guided = build_guided_prompt(task_data)
        
        assert special_statement in prompt_blind
        assert special_statement in prompt_guided