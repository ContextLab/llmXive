"""
Unit tests for T019: Bonferroni Correction
"""
import pytest
import json
import tempfile
from pathlib import Path
from code.task_t019_bonferroni_correction import (
    load_statistical_results,
    apply_bonferroni_correction,
    save_bonferroni_results
)

def test_apply_bonferroni_correction():
    """Test that Bonferroni correction is applied correctly."""
    # Mock input data
    mock_results = {
        "perseverative_errors": {"p_value": 0.02},
        "categories_completed": {"p_value": 0.04}
    }
    
    # Apply correction
    corrected = apply_bonferroni_correction(mock_results)
    
    # Check that corrected p-values exist
    assert "p_value_corrected" in corrected["perseverative_errors"]
    assert "p_value_corrected" in corrected["categories_completed"]
    
    # Bonferroni correction: p_corrected = p_raw * n (n=2 here)
    # 0.02 * 2 = 0.04, 0.04 * 2 = 0.08
    assert corrected["perseverative_errors"]["p_value_corrected"] == pytest.approx(0.04)
    assert corrected["categories_completed"]["p_value_corrected"] == pytest.approx(0.08)
    
    # Check significance flags
    assert corrected["perseverative_errors"]["is_significant_after_correction"] == True
    assert corrected["categories_completed"]["is_significant_after_correction"] == False

def test_load_statistical_results_missing_file():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        load_statistical_results("nonexistent/file.json")

def test_save_bonferroni_results():
    """Test that results are saved correctly to disk."""
    mock_results = {
        "perseverative_errors": {"p_value": 0.02, "p_value_corrected": 0.04},
        "categories_completed": {"p_value": 0.04, "p_value_corrected": 0.08}
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.json"
        save_bonferroni_results(mock_results, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["perseverative_errors"]["p_value_corrected"] == 0.04
        assert loaded["categories_completed"]["p_value_corrected"] == 0.08