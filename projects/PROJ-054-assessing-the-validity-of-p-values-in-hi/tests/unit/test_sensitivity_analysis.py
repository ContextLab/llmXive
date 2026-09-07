"""
Unit tests for T031: Sensitivity Analysis Sweep.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from sensitivity_analysis import (
    load_ks_stats, 
    calculate_ks_statistic_for_rho, 
    select_worst_case, 
    run_sensitivity_analysis
)

@pytest.fixture
def mock_ks_data(tmp_path):
    """Create a mock ks_stats.json file for testing."""
    data = {
        "seed_1": {"seed": 1, "n": 100, "p": 1000, "rho": 0.0, "ks_stat": 0.05},
        "seed_2": {"seed": 2, "n": 100, "p": 2000, "rho": 0.0, "ks_stat": 0.08}, # Higher p/n, same rho
        "seed_3": {"seed": 3, "n": 100, "p": 1000, "rho": 0.0, "ks_stat": 0.08}, # Same KS, lower p/n
        "seed_4": {"seed": 4, "n": 100, "p": 1000, "rho": 0.5, "ks_stat": 0.12},
        "seed_5": {"seed": 5, "n": 100, "p": 1000, "rho": 0.9, "ks_stat": 0.25},
    }
    file_path = tmp_path / "ks_stats.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def mock_ks_data_missing(tmp_path):
    """Create a mock ks_stats.json with missing rho."""
    data = {
        "seed_1": {"seed": 1, "n": 100, "p": 1000, "rho": 0.0, "ks_stat": 0.05},
    }
    file_path = tmp_path / "ks_stats.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def test_load_ks_stats_success(mock_ks_data):
    """Test loading valid JSON."""
    # Temporarily patch the global path for testing
    import sensitivity_analysis as sa
    original_path = sa.KS_STATS_PATH
    sa.KS_STATS_PATH = mock_ks_data
    
    try:
        result = load_ks_stats()
        assert isinstance(result, dict)
        assert len(result) == 5
        assert result['seed_4']['rho'] == 0.5
    finally:
        sa.KS_STATS_PATH = original_path

def test_load_ks_stats_file_not_found():
    """Test loading non-existent file."""
    import sensitivity_analysis as sa
    original_path = sa.KS_STATS_PATH
    sa.KS_STATS_PATH = Path("/nonexistent/path/file.json")
    
    try:
        with pytest.raises(FileNotFoundError):
            load_ks_stats()
    finally:
        sa.KS_STATS_PATH = original_path

def test_calculate_ks_statistic_for_rho(mock_ks_data):
    """Test filtering by rho."""
    import sensitivity_analysis as sa
    original_path = sa.KS_STATS_PATH
    sa.KS_STATS_PATH = mock_ks_data
    
    try:
        result = calculate_ks_statistic_for_rho(load_ks_stats(), 0.0)
        assert len(result) == 3
        assert all(r['rho'] == 0.0 for r in result)
        
        result_05 = calculate_ks_statistic_for_rho(load_ks_stats(), 0.5)
        assert len(result_05) == 1
        assert result_05[0]['seed'] == 4
    finally:
        sa.KS_STATS_PATH = original_path

def test_select_worst_case_tie_breaking(mock_ks_data):
    """Test tie-breaking logic: max KS -> max p/n -> max rho."""
    # Candidates for rho=0.0
    candidates = [
        {"seed": 1, "n": 100, "p": 1000, "rho": 0.0, "ks_stat": 0.05}, # Lower KS
        {"seed": 2, "n": 100, "p": 2000, "rho": 0.0, "ks_stat": 0.08}, # Max KS, Max p/n
        {"seed": 3, "n": 100, "p": 1000, "rho": 0.0, "ks_stat": 0.08}, # Max KS, Lower p/n
    ]
    
    winner = select_worst_case(candidates, 0.0)
    
    assert winner is not None
    assert winner['seed'] == 2, "Should pick seed 2 (highest p/n among max KS)"
    assert winner['worst_case_flag'] is True

def test_select_worst_case_empty():
    """Test with empty candidates."""
    winner = select_worst_case([], 0.5)
    assert winner is None

def test_run_sensitivity_analysis_integration(mock_ks_data, tmp_path):
    """Test the full run_sensitivity_analysis flow."""
    import sensitivity_analysis as sa
    original_path = sa.KS_STATS_PATH
    original_output = sa.OUTPUT_PATH
    
    sa.KS_STATS_PATH = mock_ks_data
    sa.OUTPUT_PATH = tmp_path / "sensitivity.csv"
    
    try:
        run_sensitivity_analysis()
        assert sa.OUTPUT_PATH.exists()
        
        # Read and verify content
        with open(sa.OUTPUT_PATH, 'r') as f:
            content = f.read()
        
        assert "rho,n,p,ks_stat,worst_case_flag" in content
        assert "0.0" in content
        assert "0.5" in content
        assert "0.9" in content
        
        # Verify specific values
        lines = content.strip().split('\n')
        # Header + 3 rows (0.0, 0.5, 0.9)
        assert len(lines) == 4 
    finally:
        sa.KS_STATS_PATH = original_path
        sa.OUTPUT_PATH = original_output
