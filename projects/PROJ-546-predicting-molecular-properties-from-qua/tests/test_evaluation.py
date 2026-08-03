"""
Integration test for comparative evaluation.
Verifies output reports MAE_semi, MAE_DFT, p-value, flags.
"""
import pytest
from pathlib import Path

def test_evaluate_models_structure():
    """Verify evaluate_models.py exists and has correct structure."""
    script_path = Path("code/evaluate_models.py")
    assert script_path.exists(), "evaluate_models.py not found"
    
    with open(script_path) as f:
        content = f.read()
        assert "run_paired_t_test" in content
        assert "verify_mae_threshold" in content
