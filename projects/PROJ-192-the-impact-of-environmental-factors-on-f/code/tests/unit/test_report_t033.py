import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.pipelines.report import run_threshold_sweep, load_permanova_results, apply_fdr_correction

@pytest.fixture
def sample_permanova_data():
    """Create a sample PERMANOVA DataFrame for testing."""
    data = {
        'term': ['pH', 'Nutrients', 'Moisture', 'Temperature'],
        'R2': [0.25, 0.15, 0.10, 0.05],
        'p-value': [0.001, 0.02, 0.04, 0.15],
        'p-value_adj': [0.002, 0.03, 0.06, 0.20]
    }
    return pd.DataFrame(data)

def test_threshold_sweep_basic(sample_permanova_data):
    """Test basic threshold sweep functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_permanova_data.to_csv(input_path, index=False)
        
        result_df = run_threshold_sweep(
            str(input_path), 
            str(output_path),
            p_value_thresholds=[0.05],
            r2_thresholds=[0.1]
        )
        
        assert os.path.exists(output_path)
        assert len(result_df) > 0
        assert 'p_value_threshold' in result_df.columns
        assert 'r2_threshold' in result_df.columns
        assert 'top_driver' in result_df.columns
        
        # With p<=0.05 and R2>=0.1, we should have pH, Nutrients, Moisture
        # Top driver should be pH (highest R2)
        row = result_df.iloc[0]
        assert row['p_value_threshold'] == 0.05
        assert row['r2_threshold'] == 0.1
        assert row['top_driver'] == 'pH'

def test_threshold_sweep_strict(sample_permanova_data):
    """Test with strict thresholds that might yield no results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_permanova_data.to_csv(input_path, index=False)
        
        # Very strict thresholds: p<=0.001 and R2>=0.3 (only pH has R2=0.25, so none match R2)
        result_df = run_threshold_sweep(
            str(input_path),
            str(output_path),
            p_value_thresholds=[0.001],
            r2_thresholds=[0.3]
        )
        
        assert os.path.exists(output_path)
        # Should have one row, but top_driver should be "None"
        row = result_df.iloc[0]
        assert row['top_driver'] == 'None'
        assert row['significant_terms_count'] == 0

def test_threshold_sweep_multiple_thresholds(sample_permanova_data):
    """Test with multiple thresholds to ensure iteration works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_permanova_data.to_csv(input_path, index=False)
        
        p_thresholds = [0.01, 0.05]
        r2_thresholds = [0.1, 0.2]
        
        result_df = run_threshold_sweep(
            str(input_path),
            str(output_path),
            p_value_thresholds=p_thresholds,
            r2_thresholds=r2_thresholds
        )
        
        # Expect 2 * 2 = 4 rows
        assert len(result_df) == 4
        
        # Check that all combinations are present
        combinations = set(zip(result_df['p_value_threshold'], result_df['r2_threshold']))
        expected_combinations = set([(p, r) for p in p_thresholds for r in r2_thresholds])
        assert combinations == expected_combinations

def test_threshold_sweep_with_fdr_correction(sample_permanova_data):
    """Test that FDR correction is applied when requested."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        sample_permanova_data.to_csv(input_path, index=False)
        
        # Use FDR (default is True)
        result_df = run_threshold_sweep(
            str(input_path),
            str(output_path),
            p_value_thresholds=[0.05],
            r2_thresholds=[0.1],
            use_fdr=True
        )
        
        # With FDR, p-value_adj for Moisture is 0.06, so it should be excluded at p<=0.05
        # Only pH (0.002) and Nutrients (0.03) should be included
        # Top driver should still be pH
        row = result_df.iloc[0]
        assert row['top_driver'] == 'pH'
        # Should have 2 significant terms (pH and Nutrients)
        assert row['significant_terms_count'] == 2

def test_threshold_sweep_empty_input():
    """Test handling of empty input data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        # Create empty DataFrame with required columns
        empty_df = pd.DataFrame(columns=['term', 'R2', 'p-value', 'p-value_adj'])
        empty_df.to_csv(input_path, index=False)
        
        result_df = run_threshold_sweep(
            str(input_path),
            str(output_path),
            p_value_thresholds=[0.05],
            r2_thresholds=[0.1]
        )
        
        assert os.path.exists(output_path)
        assert len(result_df) > 0
        # Top driver should be "None" for all
        assert all(result_df['top_driver'] == 'None')