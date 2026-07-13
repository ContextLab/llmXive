"""
Tests for the visualization module.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from visualization import (
    load_metric_data,
    create_boxplot,
    generate_all_boxplots,
    run_visualization_pipeline,
    METRIC_COLUMNS
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with test data."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / 'metrics'
    data_dir.mkdir()

    # Create test CSV files for each metric
    groups = ['human'] * 50 + ['llm'] * 50
    np.random.seed(42)

    for metric in METRIC_COLUMNS[:3]:  # Test with first 3 metrics
        values = np.concatenate([
            np.random.normal(10, 2, 50),
            np.random.normal(12, 2.5, 50)
        ])
        df = pd.DataFrame({
            'group': groups,
            metric: values
        })
        csv_path = data_dir / f"{metric}_aggregated.csv"
        df.to_csv(csv_path, index=False)

    yield data_dir

    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_load_metric_data(temp_data_dir):
    """Test loading metric data from CSV."""
    df = load_metric_data('cyclomatic_complexity', temp_data_dir)
    assert df is not None
    assert len(df) == 100
    assert 'group' in df.columns
    assert 'cyclomatic_complexity' in df.columns

def test_load_metric_data_missing_file(temp_data_dir):
    """Test loading non-existent metric file."""
    df = load_metric_data('nonexistent_metric', temp_data_dir)
    assert df is None

def test_create_boxplot(temp_data_dir, temp_output_dir):
    """Test creating a single boxplot."""
    df = load_metric_data('cyclomatic_complexity', temp_data_dir)
    output_path = temp_output_dir / 'test_boxplot.png'

    result = create_boxplot(
        df=df,
        metric_type='cyclomatic_complexity',
        output_path=output_path
    )

    assert result is True
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_create_boxplot_invalid_data(temp_output_dir):
    """Test boxplot creation with invalid data."""
    df = pd.DataFrame({'group': ['human'], 'metric': [1.0]})
    output_path = temp_output_dir / 'test.png'

    # Missing required columns
    result = create_boxplot(
        df=df,
        metric_type='cyclomatic_complexity',
        output_path=output_path
    )
    assert result is False

def test_generate_all_boxplots(temp_data_dir, temp_output_dir):
    """Test generating all boxplots."""
    generated = generate_all_boxplots(temp_data_dir, temp_output_dir)

    assert len(generated) > 0
    for metric, path in generated.items():
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0

def test_run_visualization_pipeline(temp_data_dir, temp_output_dir):
    """Test the full visualization pipeline."""
    generated = run_visualization_pipeline(
        data_dir=temp_data_dir,
        output_dir=temp_output_dir
    )

    assert len(generated) > 0
    assert all(Path(p).exists() for p in generated.values())

def test_boxplot_labels_and_structure(temp_data_dir, temp_output_dir):
    """Test that boxplots have correct labels and structure."""
    df = load_metric_data('cyclomatic_complexity', temp_data_dir)
    output_path = temp_output_dir / 'test_labels.png'

    create_boxplot(
        df=df,
        metric_type='cyclomatic_complexity',
        output_path=output_path,
        title="Test Title",
        xlabel="Custom X",
        ylabel="Custom Y"
    )

    assert output_path.exists()
    # File should be non-empty
    assert output_path.stat().st_size > 0