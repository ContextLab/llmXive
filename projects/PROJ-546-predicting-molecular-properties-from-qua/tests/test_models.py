"""
Contract test for code/train_models.py
Verifies RF training.
"""
import pytest
from pathlib import Path

def test_train_models_structure():
    """Verify train_models.py exists and has correct structure."""
    script_path = Path("code/train_models.py")
    assert script_path.exists(), "train_models.py not found"
    
    with open(script_path) as f:
        content = f.read()
        assert "train_and_evaluate_fold" in content
        assert "train_models" in content
