"""
Unit tests for complexity visualization module.

Tests T068: Generate visualization examples showing how complexity metric
maps to knot diagram features.
"""

import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from analysis.complexity_visualization import (
    load_cleaned_knots,
    create_complexity_heatmap,
    create_crossing_braid_scatter,
    create_complexity_distribution,
    create_braid_index_by_crossing,
    create_complexity_feature_examples,
    generate_complexity_visualization_examples,
    VisualizationSpec
)


@pytest.fixture
def sample_knot_data():
    """Create sample knot data for testing."""
    np.random.seed(42)
    n_knots = 100

    data = {
        'crossing_number': np.random.randint(3, 14, n_knots),
        'braid_index': np.random.randint(2, 8, n_knots),
        'is_alternating': np.random.choice([True, False], n_knots),
        'hyperbolic_volume': np.random.uniform(0.1, 10.0, n_knots)
    }

    # Ensure braid_index <= crossing_number
    for i in range(n_knots):
        if data['braid_index'][i] > data['crossing_number'][i]:
            data['braid_index'][i] = data['crossing_number'][i]

    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_file(sample_knot_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_knot_data.to_csv(f.name, index=False)
        yield Path(f.name)
    os.unlink(f.name)


def test_load_cleaned_knots(temp_csv_file):
    """Test loading cleaned knot data from CSV."""
    df = load_cleaned_knots(temp_csv_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'crossing_number' in df.columns
    assert 'braid_index' in df.columns


def test_create_complexity_heatmap(sample_knot_data):
    """Test creating complexity correlation heatmap."""
    fig, ax = plt.subplots()
    create_complexity_heatmap(sample_knot_data, ax)

    # Verify heatmap was created
    assert len(ax.collections) > 0  # Heatmap has collection
    assert ax.get_title() == 'Complexity Metrics Correlation'
    plt.close(fig)


def test_create_crossing_braid_scatter(sample_knot_data):
    """Test creating crossing number vs braid index scatter plot."""
    fig, ax = plt.subplots()
    create_crossing_braid_scatter(sample_knot_data, ax)

    # Verify scatter plot was created
    assert len(ax.collections) > 0
    assert ax.get_xlabel() == 'Crossing Number'
    assert ax.get_ylabel() == 'Braid Index'
    plt.close(fig)


def test_create_complexity_distribution(sample_knot_data):
    """Test creating crossing number distribution plot."""
    fig, ax = plt.subplots()
    create_complexity_distribution(sample_knot_data, ax)

    # Verify histogram was created
    assert len(ax.patches) > 0
    assert ax.get_xlabel() == 'Crossing Number'
    plt.close(fig)


def test_create_braid_index_by_crossing(sample_knot_data):
    """Test creating braid index boxplot by crossing number."""
    fig, ax = plt.subplots()
    create_braid_index_by_crossing(sample_knot_data, ax)

    # Verify boxplot was created
    assert len(ax.patches) > 0
    assert ax.get_xlabel() == 'Crossing Number'
    plt.close(fig)


def test_create_complexity_feature_examples(sample_knot_data):
    """Test creating complexity feature examples plot."""
    fig, ax = plt.subplots()
    create_complexity_feature_examples(sample_knot_data, ax)

    # Verify scatter plot was created
    assert len(ax.collections) > 0
    plt.close(fig)


def test_generate_complexity_visualization_examples(sample_knot_data):
    """Test generating full complexity visualization examples."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_complexity_viz.png"

        result_path = generate_complexity_visualization_examples(
            sample_knot_data,
            output_path,
            figsize=(12, 8)
        )

        # Verify file was created
        assert result_path.exists()
        assert result_path.suffix == '.png'
        assert result_path.stat().st_size > 0  # File has content


def test_generate_complexity_visualization_examples_empty_data():
    """Test handling of empty data."""
    empty_df = pd.DataFrame(columns=['crossing_number', 'braid_index'])

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_empty_viz.png"

        # Should not raise exception
        result_path = generate_complexity_visualization_examples(
            empty_df,
            output_path,
            figsize=(12, 8)
        )

        assert result_path.exists()


def test_visualization_spec():
    """Test VisualizationSpec dataclass."""
    spec = VisualizationSpec(
        title="Test Plot",
        description="Test description",
        x_metric="crossing_number",
        y_metric="braid_index",
        hue_metric="is_alternating",
        plot_type="scatter",
        sample_size=100
    )

    assert spec.title == "Test Plot"
    assert spec.x_metric == "crossing_number"
    assert spec.sample_size == 100
