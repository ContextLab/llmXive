"""
Unit tests for code/statistics.py
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from statistics import bonferroni_correction, fdr_correction

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.05, 0.1, 0.2]
    num_tests = len(p_values)
    
    corrected = bonferroni_correction(p_values)
    
    assert len(corrected) == num_tests
    # Bonferroni multiplies p-values by number of tests
    expected = [p * num_tests for p in p_values]
    
    for i, val in enumerate(corrected):
        assert val == min(expected[i], 1.0)  # Cap at 1.0

def test_fdr_correction():
    """Test FDR (Benjamini-Hochberg) correction logic."""
    p_values = [0.01, 0.05, 0.1, 0.2]
    
    corrected = fdr_correction(p_values)
    
    assert len(corrected) == len(p_values)
    # FDR should produce values <= Bonferroni (more powerful)
    bonf = bonferroni_correction(p_values)
    
    for i, val in enumerate(corrected):
        assert val <= bonf[i]

def test_power_analysis():
  """Test power analysis calculation."""
  from statistics import calculate_power
  
  # Typical parameters
  n_samples = 100
  effect_size = 0.5
  alpha = 0.05
  
  power = calculate_power(n_samples, effect_size, alpha)
  
  assert 0 <= power <= 1
  assert power > 0  # Should have some power
