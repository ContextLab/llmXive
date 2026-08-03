"""
Unit test for code/sensitivity_analysis.py
"""
import pytest
from pathlib import Path

def test_sensitivity_analysis_structure():
    """Verify sensitivity_analysis.py exists and has correct structure."""
    script_path = Path("code/sensitivity_analysis.py")
    assert script_path.exists(), "sensitivity_analysis.py not found"
    
    with open(script_path) as f:
        content = f.read()
        assert "extract_feature_importance" in content
        assert "run_sensitivity_sweep" in content
        assert "calculate_mae_degradation" in content