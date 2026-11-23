"""
Tests for the sampling and power analysis module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from code.data.sampling import (
    load_extracted_data,
    load_thread_metrics,
    calculate_stratification_grid,
    generate_power_analysis_report,
    update_analysis_summary_with_power_limitations
)


@pytest.fixture
def sample_extracted_data():
    """Create sample extracted thread data."""
    data = {
        'thread_id': [f'thread_{i}' for i in range(100)],
        'subreddit': ['reddit_a' if i % 2 == 0 else 'reddit_b' for i in range(100)],
        'reply_count': np.random.randint(1, 50, 100),
        'is_valid': [True if i % 3 == 0 else False for i in range(100)],
        'is_valid_no_gt': [False if i % 3 == 0 else True for i in range(100)]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_thread_metrics():
    """Create sample thread metrics."""
    data = {
        'thread_id': [f'thread_{i}' for i in range(100)],
        'contagion_index': np.random.uniform(-1, 1, 100),
        'agreement_proportion': np.random.uniform(0, 1, 100),
        'entropy': np.random.uniform(0, 2, 100)
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_extracted_file(sample_extracted_data):
    """Create a temporary file with sample extracted data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_extracted_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_metrics_file(sample_thread_metrics):
    """Create a temporary file with sample thread metrics."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_thread_metrics.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_summary_file():
    """Create a temporary summary file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Analysis Summary\n\n## Introduction\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


def test_load_extracted_data(temp_extracted_file, sample_extracted_data):
    """Test loading extracted thread data."""
    df = load_extracted_data(temp_extracted_file)
    assert len(df) == len(sample_extracted_data)
    assert 'thread_id' in df.columns
    assert 'subreddit' in df.columns


def test_load_thread_metrics(temp_metrics_file, sample_thread_metrics):
    """Test loading thread metrics."""
    df = load_thread_metrics(temp_metrics_file)
    assert len(df) == len(sample_thread_metrics)
    assert 'thread_id' in df.columns
    assert 'contagion_index' in df.columns


def test_load_missing_file():
    """Test that loading a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_extracted_data("/nonexistent/path/file.csv")


def test_calculate_stratification_grid(sample_extracted_data):
    """Test stratification grid calculation."""
    grid = calculate_stratification_grid(sample_extracted_data)

    assert 'stratification_columns' in grid
    assert 'distribution' in grid
    assert 'total_count' in grid
    assert grid['total_count'] == len(sample_extracted_data)

    # Check that distribution includes expected columns
    assert 'subreddit' in grid['distribution']


def test_calculate_stratification_grid_with_thread_length(sample_extracted_data):
    """Test stratification grid with thread length binning."""
    grid = calculate_stratification_grid(sample_extracted_data, ['reply_count'])

    assert 'thread_length_bin' in str(grid['distribution']) or 'reply_count' in grid['distribution']


def test_generate_power_analysis_report(sample_extracted_data):
    """Test power analysis report generation."""
    report = generate_power_analysis_report(sample_extracted_data)

    assert 'total_threads' in report
    assert 'required_sample_size' in report
    assert 'achieved_power' in report
    assert 'power_limitation' in report
    assert 'warning_message' in report

    # Check that total threads matches input
    assert report['total_threads'] == len(sample_extracted_data)


def test_generate_power_analysis_small_sample():
    """Test power analysis with small sample (should trigger warning)."""
    small_data = pd.DataFrame({
        'thread_id': [f't{i}' for i in range(10)],
        'subreddit': ['a'] * 10,
        'reply_count': [5] * 10
    })

    report = generate_power_analysis_report(small_data)

    assert report['power_limitation'] is True
    assert report['warning_message'] is not None
    assert "Power limitation detected" in report['warning_message']


def test_generate_power_analysis_large_sample():
    """Test power analysis with large sample (should not trigger warning)."""
    large_data = pd.DataFrame({
        'thread_id': [f't{i}' for i in range(200)],
        'subreddit': ['a'] * 100 + ['b'] * 100,
        'reply_count': [10] * 200
    })

    report = generate_power_analysis_report(large_data)

    # With 200 samples, power limitation should be False
    assert report['power_limitation'] is False


def test_update_analysis_summary_with_power_limitations(temp_summary_file, sample_extracted_data):
    """Test updating analysis summary with power limitations."""
    report = generate_power_analysis_report(sample_extracted_data)

    # Create a sample report with power limitation
    limited_report = report.copy()
    limited_report['power_limitation'] = True
    limited_report['warning_message'] = "Test power limitation warning"

    update_analysis_summary_with_power_limitations(temp_summary_file, limited_report)

    # Read the updated file
    with open(temp_summary_file, 'r') as f:
        content = f.read()

    assert "Statistical Power Analysis" in content
    assert "Power limitation detected" in content


def test_update_analysis_summary_without_limitations(temp_summary_file, sample_extracted_data):
    """Test updating analysis summary without power limitations."""
    report = generate_power_analysis_report(sample_extracted_data)

    # Create a sample report without power limitation
    sufficient_report = report.copy()
    sufficient_report['power_limitation'] = False
    sufficient_report['warning_message'] = None

    update_analysis_summary_with_power_limitations(temp_summary_file, sufficient_report)

    # Read the updated file
    with open(temp_summary_file, 'r') as f:
        content = f.read()

    assert "Statistical Power Analysis" in content
    assert "Sufficient Power" in content


def test_update_analysis_summary_missing_file():
    """Test updating a missing summary file."""
    with pytest.warns(UserWarning):
        update_analysis_summary_with_power_limitations("/nonexistent/summary.md", {})
