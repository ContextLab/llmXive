"""
Unit tests for T028: visualize_pathways.py
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Import the function to test
# We need to ensure the path is set up correctly if running standalone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.visualize_pathways import aggregate_pathway_scores, load_json_file

@pytest.fixture
def sample_pathway_data():
    """Sample data mimicking the output of T027."""
    return [
        {"metabolite": "M1", "importance": 0.5, "pathways": ["Pathway A", "Pathway B"]},
        {"metabolite": "M2", "importance": 0.3, "pathways": ["Pathway A"]},
        {"metabolite": "M3", "importance": 0.2, "pathways": ["Pathway C"]},
        {"metabolite": "M4", "importance": 0.4, "pathways": ["Pathway B", "Pathway C"]},
    ]

@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary directory for test artifacts."""
    return tmp_path

def test_aggregate_pathway_scores(sample_pathway_data):
    """Test that pathway aggregation sums importance correctly."""
    df = aggregate_pathway_scores(sample_pathway_data, top_n=10)
    
    assert len(df) > 0
    assert "Pathway" in df.columns
    assert "Total Importance" in df.columns
    
    # Pathway A: 0.5 + 0.3 = 0.8
    # Pathway B: 0.5 + 0.4 = 0.9
    # Pathway C: 0.2 + 0.4 = 0.6
    
    row_a = df[df['Pathway'] == 'Pathway A']
    assert not row_a.empty
    assert abs(row_a['Total Importance'].values[0] - 0.8) < 0.001
    
    row_b = df[df['Pathway'] == 'Pathway B']
    assert not row_b.empty
    assert abs(row_b['Total Importance'].values[0] - 0.9) < 0.001

def test_aggregate_pathway_scores_top_n(sample_pathway_data):
    """Test that top_n limits the output."""
    df = aggregate_pathway_scores(sample_pathway_data, top_n=2)
    assert len(df) == 2
    # Should be Pathway B (0.9) and Pathway A (0.8)
    assert df.iloc[0]['Pathway'] == 'Pathway B'
    assert df.iloc[1]['Pathway'] == 'Pathway A'

def test_load_json_file(temp_results_dir):
    """Test JSON loading."""
    test_file = temp_results_dir / "test.json"
    test_data = {"key": "value"}
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_json_file(test_file)
    assert loaded == test_data

def test_aggregate_empty_data():
    """Test behavior with empty data."""
    df = aggregate_pathway_scores([], top_n=10)
    assert df.empty

def test_plot_generation(temp_results_dir, sample_pathway_data):
    """Test that the plot generation function creates a file."""
    # This test mocks the plotting to avoid needing a display in CI
    # but verifies the logic path.
    from code.modeling.visualize_pathways import plot_pathway_importance
    import matplotlib
    matplotlib.use('Agg') # Use non-interactive backend
    
    df = aggregate_pathway_scores(sample_pathway_data, top_n=10)
    output_path = temp_results_dir / "test_plot.png"
    
    plot_pathway_importance(df, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
