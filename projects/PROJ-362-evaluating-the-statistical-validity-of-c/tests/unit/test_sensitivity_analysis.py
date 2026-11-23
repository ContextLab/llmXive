import pytest
import csv
import os
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from sensitivity_analysis import load_corrected_p_values, determine_significance, run_sensitivity_analysis

@pytest.fixture
def mock_corrected_p_values(tmp_path):
    """Creates a temporary CSV file with mock corrected p-values."""
    csv_path = tmp_path / "corrected_p_values.csv"
    data = [
        {"query_id": "q1", "metric": "NDCG@10", "raw_p": "0.05", "corrected_p": "0.08", "is_significant": "False"},
        {"query_id": "q1", "metric": "MAP", "corrected_p": "0.02", "raw_p": "0.01", "is_significant": "True"},
        {"query_id": "q2", "metric": "NDCG@10", "corrected_p": "0.15", "raw_p": "0.10", "is_significant": "False"},
        {"query_id": "q2", "metric": "MAP", "corrected_p": "0.03", "raw_p": "0.02", "is_significant": "True"},
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writeall(data)
    return str(csv_path)

def test_determine_significance():
    assert determine_significance(0.04, 0.05) == True
    assert determine_significance(0.06, 0.05) == False
    assert determine_significance(0.05, 0.05) == False  # Strict inequality <

def test_load_corrected_p_values(mock_corrected_p_values):
    data = load_corrected_p_values(mock_corrected_p_values)
    assert len(data) == 4
    assert data[0]['metric'] == "NDCG@10"
    assert data[1]['metric'] == "MAP"

def test_sensitivity_analysis_logic(mock_corrected_p_values, tmp_path):
    """
    Tests the logic of the sensitivity analysis.
    We simulate a sweep where significance changes.
    """
    # Mock the load function to use our temp file
    # Note: In a real scenario, we would patch the function or pass the path directly
    # For this unit test, we assume the function logic is correct and test the output structure
    # by mocking the load call or by directly calling the internal logic if exposed.
    # Since run_sensitivity_analysis calls load_corrected_p_values internally, we need to patch it
    # or ensure the file exists in the expected location.
    # For simplicity, we will test the core logic by calling run_sensitivity_analysis
    # but we need to ensure the file is at the expected location or patch the loader.
    
    # Patching the load function to return our test data directly
    original_load = load_corrected_p_values
    
    def mock_load(filepath=None):
        return [
            {"query_id": "q1", "metric": "NDCG@10", "corrected_p": 0.04, "raw_p": 0.04, "is_significant": True},
            {"query_id": "q1", "metric": "MAP", "corrected_p": 0.06, "raw_p": 0.06, "is_significant": False},
        ]
    
    # Temporarily replace the function
    import sensitivity_analysis as sa_module
    sa_module.load_corrected_p_values = mock_load

    try:
        # Run with a specific range to ensure we hit a change
        # Set global config for the test
        sa_module.ALPHA_SWEEP_START = 0.03
        sa_module.ALPHA_SWEEP_END = 0.07
        sa_module.ALPHA_SWEEP_STEP = 0.01

        results = run_sensitivity_analysis()
        
        assert len(results) > 0
        # Check structure
        for res in results:
            assert 'alpha' in res
            assert 'significant_count' in res
            assert 'status_change_count' in res
        
        # Verify logic:
        # At alpha=0.03: q1(NDCG) 0.04>0.03 (False), q1(MAP) 0.06>0.03 (False). Sig=0.
        # At alpha=0.04: q1(NDCG) 0.04<0.04 (False), q1(MAP) 0.06>0.04 (False). Sig=0.
        # At alpha=0.05: q1(NDCG) 0.04<0.05 (True), q1(MAP) 0.06>0.05 (False). Sig=1. Change from prev=1.
        # At alpha=0.06: q1(NDCG) 0.04<0.06 (True), q1(MAP) 0.06<0.06 (False). Sig=1. Change from prev=0.
        # At alpha=0.07: q1(NDCG) 0.04<0.07 (True), q1(MAP) 0.06<0.07 (True). Sig=2. Change from prev=1.
        
        # Find the entry for alpha=0.05
        res_05 = next((r for r in results if abs(r['alpha'] - 0.05) < 0.001), None)
        assert res_05 is not None
        assert res_05['significant_count'] == 1
        assert res_05['status_change_count'] == 1

    finally:
        # Restore original function
        sa_module.load_corrected_p_values = original_load
