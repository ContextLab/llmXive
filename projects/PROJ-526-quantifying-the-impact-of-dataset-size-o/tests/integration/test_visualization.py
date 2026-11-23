"""
Integration tests for the visualization module (T028).
Verifies that the visualization scripts can run end-to-end and produce valid output files.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from visualize_results import (
    load_scaling_results,
    load_learning_curve_data,
    plot_learning_curves,
    plot_scaling_exponents_heatmap,
    plot_fit_quality_distribution
)
from config import get_config

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data layout."""
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    figures_dir = data_dir / "figures"
    
    processed_dir.mkdir(parents=True)
    figures_dir.mkdir(parents=True)
    
    # Create mock scaling_results.csv
    scaling_data = {
        'property_name': ['prop_A', 'prop_B', 'prop_C', 'prop_D', 'prop_E'],
        'exponent_b': [0.32, 0.45, 0.12, 0.88, 0.55],
        'intercept_a': [1.2, 0.8, 2.1, 0.5, 1.0],
        'r_squared': [0.95, 0.88, 0.92, 0.99, 0.75],
        'fit_status': ['power-law', 'non-power-law', 'power-law', 'power-law', 'non-power-law']
    }
    scaling_df = pd.DataFrame(scaling_data)
    scaling_df.to_csv(processed_dir / "scaling_results.csv", index=False)
    
    # Create mock learning_curves.csv
    lc_data = {
        'property_name': ['prop_A', 'prop_A', 'prop_B', 'prop_B', 'prop_C'] * 5,
        'subset_size': [1000, 5000, 1000, 5000, 1000] * 5,
        'mae': [0.5, 0.3, 0.6, 0.4, 0.7] * 5,
        'rmse': [0.6, 0.4, 0.7, 0.5, 0.8] * 5,
        'seed': [42] * 25
    }
    lc_df = pd.DataFrame(lc_data)
    lc_df.to_csv(processed_dir / "learning_curves.csv", index=False)
    
    return data_dir

def test_plot_learning_curves_integration(temp_data_dir, tmp_path):
    """Test that learning curve plot generation runs without error and produces a file."""
    # Mock config to use temp directory
    original_get_config = get_config
    def mock_get_config():
        class MockConfig:
            data_dir = str(temp_data_dir)
        return MockConfig()
    
    # Patch get_config
    import visualize_results
    visualize_results.get_config = mock_get_config
    
    try:
        # Load data
        lc_df = pd.read_csv(temp_data_dir / "processed" / "learning_curves.csv")
        
        # Generate plot
        output_path = tmp_path / "test_lc.png"
        plot_learning_curves(lc_df, top_n=3, output_path=output_path)
        
        # Verify file exists and has content
        assert output_path.exists(), "Output file was not created."
        assert output_path.stat().st_size > 0, "Output file is empty."
        
        # Verify it's a valid image (basic check)
        import matplotlib.image as mpimg
        try:
            img = mpimg.imread(str(output_path))
            assert img.shape[0] > 0 and img.shape[1] > 0, "Image has invalid dimensions."
        except Exception as e:
            pytest.fail(f"Failed to read generated image: {e}")
            
    finally:
        # Restore original
        visualize_results.get_config = original_get_config

def test_plot_scaling_exponents_heatmap_integration(temp_data_dir, tmp_path):
    """Test that scaling exponents heatmap generation runs without error."""
    import visualize_results
    visualize_results.get_config = lambda: type('obj', (object,), {'data_dir': str(temp_data_dir)})()
    
    try:
        scaling_df = pd.read_csv(temp_data_dir / "processed" / "scaling_results.csv")
        
        output_path = tmp_path / "test_heatmap.png"
        plot_scaling_exponents_heatmap(scaling_df, output_path=output_path)
        
        assert output_path.exists(), "Heatmap file was not created."
        assert output_path.stat().st_size > 0, "Heatmap file is empty."
        
    finally:
        visualize_results.get_config = lambda: None

def test_plot_fit_quality_distribution_integration(temp_data_dir, tmp_path):
    """Test that fit quality distribution plot runs without error."""
    import visualize_results
    visualize_results.get_config = lambda: type('obj', (object,), {'data_dir': str(temp_data_dir)})()
    
    try:
        scaling_df = pd.read_csv(temp_data_dir / "processed" / "scaling_results.csv")
        
        output_path = tmp_path / "test_dist.png"
        plot_fit_quality_distribution(scaling_df, output_path=output_path)
        
        assert output_path.exists(), "Distribution file was not created."
        assert output_path.stat().st_size > 0, "Distribution file is empty."
        
    finally:
        visualize_results.get_config = lambda: None

def test_main_entry_point_integration(temp_data_dir, tmp_path):
    """Test the full main() entry point with mock data."""
    import visualize_results
    visualize_results.get_config = lambda: type('obj', (object,), {'data_dir': str(temp_data_dir)})()
    
    try:
        # Run main
        visualize_results.main()
        
        # Check that all expected files were created in the temp figures dir
        figures_dir = temp_data_dir / "figures"
        expected_files = [
            "learning_curves_comparison.png",
            "scaling_exponents_heatmap.png",
            "fit_quality_distribution.png"
        ]
        
        for fname in expected_files:
            fpath = figures_dir / fname
            assert fpath.exists(), f"Expected file {fname} was not created."
            assert fpath.stat().st_size > 0, f"File {fname} is empty."
            
    except Exception as e:
        pytest.fail(f"Main entry point failed: {e}")
    finally:
        visualize_results.get_config = lambda: None