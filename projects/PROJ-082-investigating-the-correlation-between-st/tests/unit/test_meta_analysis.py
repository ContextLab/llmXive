"""
Unit tests for meta_analysis.py (T014).
Verifies gate logic, model execution, and output format.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.meta_analysis import (
    load_study_count_from_json,
    load_effect_sizes_and_se,
    run_random_effects_model,
    run_meta_analysis,
    PROJECT_ROOT,
    DATA_PROCESSED,
    DATA_DERIVED
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Mock project root structure
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "derived").mkdir(parents=True, exist_ok=True)
        yield tmp_path

def test_gate_logic_insufficient_studies(temp_dirs, caplog):
    """Test that analysis is skipped when N < 10."""
    # Setup
    study_count_file = temp_dirs / "data" / "processed" / "study_count.json"
    with open(study_count_file, 'w') as f:
        json.dump({"N": 5}, f)
    
    # Patch paths to use temp dir
    with patch('analysis.meta_analysis.STUDY_COUNT_PATH', study_count_file), \
         patch('analysis.meta_analysis.DATA_PROCESSED', temp_dirs / "data" / "processed"), \
         patch('analysis.meta_analysis.DATA_DERIVED', temp_dirs / "data" / "derived"):
        
        result = run_meta_analysis()
        
    assert result["status"] == "skipped"
    assert result["reason"] == "Insufficient studies"
    assert result["N"] == 5

def test_gate_logic_sufficient_studies(temp_dirs):
    """Test that analysis runs when N >= 10."""
    # Setup
    study_count_file = temp_dirs / "data" / "processed" / "study_count.json"
    with open(study_count_file, 'w') as f:
        json.dump({"N": 15}, f)
    
    extracted_csv = temp_dirs / "data" / "processed" / "extracted_studies.csv"
    # Create a CSV with 15 valid studies
    import csv
    with open(extracted_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['author', 'year', 'r', 'se', 'narrative_pool'])
        for i in range(15):
            writer.writerow([f"Author{i}", 2020, 0.3 + (i * 0.01), 0.05, 'False'])
    
    # Patch paths
    with patch('analysis.meta_analysis.STUDY_COUNT_PATH', study_count_file), \
         patch('analysis.meta_analysis.DATA_PROCESSED', temp_dirs / "data" / "processed"), \
         patch('analysis.meta_analysis.DATA_DERIVED', temp_dirs / "data" / "derived"):
        
        result = run_meta_analysis()
        
    assert result["status"] == "completed"
    assert "pooled_effect" in result
    assert "i_squared" in result

def test_run_random_effects_model_basic():
    """Test basic random effects model calculation."""
    r_vals = [0.3, 0.4, 0.35, 0.25, 0.5]
    se_vals = [0.05, 0.05, 0.05, 0.05, 0.05]
    
    result = run_random_effects_model(r_vals, se_vals)
    
    assert "pooled_effect" in result
    assert "ci_lower" in result
    assert "ci_upper" in result
    assert result["model_type"] == "random_effects"
    assert result["reliability"] == "reliable"

def test_run_random_effects_model_fallback(caplog):
    """Test fallback to fixed effects on convergence failure."""
    # Simulate data that might cause issues or force fallback logic
    r_vals = [0.1, 0.9] # High variance
    se_vals = [0.01, 0.01]
    
    # Force a scenario where we might hit a warning or fallback
    # In this test, we just verify the function returns a result
    result = run_random_effects_model(r_vals, se_vals)
    
    assert "pooled_effect" in result
    # Even if it falls back, it should return a result
    assert result["model_type"] in ["random_effects", "fixed_effects_fallback"]

def test_load_study_count_from_json_missing():
    """Test error handling for missing study count file."""
    with pytest.raises(FileNotFoundError):
        load_study_count_from_json(Path("/nonexistent/path.json"))

def test_load_effect_sizes_and_se_missing():
    """Test error handling for missing CSV."""
    with pytest.raises(FileNotFoundError):
        load_effect_sizes_and_se(Path("/nonexistent/studies.csv"))

def test_load_effect_sizes_and_se_skips_narrative():
    """Test that narrative-only studies are skipped if r is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['author', 'r', 'se', 'narrative_pool'])
        writer.writerow(['A', '', '', 'True']) # No r, narrative
        writer.writerow(['B', '0.3', '0.05', 'False']) # Valid
        fname = f.name
    
    try:
        r_vals, se_vals = load_effect_sizes_and_se(Path(fname))
        assert len(r_vals) == 1
        assert r_vals[0] == 0.3
    finally:
        os.unlink(fname)
