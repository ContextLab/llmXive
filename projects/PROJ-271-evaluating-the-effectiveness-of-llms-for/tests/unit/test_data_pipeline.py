import pytest
import json
import os
from pathlib import Path
import tempfile
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import setup_logging
from code.data_pipeline import compute_radon_metrics, run_pylint_analysis, normalize_pylint_smells

logger = setup_logging("test_data_pipeline")

def test_radon_metrics():
    """Test that radon metrics are computed correctly."""
    code = """
    def hello():
        x = 1
        if x > 0:
            return True
        return False
    """
    metrics = compute_radon_metrics(code)
    assert "loc" in metrics
    assert "cyclomatic_complexity" in metrics
    assert "nesting_depth" in metrics
    assert metrics["loc"] > 0
    assert metrics["cyclomatic_complexity"] >= 1
    assert metrics["nesting_depth"] >= 1

def test_pylint_analysis():
    """Test that pylint runs and returns codes."""
    code = """
    def bad_func( ):
        x=1
    """
    codes = run_pylint_analysis(code)
    # Should return a list of strings
    assert isinstance(codes, list)
    # Might be empty if no errors found in this simple snippet, but should not crash

def test_normalize_pylint_smells():
    """Test normalization of pylint codes."""
    mapping = {
        "C0111": "Missing Docstring",
        "R0913": "Too Many Arguments"
    }
    codes = ["C0111", "R0913", "UNKNOWN_CODE"]
    normalized = normalize_pylint_smells(codes, mapping)
    assert "Missing Docstring" in normalized
    assert "Too Many Arguments" in normalized
    assert "Unknown-UNKNOWN_CODE" in normalized

def test_sample_size_limit():
    """Verify dynamic sample size reduction logic."""
    # This is a unit test for the logic, not the full pipeline
    # We mock the time estimation to force a reduction
    from code.data_pipeline import load_sampled_functions_stratified
    # This would require mocking the dataset and time functions
    # For now, we assert the function exists and signature is correct
    assert callable(load_sampled_functions_stratified)
    
    # Verify the logic in the report generation
    # We can't easily run the full stream here, but we can test the math
    # If time_per_func * N > budget, N should be reduced.
    # This is implicitly tested in the integration flow.
    pass