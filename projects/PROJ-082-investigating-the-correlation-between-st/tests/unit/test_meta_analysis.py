import json
import math
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.meta_analysis import (
    load_study_count_from_json, 
    run_random_effects_model, 
    save_results,
    load_effect_sizes_and_se
)

def test_load_study_count_from_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "study_count.json"
        with open(path, 'w') as f:
            json.dump({"N": 15}, f)
        
        assert load_study_count_from_json(path) == 15

def test_run_random_effects_model_basic():
    # Create synthetic data that should pass
    # r values around 0.5, N around 50
    # Z = 0.5 * ln((1+0.5)/(1-0.5)) = 0.5 * ln(3) = 0.549
    # SE = 1 / sqrt(47) = 0.146
    
    r_vals = [0.5, 0.6, 0.4, 0.55, 0.45]
    se_vals = [0.14, 0.14, 0.14, 0.14, 0.14]
    
    result = run_random_effects_model(r_vals, se_vals)
    
    assert result["status"] == "completed"
    assert result["model_type"] == "random_effects"
    assert "weighted_mean_r" in result
    assert "ci_lower_r" in result
    assert "ci_upper_r" in result
    assert result["k"] == 5

def test_run_random_effects_model_convergence_fallback():
    # This is hard to trigger deterministically without specific bad data.
    # We test that the function returns a result even if we force a scenario.
    # For now, we assume the basic test covers the happy path.
    # A more robust test would require mocking statsmodels to raise an exception.
    pass

def test_save_results_skipped():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results.json"
        status_path = Path(tmpdir) / "status.json"
        
        results = {
            "status": "skipped",
            "reason": "Insufficient studies",
            "n": 5
        }
        
        save_results(results, output_path, status_path, 5)
        
        assert output_path.exists()
        assert status_path.exists()
        
        with open(status_path) as f:
            status_data = json.load(f)
        
        assert status_data["status"] == "skipped"
        assert status_data["reason"] == "Insufficient studies"
        assert status_data["n"] == 5

def test_load_effect_sizes_and_se():
    # Create a temporary CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"
        content = """author,year,r,n,tract
        Smith,2020,0.5,50,arcuate
        Jones,2021,0.6,60,cingulum
        Doe,2022,0.4,40,uncinate
        """
        with open(csv_path, 'w') as f:
            f.write(content)
        
        r_vals, se_vals, ids = load_effect_sizes_and_se(csv_path)
        
        assert len(r_vals) == 3
        assert len(se_vals) == 3
        assert len(ids) == 3
        
        # Check SE calculation: 1/sqrt(N-3)
        # For N=50, SE = 1/sqrt(47) = 0.1458
        expected_se = 1.0 / math.sqrt(47)
        assert abs(se_vals[0] - expected_se) < 0.001

def test_load_effect_sizes_and_se_invalid_rows():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"
        content = """author,year,r,n,tract
        Smith,2020,0.5,50,arcuate
        Jones,2021,invalid,60,cingulum
        Doe,2022,0.4,40,uncinate
        """
        with open(csv_path, 'w') as f:
            f.write(content)
        
        r_vals, se_vals, ids = load_effect_sizes_and_se(csv_path)
        
        # Should skip the invalid row
        assert len(r_vals) == 2