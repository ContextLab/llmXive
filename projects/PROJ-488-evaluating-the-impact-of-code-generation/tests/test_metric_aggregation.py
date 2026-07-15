"""
Tests for metric aggregation module (T023).
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metric_aggregation import (
    load_metrics_for_group,
    aggregate_metrics,
    write_aggregate_csv,
    run_aggregation
)

def test_load_metrics_for_group():
    """Test loading metrics for a specific group."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir)
        
        # Create mock metric files
        human_df = pd.DataFrame({
            'snippet_id': ['h1', 'h2', 'h3'],
            'cyclomatic_complexity': [5, 8, 3],
            'maintainability_index': [45.2, 38.7, 52.1]
        })
        human_df.to_csv(metrics_dir / "human_cyclomatic_metrics.csv", index=False)
        human_df.to_csv(metrics_dir / "human_maintainability_metrics.csv", index=False)
        
        codegen_df = pd.DataFrame({
            'snippet_id': ['c1', 'c2', 'c3'],
            'cyclomatic_complexity': [7, 9, 6],
            'maintainability_index': [42.1, 35.5, 40.8]
        })
        codegen_df.to_csv(metrics_dir / "codegen_cyclomatic_metrics.csv", index=False)
        codegen_df.to_csv(metrics_dir / "codegen_maintainability_metrics.csv", index=False)
        
        # Test loading human group
        df = load_metrics_for_group('human', metrics_dir)
        assert df is not None, "Failed to load human metrics"
        assert len(df) == 6, f"Expected 6 rows, got {len(df)}"
        assert 'group' in df.columns, "Group column missing"
        assert all(df['group'] == 'human'), "Group values incorrect"
        
        # Test loading codegen group
        df = load_metrics_for_group('codegen', metrics_dir)
        assert df is not None, "Failed to load codegen metrics"
        assert len(df) == 6, f"Expected 6 rows, got {len(df)}"
        
        # Test non-existent group
        df = load_metrics_for_group('nonexistent', metrics_dir)
        assert df is None, "Should return None for non-existent group"
        
    print("✓ test_load_metrics_for_group passed")

def test_aggregate_metrics():
    """Test metric aggregation calculations."""
    df = pd.DataFrame({
        'snippet_id': ['s1', 's2', 's3', 's4', 's5'],
        'metric_a': [10.0, 20.0, 30.0, 40.0, 50.0],
        'metric_b': [5.0, 5.0, 5.0, 5.0, 5.0]
    })
    
    aggregates = aggregate_metrics(df, ['metric_a', 'metric_b'])
    
    assert 'metric_a' in aggregates, "metric_a missing from aggregates"
    assert 'metric_b' in aggregates, "metric_b missing from aggregates"
    
    # Check metric_a stats
    assert abs(aggregates['metric_a']['mean'] - 30.0) < 0.01, "Mean incorrect"
    assert abs(aggregates['metric_a']['median'] - 30.0) < 0.01, "Median incorrect"
    assert abs(aggregates['metric_a']['variance'] - 250.0) < 0.01, "Variance incorrect"
    assert aggregates['metric_a']['count'] == 5, "Count incorrect"
    
    # Check metric_b stats (constant value)
    assert abs(aggregates['metric_b']['mean'] - 5.0) < 0.01, "Mean incorrect"
    assert abs(aggregates['metric_b']['median'] - 5.0) < 0.01, "Median incorrect"
    assert aggregates['metric_b']['variance'] == 0.0, "Variance should be 0 for constant"
    
    print("✓ test_aggregate_metrics passed")

def test_write_aggregate_csv():
    """Test writing aggregated metrics to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_aggregated.csv"
        
        aggregates = {
            'metric_a': {
                'mean': 30.0,
                'median': 30.0,
                'variance': 250.0,
                'count': 5,
                'std': 15.811
            },
            'metric_b': {
                'mean': 5.0,
                'median': 5.0,
                'variance': 0.0,
                'count': 5,
                'std': 0.0
            }
        }
        
        success = write_aggregate_csv(aggregates, 'test_group', output_path)
        
        assert success, "Failed to write CSV"
        assert output_path.exists(), "Output file not created"
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 2, "Expected 2 rows"
        assert 'metric_name' in df.columns, "metric_name column missing"
        assert 'group' in df.columns, "group column missing"
        assert 'mean' in df.columns, "mean column missing"
        assert 'median' in df.columns, "median column missing"
        assert 'variance' in df.columns, "variance column missing"
        
        # Verify values
        row_a = df[df['metric_name'] == 'metric_a'].iloc[0]
        assert abs(row_a['mean'] - 30.0) < 0.01, "Mean value incorrect"
        assert row_a['group'] == 'test_group', "Group value incorrect"
        
    print("✓ test_write_aggregate_csv passed")

def test_run_aggregation():
    """Test the full aggregation workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_dir = Path(tmpdir) / "metrics"
        output_dir = Path(tmpdir) / "output"
        metrics_dir.mkdir()
        
        # Create mock data for both groups
        for group in ['human', 'codegen']:
            for metric_type in ['cyclomatic', 'maintainability']:
                df = pd.DataFrame({
                    'snippet_id': [f'{group}{i}' for i in range(10)],
                    f'{metric_type}_score': np.random.rand(10) * 100
                })
                df.to_csv(metrics_dir / f"{group}_{metric_type}_metrics.csv", index=False)
        
        # Run aggregation
        output_files = run_aggregation(metrics_dir, output_dir)
        
        assert 'human' in output_files, "human group not processed"
        assert 'codegen' in output_files, "codegen group not processed"
        assert output_files['human'].exists(), "human output file not created"
        assert output_files['codegen'].exists(), "codegen output file not created"
        
        # Verify content of output files
        for group, path in output_files.items():
            df = pd.read_csv(path)
            assert len(df) > 0, f"No data in {group} output"
            assert 'metric_name' in df.columns, "Missing metric_name column"
            assert 'mean' in df.columns, "Missing mean column"
            assert 'median' in df.columns, "Missing median column"
            assert 'variance' in df.columns, "Missing variance column"
        
    print("✓ test_run_aggregation passed")

if __name__ == "__main__":
    test_load_metrics_for_group()
    test_aggregate_metrics()
    test_write_aggregate_csv()
    test_run_aggregation()
    print("\n✅ All tests passed!")
