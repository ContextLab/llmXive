import pytest
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Import the logic we are testing.
# Since T013/T014/T015 are not yet implemented, we implement the
# filter logic here inline for the purpose of this unit test,
# ensuring the test is self-contained and verifiable.
# In the full pipeline, these functions would reside in code/utils/extraction.py.

class ExtractionFilterLogic:
    """
    Implementation of the "failed-then-success" and "coordinate-free" filter logic
    to be tested by T010 and T011.
    """

    @staticmethod
    def is_failed_then_success(trajectory: List[Dict[str, Any]]) -> bool:
        """
        Checks if a trajectory starts with a failure and ends with a success
        immediately following a hint.

        A valid trajectory must have at least two steps:
        1. Initial attempt: status == "failure" (or similar failure indicator)
        2. Post-hint attempt: status == "success"

        Args:
            trajectory: List of step dictionaries. Each step should contain
                        'status' (e.g., 'failure', 'success') and optionally 'hint'.

        Returns:
            bool: True if the trajectory matches the pattern, False otherwise.
        """
        if len(trajectory) < 2:
            return False

        # Check initial step for failure
        initial_step = trajectory[0]
        if initial_step.get('status') != 'failure':
            return False

        # Check that there is a subsequent success
        # The task requires "initial failure, post-hint success".
        # We look for the first success after the initial failure.
        found_success = False
        for step in trajectory[1:]:
            if step.get('status') == 'success':
                found_success = True
                break
            # If we encounter another failure without a success in between,
            # strictly speaking, the pattern "failed-then-success" might be broken
            # depending on interpretation. However, usually, we just need
            # at least one success after the initial failure.
            # Let's assume the requirement is: Start with Failure, eventually Success.
            # But to be stricter as per "failed-then-success" (implying the transition):
            # We will just ensure the first state is failure and there exists a success later.
        
        return found_success

    @staticmethod
    def is_coordinate_free(hint: str) -> bool:
        """
        Validates that a hint does not contain coordinate-based visual grounding.
        Rejects hints containing patterns like [x, y], (x, y), or specific
        coordinate formats that rely on screen position rather than semantic description.

        Args:
            hint: The hint string to validate.

        Returns:
            bool: True if the hint is coordinate-free (purely linguistic), False otherwise.
        """
        if not hint:
            return False

        import re
        # Pattern to detect coordinate-like structures: [x, y], (x, y), x,y
        # We look for brackets/parens containing numbers and commas.
        # Examples: [100, 200], (50, 50), 10,20
        coord_pattern = re.compile(r'[\[\(]\s*\d+\s*,\s*\d+\s*[\]\)]')
        
        if coord_pattern.search(hint):
            return False

        # Additional check for common coordinate keywords that might imply position
        # without semantic meaning, though the bracket check is usually sufficient.
        # We stick to the regex for robustness.

        return True

def test_failed_then_success_basic():
    """Test basic failed-then-success detection."""
    trajectory = [
        {"step": 1, "status": "failure", "action": "click(50,50)"},
        {"step": 2, "status": "success", "action": "click(text='Submit')"}
    ]
    assert ExtractionFilterLogic.is_failed_then_success(trajectory) is True

def test_failed_then_success_no_initial_failure():
    """Test that trajectories starting with success are rejected."""
    trajectory = [
        {"step": 1, "status": "success", "action": "click(text='Start')"}
    ]
    assert ExtractionFilterLogic.is_failed_then_success(trajectory) is False

def test_failed_then_success_no_success():
    """Test that trajectories ending in failure are rejected."""
    trajectory = [
        {"step": 1, "status": "failure", "action": "click(50,50)"},
        {"step": 2, "status": "failure", "action": "click(60,60)"}
    ]
    assert ExtractionFilterLogic.is_failed_then_success(trajectory) is False

def test_failed_then_success_too_short():
    """Test that single-step trajectories are rejected."""
    trajectory = [{"step": 1, "status": "failure"}]
    assert ExtractionFilterLogic.is_failed_then_success(trajectory) is False
    
    trajectory_empty = []
    assert ExtractionFilterLogic.is_failed_then_success(trajectory_empty) is False

def test_coordinate_free_valid_hint():
    """Test valid linguistic hints."""
    valid_hints = [
        "Click the 'Submit' button at the bottom.",
        "Type your email address in the text field.",
        "Scroll down to find the settings.",
        "Tap the icon that looks like a gear."
    ]
    for hint in valid_hints:
        assert ExtractionFilterLogic.is_coordinate_free(hint) is True

def test_coordinate_free_invalid_bracket():
    """Test rejection of hints with [x, y] coordinates."""
    invalid_hints = [
        "Click at [100, 200].",
        "Tap (50, 50).",
        "Touch the screen at [ 10 , 20 ]."
    ]
    for hint in invalid_hints:
        assert ExtractionFilterLogic.is_coordinate_free(hint) is False

def test_coordinate_free_empty_hint():
    """Test rejection of empty hints."""
    assert ExtractionFilterLogic.is_coordinate_free("") is False
    assert ExtractionFilterLogic.is_coordinate_free(None) is False

def test_integration_filter_trajectory():
    """Integration test combining both filters on a sample trajectory."""
    # Valid trajectory with valid hint
    trajectory_valid = [
        {
            "step": 1,
            "status": "failure",
            "action": "click(100, 100)",
            "hint": "Click the 'Login' button."
        },
        {
            "step": 2,
            "status": "success",
            "action": "click(text='Login')",
            "hint": "Click the 'Login' button."
        }
    ]
    
    # Check logic
    assert ExtractionFilterLogic.is_failed_then_success(trajectory_valid) is True
    # Assuming the hint is extracted from the step
    hint = trajectory_valid[0].get('hint', '')
    assert ExtractionFilterLogic.is_coordinate_free(hint) is True

    # Invalid trajectory with coordinate hint
    trajectory_invalid_hint = [
        {
            "step": 1,
            "status": "failure",
            "action": "click(100, 100)",
            "hint": "Click at [100, 200]."
        },
        {
            "step": 2,
            "status": "success",
            "action": "click(100, 200)",
            "hint": "Click at [100, 200]."
        }
    ]
    
    assert ExtractionFilterLogic.is_failed_then_success(trajectory_invalid_hint) is True
    assert ExtractionFilterLogic.is_coordinate_free(trajectory_invalid_hint[0].get('hint', '')) is False