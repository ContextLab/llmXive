"""
Tests for the quality report generation in filter.py
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.filter import apply_filter_to_dataset, write_quality_report
from logging_config import LoggingContext

def test_quality_report_initialization():
    """Test that LoggingContext initializes and writes headers correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "quality_report.csv")
        
        # Initialize context and write report
        context = LoggingContext()
        write_quality_report(context, report_path)
        
        # Verify file exists and has correct headers
        assert os.path.exists(report_path)
        df = pd.read_csv(report_path)
        assert list(df.columns) == ['exclusion_type', 'count']
        assert len(df) == 0  # No exclusions yet

def test_quality_report_add_exclusion():
    """Test that add_exclusion properly tracks exclusions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "quality_report.csv")
        
        context = LoggingContext()
        
        # Add some exclusions
        context.add_exclusion(type="blink_interpolation", count=10, reason="Test blink")
        context.add_exclusion(type="missing_data_threshold", count=1, reason="Test missing")
        context.add_exclusion(type="blink_interpolation", count=5, reason="Another blink")
        
        write_quality_report(context, report_path)
        
        # Verify report content
        df = pd.read_csv(report_path)
        assert len(df) == 3
        
        # Check specific entries
        blink_rows = df[df['exclusion_type'] == 'blink_interpolation']
        assert len(blink_rows) == 2
        assert blink_rows.iloc[0]['count'] == 10
        assert blink_rows.iloc[1]['count'] == 5

def test_apply_filter_to_dataset_with_logging():
    """Test that apply_filter_to_dataset correctly logs exclusions."""
    # Create synthetic data with some missing values and blinks
    n_samples = 1000
    timestamps = np.arange(n_samples)
    pupil_data = np.random.normal(5.0, 0.5, n_samples)
    
    # Simulate some missing data (blinks)
    pupil_data[100:110] = np.nan
    pupil_data[200:215] = np.nan
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'pupil_diameter': pupil_data,
        'x': np.random.rand(n_samples),
        'y': np.random.rand(n_samples)
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "quality_report.csv")
        
        context = LoggingContext()
        
        # Process data with logging
        processed_df, metrics = apply_filter_to_dataset(
            df, fs=1000.0, logging_context=context
        )
        
        # Write report
        write_quality_report(context, report_path)
        
        # Verify report was created
        assert os.path.exists(report_path)
        report_df = pd.read_csv(report_path)
        
        # Verify exclusions were logged
        assert len(report_df) > 0
        
        # Check that missing data was logged
        missing_rows = report_df[report_df['exclusion_type'].str.contains('missing', case=False)]
        assert len(missing_rows) > 0

def test_apply_filter_to_dataset_exclusion_threshold():
    """Test that datasets with too much missing data are excluded."""
    # Create data with >30% missing
    n_samples = 100
    pupil_data = np.random.normal(5.0, 0.5, n_samples)
    pupil_data[35:100] = np.nan  # 65% missing
    
    df = pd.DataFrame({
        'timestamp': np.arange(n_samples),
        'pupil_diameter': pupil_data,
        'x': np.random.rand(n_samples),
        'y': np.random.rand(n_samples)
    })
    
    context = LoggingContext()
    
    # Process with default max_missing_ratio=0.30
    processed_df, metrics = apply_filter_to_dataset(
        df, fs=1000.0, logging_context=context
    )
    
    # Verify exclusion was logged
    write_quality_report(context, "/tmp/test_report.csv")
    report_df = pd.read_csv("/tmp/test_report.csv")
    
    exclusion_rows = report_df[report_df['exclusion_type'] == 'missing_data_threshold']
    assert len(exclusion_rows) == 1
    assert metrics['excluded'] is True

def test_write_quality_report_empty_context():
    """Test writing report with no exclusions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "quality_report.csv")
        
        context = LoggingContext()
        write_quality_report(context, report_path)
        
        df = pd.read_csv(report_path)
        assert len(df) == 0
        assert list(df.columns) == ['exclusion_type', 'count']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])