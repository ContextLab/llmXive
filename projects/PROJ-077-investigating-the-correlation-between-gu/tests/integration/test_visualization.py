"""
Integration tests for visualization module.
Tests T031: Visualization PNG generation.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports if running from test directory
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.visualization import generate_scatter_plot, generate_histogram_plot
from code.config import ensure_directories


@pytest.fixture
def mock_plot_data_path():
    """Create a temporary directory and mock data file for visualization testing."""
    # Create a temporary directory for this test
    temp_dir = tempfile.mkdtemp(prefix="viz_test_")
    fixture_path = Path(temp_dir) / "mock_plot_data.csv"
    
    # Generate mock data using np.random
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'participant_id': range(n_samples),
        'shannon_index': np.random.normal(loc=3.5, scale=0.5, size=n_samples),
        'fluid_intelligence': np.random.normal(loc=100, scale=15, size=n_samples),
        'age': np.random.randint(25, 75, size=n_samples),
        'bmi': np.random.normal(loc=25, scale=4, size=n_samples),
        'sex': np.random.choice(['M', 'F'], size=n_samples),
        'dqs': np.random.normal(loc=50, scale=10, size=n_samples)
    }
    
    df = pd.DataFrame(data)
    df.to_csv(fixture_path, index=False)
    
    yield fixture_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def output_dir():
    """Create a temporary output directory for generated plots."""
    temp_dir = tempfile.mkdtemp(prefix="viz_output_")
    yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_visualization_png_generation(mock_plot_data_path, output_dir):
    """
    Test T031: Verify that visualization functions generate valid PNG files.
    
    Requirements:
    - Generate mock data using np.random (already done in fixture)
    - Save to tests/fixtures/mock_plot_data.csv (done in fixture)
    - Expect output file scatter_shannon_fi.png exists and is > 1KB
    """
    # Ensure output directory exists
    ensure_directories()
    
    # Define output paths
    scatter_output = output_dir / "scatter_shannon_fi.png"
    histogram_output = output_dir / "diversity_histogram.png"
    
    # Load the mock data
    df = pd.read_csv(mock_plot_data_path)
    
    # Test scatter plot generation
    generate_scatter_plot(
        df,
        x_col='shannon_index',
        y_col='fluid_intelligence',
        output_path=str(scatter_output),
        xlabel='Shannon Index',
        ylabel='Fluid Intelligence',
        title='Gut Microbiome Diversity vs. Cognitive Performance'
    )
    
    # Test histogram plot generation
    generate_histogram_plot(
        df,
        col='shannon_index',
        output_path=str(histogram_output),
        xlabel='Shannon Index',
        title='Distribution of Alpha Diversity'
    )
    
    # Assertions
    assert scatter_output.exists(), f"Scatter plot file not created: {scatter_output}"
    assert histogram_output.exists(), f"Histogram plot file not created: {histogram_output}"
    
    # Check file sizes are > 1KB (1024 bytes)
    scatter_size = scatter_output.stat().st_size
    histogram_size = histogram_output.stat().st_size
    
    assert scatter_size > 1024, f"Scatter plot file too small: {scatter_size} bytes"
    assert histogram_size > 1024, f"Histogram plot file too small: {histogram_size} bytes"
    
    # Verify file format (should be PNG)
    assert scatter_output.suffix == '.png', f"Scatter plot is not PNG: {scatter_output}"
    assert histogram_output.suffix == '.png', f"Histogram plot is not PNG: {histogram_output}"
    
    # Optional: Verify PNG header magic bytes
    with open(scatter_output, 'rb') as f:
        header = f.read(8)
        assert header[:4] == b'\x89PNG', f"Scatter plot is not a valid PNG file"
    
    with open(histogram_output, 'rb') as f:
        header = f.read(8)
        assert header[:4] == b'\x89PNG', f"Histogram plot is not a valid PNG file"
    
    print(f"✓ Scatter plot generated: {scatter_output} ({scatter_size} bytes)")
    print(f"✓ Histogram plot generated: {histogram_output} ({histogram_size} bytes)")
