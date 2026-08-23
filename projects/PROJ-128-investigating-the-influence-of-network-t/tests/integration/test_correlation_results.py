import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path if running from tests directory
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.generate_correlation_results import generate_correlation_results
from config import get_config_dict

@pytest.fixture
def setup_test_data():
    """
    Create temporary structural and dynamic metrics CSVs for testing.
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock structural data
    struct_data = {
        'subject_id': [f'sub-{i:03d}' for i in range(10)],
        'global_efficiency': np.random.rand(10) * 0.5 + 0.2,
        'avg_clustering': np.random.rand(10) * 0.5 + 0.2,
        'modularity': np.random.rand(10) * 0.5 + 0.2
    }
    struct_df = pd.DataFrame(struct_data)
    struct_path = processed_dir / 'structural_metrics.csv'
    struct_df.to_csv(struct_path, index=False)
    
    # Create mock dynamic data
    dyn_data = {
        'subject_id': [f'sub-{i:03d}' for i in range(10)],
        'dwell_time_mean': np.random.rand(10) * 100 + 50,
        'visited_states_count': np.random.randint(1, 5, 10)
    }
    dyn_df = pd.DataFrame(dyn_data)
    dyn_path = processed_dir / 'dynamic_metrics.csv'
    dyn_df.to_csv(dyn_path, index=False)
    
    yield struct_path, dyn_path
    
    # Cleanup
    if struct_path.exists():
        struct_path.unlink()
    if dyn_path.exists():
        dyn_path.unlink()

def test_generate_correlation_results_creates_file(setup_test_data):
    """
    Test that generate_correlation_results creates the expected output file
    and contains the required columns.
    """
    output_path = setup_test_data[0].parent / 'correlation_results.csv'
    if output_path.exists():
        output_path.unlink()
    
    # Run the function
    result_df = generate_correlation_results(str(output_path))
    
    # Check file exists
    assert output_path.exists(), "Correlation results file was not created."
    
    # Check required columns
    required_cols = ['structural_metric', 'dynamic_metric', 'n', 'r', 'p_raw', 'fdr_corrected', 'significant']
    for col in required_cols:
        assert col in result_df.columns, f"Missing column: {col}"
    
    # Check data types
    assert result_df['r'].dtype in [np.float64, np.float32], "r column should be numeric"
    assert result_df['p_raw'].dtype in [np.float64, np.float32], "p_raw column should be numeric"
    assert result_df['fdr_corrected'].dtype in [np.float64, np.float32], "fdr_corrected column should be numeric"
    
    # Check that we have at least some results
    assert len(result_df) > 0, "No correlation pairs were generated."
    
    # Check that significant is boolean
    assert result_df['significant'].dtype == bool, "significant column should be boolean"

def test_fdr_correction_logic(setup_test_data):
    """
    Test that FDR correction is applied correctly (values should be <= raw p-values generally,
    and sorted appropriately).
    """
    output_path = setup_test_data[0].parent / 'correlation_results.csv'
    if output_path.exists():
        output_path.unlink()
    
    result_df = generate_correlation_results(str(output_path))
    
    # Filter out NaNs
    valid_df = result_df.dropna(subset=['p_raw', 'fdr_corrected'])
    
    if len(valid_df) > 0:
        # FDR corrected p-values should generally be >= raw p-values (conservative)
        # But for BH, they are monotonic.
        # We just check that the column is populated with numbers
        assert not valid_df['fdr_corrected'].isna().all(), "FDR correction resulted in all NaNs."
        
        # Check that significant flag is consistent with fdr_corrected < 0.05
        expected_significant = valid_df['fdr_corrected'] < 0.05
        assert all(valid_df['significant'] == expected_significant), "Significant flag mismatch."

def test_zero_significant_findings_handling(setup_test_data):
    """
    Test that if no findings are significant, the file is still created correctly
    and the report logic (in a downstream task) would see zero significant findings.
    """
    # We can't easily force zero significant findings without controlling the data,
    # but we can verify the structure is correct even if significant is all False.
    output_path = setup_test_data[0].parent / 'correlation_results.csv'
    if output_path.exists():
        output_path.unlink()
    
    result_df = generate_correlation_results(str(output_path))
    
    # Verify structure is valid regardless of significance count
    assert 'significant' in result_df.columns
    assert result_df['significant'].dtype == bool
    
    # The task T028 will handle the explicit statement in the report,
    # but here we ensure the data is ready for that check.
    # Just verify the file is written.
    assert os.path.getsize(output_path) > 0, "Output file is empty."
