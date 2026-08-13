"""
Tests for the power analysis functionality.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.power_analysis import calculate_sample_size

def test_sample_size_calculation():
    """
    Test that the sample size calculation produces a reasonable integer.
    For r=0.10, alpha=0.001, power=0.80, N should be large.
    """
    # Parameters from the task
    r = 0.10
    alpha = 0.001
    power = 0.80

    n = calculate_sample_size(r, alpha, power)

    # N must be a positive integer
    assert isinstance(n, int), "Sample size must be an integer"
    assert n > 0, "Sample size must be positive"
    
    # With r=0.10 and alpha=0.001, N should be significantly larger than typical small studies
    # Roughly: z_alpha ~ 3.3, z_beta ~ 0.84, z_r ~ 0.1
    # N ~ (4.14/0.1)^2 ~ 1714 + 3 ~ 1717
    assert n > 1000, f"Expected N > 1000 for r=0.10, alpha=0.001, got {n}"

def test_zero_effect_size():
    """Test that zero effect size raises an error."""
    with pytest.raises(ValueError):
        calculate_sample_size(0.0, 0.05, 0.80)