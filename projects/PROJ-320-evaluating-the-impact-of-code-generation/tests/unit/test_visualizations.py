"""
Unit tests for the visualization module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.visualizations import (
    load_metrics_for_viz,
    generate_boxplots,
    generate_histograms,
    generate_correlation_plot,
    run_visualization_pipeline
)
from code.utils.logging import setup_logging

@pytest.fixture
def sample_data():
    """Create sample metrics data for testing."""
    return [
        {'source_type': 'llm', 'comment_count': 5.0, 'time_to_merge_minutes': 120.0, 'review_cycles': 2.0, 'complexity_score': 1.5},
        {'source_type': 'llm', 'comment_count': 8.0, 'time_to_merge_minutes': 150.0, 'review_cycles': 3.0, 'complexity_score': 2.0},
        {'source_type': 'human', 'comment_count': 12.0, 'time_to_merge_minutes': 200.0, 'review_cycles': 4.0, 'complexity_score': 3.5},
        {'source_type': 'human', 'comment_count': 15.0, 'time_to_merge_minutes': 250.0, 'review_cycles': 5.0, 'complexity_score': 4.0},
    ]

@pytest.fixture
def temp_metrics_file(sample_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("source_type,comment_count,time_to_merge_minutes,review_cycles,complexity_score\n")
        for row in sample_data:
            f.write(f"{row['source_type']},{row['comment_count']},{row['time_to_merge_minutes']},{row['review_cycles']},{row['complexity_score']}\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_metrics_for_viz(temp_metrics_file, sample_data):
    """Test that metrics are loaded correctly from CSV."""
    result = load_metrics_for_viz(Path(temp_metrics_file))
    assert len(result) == len(sample_data)
    assert result[0]['source_type'] == 'llm'
    assert result[0]['comment_count'] == 5.0

def test_generate_boxplots_creates_file(temp_metrics_file, sample_data):
    """Test that boxplot generation creates a valid PDF file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_boxplots.pdf'
        generate_boxplots(sample_data, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

def test_generate_histograms_creates_file(temp_metrics_file, sample_data):
    """Test that histogram generation creates a valid PDF file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_histograms.pdf'
        generate_histograms(sample_data, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

def test_generate_correlation_plot_creates_file(temp_metrics_file, sample_data):
    """Test that correlation plot generation creates a valid PDF file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_correlation.pdf'
        generate_correlation_plot(sample_data, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

def test_run_visualization_pipeline_fails_without_metrics():
    """Test that pipeline fails gracefully when metrics file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake metrics path that doesn't exist
        fake_metrics = Path(tmpdir) / 'nonexistent.csv'
        # Mock the load function to raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            run_visualization_pipeline()