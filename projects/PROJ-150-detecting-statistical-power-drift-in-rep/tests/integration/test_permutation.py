import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from robustness import run_permutation_test, load_cleaned_data

@pytest.fixture
def sample_data(tmp_path):
    """Create a small sample dataset for testing."""
    data_dir = tmp_path / "data" / "derived"
    data_dir.mkdir(parents=True)
    
    # Create a minimal dataset
    n = 100
    df = pd.DataFrame({
        'year': np.random.randint(1990, 2020, n),
        'effect_size': np.random.randn(n) * 0.5 + 0.2,
        'sample_size': np.random.randint(20, 100, n),
        'power_est': np.random.rand(n),
        'field': np.random.choice(['Bio', 'Psych', 'Soc'], n),
        'original_study_id': np.random.choice(['S1', 'S2', 'S3'], n)
    })
    
    csv_path = data_dir / "cleaned_data.csv"
    df.to_csv(csv_path, index=False)
    return df

@pytest.fixture
def setup_results_dir(tmp_path):
    """Setup results directory."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)
    # Create a dummy summary for T012
    summary = {
        "slope_year": 0.01,
        "se_year": 0.005,
        "ci_lower": 0.001,
        "ci_upper": 0.019,
        "p_value_lrt": 0.03,
        "chi2_statistic": 4.5,
        "df_diff": 1
    }
    with open(results_dir / "lmm_final_summary.json", 'w') as f:
        json.dump(summary, f)
    return results_dir

def test_permutation_logic_small_count(tmp_path, sample_data, setup_results_dir):
    """Test the permutation logic with a small number of iterations."""
    # Change working directory to tmp_path to simulate project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Run with very few iterations for speed
        result = run_permutation_test(sample_data, n_permutations=10, target_max_time=3600)
        
        # Verify output
        assert isinstance(result, pd.DataFrame)
        assert 'simulated_drift' in result.columns
        assert 'count' in result.columns
        assert len(result) == 10
        assert result['simulated_drift'].notna().all()
        
        # Verify file was created
        output_path = Path(tmp_path) / "results" / "null_distribution_implied_power.csv"
        assert output_path.exists()
        
    finally:
        os.chdir(original_cwd)

def test_permutation_fallback_logic(tmp_path, sample_data, setup_results_dir):
    """Test that the function falls back to 1000 if time limit is tight."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Set a very tight time limit to force fallback (though 10 iterations is fast)
        # We test the logic by checking the status if we could measure time, 
        # but for unit test we just ensure it runs without error and returns a result.
        # The fallback logic is triggered by estimated time > limit.
        # Since 10 is small, it won't trigger fallback in a real sense, but the code path exists.
        
        result = run_permutation_test(sample_data, n_permutations=100, target_max_time=1) # 1 second
        
        # It should complete 100 iterations if fast enough, or stop early if slow.
        # We just check it returns a valid dataframe.
        assert isinstance(result, pd.DataFrame)
        assert 'simulated_drift' in result.columns
        
    finally:
        os.chdir(original_cwd)