"""Integration test for T031: Brain surface plot generation.

Tests the visualization pipeline end-to-end, including:
- Loading model coefficients
- Extracting top connections
- Generating brain plot
- Handling edge cases (< 50 edges)
"""
import os
import json
import tempfile
import numpy as np
from pathlib import Path

import pytest
from nilearn import plotting

# Add project root to path
sys_path = str(Path(__file__).parent.parent.parent)
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from modeling.visualize import (
    load_model_coefficients,
    extract_top_connections,
    load_schaefer_coords,
    generate_brain_plot,
    run_visualization_pipeline
)


@pytest.fixture
def temp_model_coeffs():
    """Create temporary model coefficients file."""
    with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
        # Create synthetic coefficients (400 ROIs -> 79800 edges)
        n_rois = 400
        n_features = n_rois * (n_rois - 1) // 2
        coeffs = np.random.randn(n_features) * 0.1
        # Make some coefficients larger to simulate predictive edges
        coeffs[:100] = np.random.randn(100) * 0.5
        np.save(f.name, coeffs)
        yield f.name
        os.unlink(f.name)


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_extract_top_connections():
    """Test extraction of top N connections."""
    n_rois = 40
    n_features = n_rois * (n_rois - 1) // 2
    coeffs = np.random.randn(n_features)
    
    # Extract top 10
    edges = extract_top_connections(coeffs, n_top=10)
    
    assert len(edges) == 10
    assert all(isinstance(e, tuple) and len(e) == 3 for e in edges)
    assert all(isinstance(e[0], int) and isinstance(e[1], int) for e in edges)
    
    # Verify they are sorted by absolute magnitude
    magnitudes = [abs(e[2]) for e in edges]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_extract_top_connections_few_edges():
    """Test handling of fewer than 50 edges."""
    # Create coefficients with only 20 non-zero edges
    n_rois = 20
    n_features = n_rois * (n_rois - 1) // 2
    coeffs = np.zeros(n_features)
    coeffs[:20] = np.random.randn(20) * 0.5
    
    edges = extract_top_connections(coeffs, n_top=50)
    
    # Should return all available (20)
    assert len(edges) == 20


def test_generate_brain_plot(temp_model_coeffs, temp_output_dir):
    """Test brain plot generation."""
    # Load coefficients
    coeffs = np.load(temp_model_coeffs)
    
    # Extract top edges
    edges = extract_top_connections(coeffs, n_top=50)
    
    # Load coordinates
    coords = load_schaefer_coords()
    
    # Generate plot
    output_path = os.path.join(temp_output_dir, "test_plot.png")
    saved_path = generate_brain_plot(
        coords,
        edges,
        output_path,
        title="Test Plot"
    )
    
    # Verify file exists
    assert os.path.exists(saved_path)
    assert os.path.getsize(saved_path) > 0


def test_run_visualization_pipeline(temp_model_coeffs, temp_output_dir):
    """Test full visualization pipeline."""
    result = run_visualization_pipeline(
        model_path=temp_model_coeffs,
        feature_path="dummy_path",  # Not used in this simplified test
        output_dir=temp_output_dir,
        n_top=50
    )
    
    # Verify result structure
    assert "plot_path" in result
    assert "n_edges_plotted" in result
    assert os.path.exists(result["plot_path"])
    assert result["n_edges_plotted"] <= 50  # May be less if fewer non-zero coeffs


def test_pipeline_handles_few_edges(temp_output_dir):
    """Test pipeline when fewer than 50 edges available."""
    # Create model with very few non-zero coefficients
    with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
        n_rois = 10
        n_features = n_rois * (n_rois - 1) // 2
        coeffs = np.zeros(n_features)
        coeffs[:10] = np.random.randn(10) * 0.5  # Only 10 non-zero
        np.save(f.name, coeffs)
        
        try:
            result = run_visualization_pipeline(
                model_path=f.name,
                feature_path="dummy_path",
                output_dir=temp_output_dir,
                n_top=50
            )
            
            # Should complete successfully with fewer edges
            assert "warning" in result
            assert "Only 10 edges plotted" in result["warning"]
            assert os.path.exists(result["plot_path"])
        finally:
            os.unlink(f.name)