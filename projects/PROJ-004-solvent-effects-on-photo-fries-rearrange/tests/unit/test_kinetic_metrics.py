import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.kinetic_metrics import (
    load_kinetic_results,
    load_outlier_flags,
    aggregate_metrics,
    write_metrics_csv
)
from config import get_processed_data_path

@pytest.fixture
def mock_kinetic_results():
    """Create mock kinetic fit results data"""
    return [
        {
            "solvent": "hexane",
            "replicate_id": 1,
            "lifetime_ns": 12.5,
            "ci_lower": 11.8,
            "ci_upper": 13.2,
            "outlier_flag": False
        },
        {
            "solvent": "hexane",
            "replicate_id": 2,
            "lifetime_ns": 12.8,
            "ci_lower": 12.1,
            "ci_upper": 13.5,
            "outlier_flag": False
        },
        {
            "solvent": "hexane",
            "replicate_id": 3,
            "lifetime_ns": 12.6,
            "ci_lower": 11.9,
            "ci_upper": 13.3,
            "outlier_flag": False
        },
        {
            "solvent": "acetonitrile",
            "replicate_id": 1,
            "lifetime_ns": 8.2,
            "ci_lower": 7.5,
            "ci_upper": 8.9,
            "outlier_flag": False
        },
        {
            "solvent": "acetonitrile",
            "replicate_id": 2,
            "lifetime_ns": 8.5,
            "ci_lower": 7.8,
            "ci_upper": 9.2,
            "outlier_flag": False
        },
        {
            "solvent": "acetonitrile",
            "replicate_id": 3,
            "lifetime_ns": 25.0,  # Outlier
            "ci_lower": 24.3,
            "ci_upper": 25.7,
            "outlier_flag": True
        }
    ]

@pytest.fixture
def mock_outlier_flags():
    """Create mock outlier flags data"""
    return [
        {
            "solvent": "acetonitrile",
            "replicate_id": 3,
            "is_outlier": True,
            "method": "IQR",
            "threshold": 1.5
        }
    ]

@pytest.fixture
def temp_processed_dir(mock_kinetic_results, mock_outlier_flags):
    """Create a temporary processed directory with mock data files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Mock config to use temp directory
        import config
        original_get_processed = config.get_processed_data_path
        
        def mock_get_processed():
            return tmpdir_path
        
        config.get_processed_data_path = mock_get_processed
        
        # Write mock data files
        results_file = tmpdir_path / "kinetic_fit_results.json"
        with open(results_file, 'w') as f:
            json.dump(mock_kinetic_results, f)
        
        flags_file = tmpdir_path / "outlier_flags.json"
        with open(flags_file, 'w') as f:
            json.dump(mock_outlier_flags, f)
        
        yield tmpdir_path
        
        # Restore original function
        config.get_processed_data_path = original_get_processed

def test_load_kinetic_results_success(temp_processed_dir):
    """Test successful loading of kinetic results"""
    df = load_kinetic_results()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6
    assert 'solvent' in df.columns
    assert 'lifetime_ns' in df.columns
    assert 'ci_lower' in df.columns
    assert 'ci_upper' in df.columns
    assert 'outlier_flag' in df.columns
    
    # Check values
    assert df['solvent'].nunique() == 2
    assert set(df['solvent'].unique()) == {'hexane', 'acetonitrile'}

def test_load_kinetic_results_missing_file():
    """Test error when results file is missing"""
    import config
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config.get_processed_data_path = lambda: tmpdir_path
        
        with pytest.raises(FileNotFoundError, match="Kinetic fit results not found"):
            load_kinetic_results()

def test_load_outlier_flags_success(temp_processed_dir):
    """Test successful loading of outlier flags"""
    df = load_outlier_flags()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert 'solvent' in df.columns
    assert 'is_outlier' in df.columns
    assert df['is_outlier'].iloc[0] == True

def test_load_outlier_flags_missing_file():
    """Test empty DataFrame when flags file is missing"""
    import config
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        config.get_processed_data_path = lambda: tmpdir_path
        
        # Remove the flags file if it exists
        flags_file = tmpdir_path / "outlier_flags.json"
        if flags_file.exists():
            flags_file.unlink()
        
        df = load_outlier_flags()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

def test_aggregate_metrics(temp_processed_dir):
    """Test aggregation of metrics per solvent"""
    results_df = load_kinetic_results()
    metrics_df = aggregate_metrics(results_df)
    
    assert isinstance(metrics_df, pd.DataFrame)
    assert len(metrics_df) == 2  # Two solvents
    
    # Check required columns
    required_cols = [
        'solvent', 'mean_lifetime_ns', 'std_lifetime_ns',
        'replicate_count', 'ci_lower_mean', 'ci_upper_mean'
    ]
    for col in required_cols:
        assert col in metrics_df.columns
    
    # Check hexane statistics (should have 3 replicates, no outliers)
    hexane_row = metrics_df[metrics_df['solvent'] == 'hexane'].iloc[0]
    assert hexane_row['replicate_count'] == 3
    assert np.isclose(hexane_row['mean_lifetime_ns'], 12.633, rtol=0.01)
    
    # Check acetonitrile statistics (should have 2 replicates after outlier removal)
    acn_row = metrics_df[metrics_df['solvent'] == 'acetonitrile'].iloc[0]
    assert acn_row['replicate_count'] == 2  # One outlier removed
    assert np.isclose(acn_row['mean_lifetime_ns'], 8.35, rtol=0.01)

def test_aggregate_metrics_empty_data():
    """Test aggregation with empty DataFrame"""
    empty_df = pd.DataFrame(columns=['solvent', 'replicate_id', 'lifetime_ns', 'ci_lower', 'ci_upper', 'outlier_flag'])
    
    metrics_df = aggregate_metrics(empty_df)
    assert isinstance(metrics_df, pd.DataFrame)
    assert len(metrics_df) == 0

def test_write_metrics_csv(temp_processed_dir):
    """Test writing metrics to CSV"""
    results_df = load_kinetic_results()
    metrics_df = aggregate_metrics(results_df)
    
    output_file = temp_processed_dir / "test_metrics.csv"
    written_file = write_metrics_csv(metrics_df, output_file)
    
    assert written_file.exists()
    assert written_file == output_file
    
    # Verify CSV content
    loaded_df = pd.read_csv(written_file)
    assert len(loaded_df) == len(metrics_df)
    assert list(loaded_df.columns) == list(metrics_df.columns)