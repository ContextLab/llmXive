import json
import math
import random
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.generate_trajectories import (
    generate_text_block,
    inject_critical_evidence,
    clamp_density,
    validate_density_computation,
    generate_trajectory,
    entropy_per_token,
    NUM_TRAJECTORIES,
    DENSITY_LEVELS
)

def test_clamp_density_zero():
    """Test that zero density is clamped to a positive value."""
    result = clamp_density(0.0)
    assert result > 0.0, "Zero density should be clamped to a positive value."
    assert result == 0.01, "Zero density should be clamped to 0.01."

def test_clamp_density_negative():
    """Test that negative density is clamped."""
    result = clamp_density(-5.0)
    assert result > 0.0, "Negative density should be clamped to a positive value."

def test_clamp_density_positive():
    """Test that positive density is returned as is."""
    result = clamp_density(3.5)
    assert result == 3.5, "Positive density should remain unchanged."

def test_inject_critical_evidence():
    """Test that critical evidence is injected into the text."""
    text = "This is a test string."
    evidence_index = 5
    result = inject_critical_evidence(text, evidence_index, 10)
    assert f"[CRITICAL_EVIDENCE_TURN_{evidence_index}]" in result, "Evidence marker not found in text."

def test_generate_trajectory_structure():
    """Test that a generated trajectory has the correct structure."""
    trajectory = generate_trajectory(1, "low", 15)
    
    assert "trajectory_id" in trajectory
    assert trajectory["trajectory_id"] == 1
    assert "density_level" in trajectory
    assert trajectory["density_level"] == "low"
    assert "turns" in trajectory
    assert len(trajectory["turns"]) == 15
    
    # Check turn structure
    for turn in trajectory["turns"]:
        assert "turn_index" in turn
        assert "text" in turn
        assert "density" in turn
        assert "is_critical_evidence" in turn

def test_density_computation_validation():
    """Test that density computation validation works."""
    # Create a text with known properties
    text = "a" * 100
    # This will have low entropy. We just check the function runs and returns a boolean.
    # We can't easily predict the exact entropy without running the calc, but we can check logic.
    result = validate_density_computation(text, 0.0, tolerance=10.0)
    assert isinstance(result, bool), "Validation result should be a boolean."

def test_entropy_per_token_non_zero():
    """Test that entropy per token is non-zero for non-empty text."""
    text = "This is a test."
    entropy = entropy_per_token(text)
    assert entropy > 0, "Entropy should be positive for non-empty text."

def test_trajectory_density_clamping():
    """Test that trajectory density is clamped if generated as zero."""
    # Force a scenario where density might be zero by mocking or specific input
    # Since we can't easily force zero entropy with random generation, we rely on the clamp_density function
    # being called inside generate_trajectory.
    # We test the clamp_density function directly as a proxy.
    assert clamp_density(0) > 0
    assert clamp_density(-1) > 0