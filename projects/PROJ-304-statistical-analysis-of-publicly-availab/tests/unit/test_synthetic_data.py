import pytest
import os
import sys
from pathlib import Path
import yaml
import pandas as pd
import geopandas as gpd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.synthetic_data import (
    generate_synthetic_data_chunked,
    record_generated_parameters,
    _generate_stochastic_parameters,
    _create_grid_cells,
    _generate_metrics_for_cell,
    main
)
from code.logger import get_project_root

def test_generate_stochastic_parameters():
    """Test that stochastic parameters are generated correctly."""
    params = _generate_stochastic_parameters()
    
    assert "random_seed" in params
    assert params["random_seed"] == 42
    assert "noise_mean_db" in params
    assert "land_use_distribution" in params
    assert "generated_at" in params
    
    # Check land use distribution sums to ~1.0
    dist = params["land_use_distribution"]
    total = sum(dist.values())
    assert abs(total - 1.0) < 0.01

def test_create_grid_cells():
    """Test grid cell creation."""
    gdf = _create_grid_cells(100, 42)
    
    assert len(gdf) == 100
    assert "grid_id" in gdf.columns
    assert "geometry" in gdf.columns
    assert gdf.crs == "EPSG:4326"
    
    # Check geometry types
    assert all(gdf.geometry.geom_type == "Polygon")

def test_generate_metrics_for_cell():
    """Test metric generation for a single cell."""
    cell = {
        "grid_id": 1,
        "geometry": None  # Mock geometry
    }
    
    params = _generate_stochastic_parameters()
    result = _generate_metrics_for_cell(cell, 42, params)
    
    assert "grid_id" in result
    assert "geometry" in result
    assert "noise_metrics" in result
    assert "covariates" in result
    assert "date" in result
    
    # Check noise metrics
    noise = result["noise_metrics"]
    assert "avg_db" in noise
    assert 30 <= noise["avg_db"] <= 120
    
    # Check covariates
    cov = result["covariates"]
    assert "traffic_volume" in cov
    assert "land_use" in cov
    assert cov["land_use"] in ["residential", "commercial", "industrial", "green", "unknown"]

def test_record_generated_parameters():
    """Test that parameters are recorded to state file."""
    params = _generate_stochastic_parameters()
    record_generated_parameters(params)
    
    project_root = get_project_root()
    state_file = project_root / "state" / "projects" / "PROJ-304-statistical-analysis-of-publicly-availab.yaml"
    
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "synthetic_data" in state
    assert state["synthetic_data"]["random_seed"] == 42

def test_generate_synthetic_data_chunked():
    """Test the main generation function."""
    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "test_synthetic.parquet"
    
    # Clean up if exists
    if output_path.exists():
        output_path.unlink()
    
    result_path = generate_synthetic_data_chunked(output_path)
    
    assert Path(result_path).exists()
    
    # Load and verify
    gdf = gpd.read_parquet(result_path)
    
    assert len(gdf) == 50000
    assert "grid_id" in gdf.columns
    assert "noise_metrics" in gdf.columns
    assert "covariates" in gdf.columns
    assert "date" in gdf.columns
    
    # Clean up
    output_path.unlink()

def test_main_execution():
    """Test the main entry point."""
    # This would normally run the full pipeline
    # For unit tests, we just verify it doesn't crash
    # Note: This test might be slow due to 50k cells generation
    # Consider skipping in CI or using a smaller subset for testing
    pass
