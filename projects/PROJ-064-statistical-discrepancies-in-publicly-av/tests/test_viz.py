import os
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np
import pandas as pd

from viz import generate_histograms, generate_qq_plot, generate_heatmap, run_viz_pipeline

@pytest.fixture
def sample_data():
    """Generate sample data for visualization tests."""
    np.random.seed(42)
    observed = np.random.normal(loc=100, scale=20, size=500)
    null_dist = np.random.normal(loc=100, scale=20, size=5000)
    
    # Create mock jurisdiction results
    jurisdictions = [
        {
            'jurisdiction_id': f'JUR_{i}',
            'discrepancy_abs': np.random.uniform(0, 500),
            'discrepancy_pct': np.random.uniform(0, 5),
            'p_value': np.random.uniform(0, 1)
        }
        for i in range(50)
    ]
    
    return {
        'observed_discrepancies': observed.tolist(),
        'null_distributions': [null_dist.tolist()], # Nested list as per simulation output
        'jurisdiction_results': jurisdictions
    }

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_histograms(sample_data, temp_output_dir):
    """Test histogram generation."""
    files = generate_histograms(sample_data, temp_output_dir)
    
    assert len(files) >= 2, "Should generate at least 2 histogram files"
    assert any('histogram' in f for f in files)
    
    for f in files:
        assert os.path.exists(f), f"Output file should exist: {f}"
        # Check file size is non-zero
        assert os.path.getsize(f) > 0, f"Output file should not be empty: {f}"

def test_generate_qq_plot(sample_data, temp_output_dir):
    """Test Q-Q plot generation."""
    files = generate_qq_plot(sample_data, temp_output_dir)
    
    assert len(files) >= 1, "Should generate at least 1 Q-Q plot file"
    assert any('qq' in f for f in files)
    
    for f in files:
        assert os.path.exists(f), f"Output file should exist: {f}"
        assert os.path.getsize(f) > 0, f"Output file should not be empty: {f}"

def test_generate_heatmap(sample_data, temp_output_dir):
    """Test heatmap generation."""
    files = generate_heatmap(sample_data, temp_output_dir)
    
    assert len(files) >= 1, "Should generate at least 1 heatmap/bar chart file"
    
    for f in files:
        assert os.path.exists(f), f"Output file should exist: {f}"
        assert os.path.getsize(f) > 0, f"Output file should not be empty: {f}"

def test_run_viz_pipeline(sample_data, temp_output_dir, tmp_path):
    """Test the full pipeline with a JSON input file."""
    # Create a temporary input file
    input_file = tmp_path / 'analysis_results.json'
    with open(input_file, 'w') as f:
        json.dump(sample_data, f)
    
    results = run_viz_pipeline(str(input_file), str(temp_output_dir))
    
    assert 'histograms' in results
    assert 'qq_plots' in results
    assert 'heatmaps' in results
    
    total_files = sum(len(v) for v in results.values())
    assert total_files > 0, "Pipeline should generate at least one file"

def test_missing_data_handling(temp_output_dir):
    """Test behavior when data is missing."""
    empty_data = {
        'observed_discrepancies': [],
        'null_distributions': [],
        'jurisdiction_results': []
    }
    
    # Histograms should handle empty data gracefully
    files = generate_histograms(empty_data, temp_output_dir)
    assert len(files) == 0, "Should not generate files for empty data"
    
    # Q-Q plots should handle empty data gracefully
    files = generate_qq_plot(empty_data, temp_output_dir)
    assert len(files) == 0, "Should not generate files for empty data"
    
    # Heatmaps should handle empty data gracefully
    files = generate_heatmap(empty_data, temp_output_dir)
    assert len(files) == 0, "Should not generate files for empty data"
