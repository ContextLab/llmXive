import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_csv_schema():
    """Test that CSV output matches expected schema."""
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / 'data' / 'benchmark_results.csv'
    
    # Skip test if file doesn't exist yet
    if not csv_path.exists():
        pytest.skip("CSV file not found - run benchmarks first")
    
    df = pd.read_csv(csv_path)
    
    # Check required columns
    expected_columns = ['thread_count', 'configuration', 'iteration_count', 'wall_clock_time_ms']
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check data types
    assert df['thread_count'].dtype in ['int64', 'int32'], "thread_count should be integer"
    assert df['configuration'].dtype == 'object', "configuration should be string"
    assert df['iteration_count'].dtype in ['int64', 'int32'], "iteration_count should be integer"
    assert df['wall_clock_time_ms'].dtype in ['float64', 'float32'], "wall_clock_time_ms should be float"
    
    # Check valid values
    assert all(df['thread_count'].isin([2, 4, 8])), "thread_count must be 2, 4, or 8"
    assert all(df['configuration'].isin(['packed', 'padded'])), "configuration must be 'packed' or 'padded'"
    assert all(df['wall_clock_time_ms'] > 0), "wall_clock_time_ms must be positive"

def test_minimum_samples():
    """Test that we have at least 5 samples per configuration."""
    project_root = Path(__file__).parent.parent.parent
    csv_path = project_root / 'data' / 'benchmark_results.csv'
    
    if not csv_path.exists():
        pytest.skip("CSV file not found - run benchmarks first")
    
    df = pd.read_csv(csv_path)
    
    for config in ['packed', 'padded']:
        for thread_count in [2, 4, 8]:
            subset = df[(df['configuration'] == config) & (df['thread_count'] == thread_count)]
            assert len(subset) >= 5, f"Expected at least 5 samples for {config} at {thread_count} threads, got {len(subset)}"
