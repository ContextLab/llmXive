"""
Unit tests for collapse detection logic in the analysis pipeline.

Task: T024 [US3] Unit test for collapse detection logic (depth ≤ 0.5 × teacher depth)
"""
import pytest
import numpy as np
import sys
import os

# Add the project root to the path to allow imports from code/
# Assuming this test file is run from the project root or the path is configured correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.seed_manager import set_seed

# We will implement the collapse detection logic directly in this test file
# or import it if it exists in code/analysis/ (which is not yet implemented per task list)
# Since T027 is not done yet, we define the logic here for testing purposes.
# In a real workflow, this would be imported from code/analysis/tobit_model.py or similar.

def detect_collapse(effective_depth: float, teacher_depth: float, threshold: float = 0.5) -> bool:
    """
    Detects if reasoning collapse has occurred.
    
    Collapse is defined as: effective_depth <= threshold * teacher_depth
    
    Args:
        effective_depth: The actual depth of reasoning achieved by the student.
        teacher_depth: The optimal depth provided by the teacher policy.
        threshold: The ratio threshold (default 0.5) to consider as collapse.
        
    Returns:
        True if collapse is detected, False otherwise.
    """
    if teacher_depth <= 0:
        # Avoid division by zero or undefined behavior for zero-length teacher paths
        # If teacher depth is 0, effective must also be 0 to not be collapse? 
        # Or if teacher is 0, there is no reasoning to collapse. 
        # Let's assume if teacher is 0, collapse is False (no reasoning to lose).
        return False
        
    return effective_depth <= (threshold * teacher_depth)

class TestCollapseDetection:
    """Tests for the collapse detection logic."""

    def test_collapse_detected_when_efficient_is_half(self):
        """Test that collapse is detected when effective depth is exactly 0.5 * teacher depth."""
        teacher_depth = 10.0
        effective_depth = 5.0  # Exactly 50%
        
        assert detect_collapse(effective_depth, teacher_depth) is True

    def test_collapse_detected_when_efficient_is_less_than_half(self):
        """Test that collapse is detected when effective depth is less than 0.5 * teacher depth."""
        teacher_depth = 20.0
        effective_depth = 8.0  # 40%
        
        assert detect_collapse(effective_depth, teacher_depth) is True

    def test_no_collapse_when_efficient_is_above_half(self):
        """Test that collapse is NOT detected when effective depth is greater than 0.5 * teacher depth."""
        teacher_depth = 10.0
        effective_depth = 5.1  # 51%
        
        assert detect_collapse(effective_depth, teacher_depth) is False

    def test_collapse_with_custom_threshold(self):
        """Test collapse detection with a custom threshold."""
        teacher_depth = 100.0
        effective_depth = 40.0  # 40%
        
        # With default 0.5, should be collapse
        assert detect_collapse(effective_depth, teacher_depth, threshold=0.5) is True
        
        # With custom 0.45, should NOT be collapse (40% > 45% is false, wait. 40 < 45 -> collapse)
        # 40 <= 45 -> True (collapse)
        assert detect_collapse(effective_depth, teacher_depth, threshold=0.45) is True
        
        # With custom 0.35, should NOT be collapse (40% > 35%)
        assert detect_collapse(effective_depth, teacher_depth, threshold=0.35) is False

    def test_zero_teacher_depth(self):
        """Test behavior when teacher depth is zero."""
        # If teacher depth is 0, there is no path to collapse from.
        # Logic should handle this gracefully.
        assert detect_collapse(0.0, 0.0) is False
        assert detect_collapse(1.0, 0.0) is False

    def test_negative_depths(self):
        """Test behavior with negative depths (should not happen in valid data, but test robustness)."""
        # Negative depths are invalid, but the function should not crash.
        # Assuming the mathematical comparison still holds or we treat them as 0?
        # For now, standard comparison: -5 <= 0.5 * -10 -> -5 <= -5 -> True
        assert detect_collapse(-5.0, -10.0) is True

    def test_float_precision_edge_case(self):
        """Test a case very close to the threshold to ensure floating point handling."""
        teacher_depth = 1000000.0
        effective_depth = 500000.0000001  # Slightly above 0.5
        
        assert detect_collapse(effective_depth, teacher_depth) is False
        
        effective_depth = 500000.0  # Exactly 0.5
        assert detect_collapse(effective_depth, teacher_depth) is True

    def test_integer_inputs(self):
        """Test that integer inputs work correctly."""
        assert detect_collapse(2, 4) is True
        assert detect_collapse(3, 4) is False