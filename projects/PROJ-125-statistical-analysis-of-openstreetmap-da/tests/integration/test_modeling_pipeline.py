"""
Integration test for the full modeling pipeline (User Story 3).

This test verifies the end-to-end execution of the spatial regression modeling
pipeline, including:
1. Spatial block sampling (memory safety)
2. OLS baseline model fitting
3. SAR model fitting (with degradation logic)
4. Spatial cross-validation
5. Metrics output generation

Prerequisites:
- US1 data pipeline must have generated aligned rasters in data/processed/
- US2 EDA must have generated correlation matrices in data/results/

Expected outputs:
- data/results/metrics.csv
- data/results/sensitivity_report.md (if GWR runs)
- Console logs confirming successful pipeline completion
"""
import os
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import pytest
import geopandas as gpd
from shapely.geometry import box

# Import project modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import get_project_root, MAX_BLOCKS, CITY_CRS
from code.utils.logging import get_main_logger
from code.utils.memory import generate_spatial_blocks, sample_spatial_blocks
from code.ingest import create_aligned_stack
from code.eda import calculate_correlation_matrix, calculate_morans_i
from code import modeling

# Configure logger
logger = get_main_logger("integration_test_modeling")

# Mock data generation for integration testing
# Since real data ingestion (T012-T015) might not be complete in this context,
# we generate realistic synthetic data that mimics the expected structure
# from the US1 pipeline.

def _create_mock_raster_data(output_dir: Path, city_name: str = "nyc"):
    """
    Create mock aligned raster data for integration testing.
    This simulates the output of the US1 ingestion pipeline.
    """
    logger.info(f"Creating mock raster data in {output_dir}")
    
    # Create a small grid (100x100) for fast testing
    n = 100
    x = np.linspace(0, 1000, n)
    y = np.linspace(0, 1000, n)
    X, Y = np.meshgrid(x, y)
    
    # Temperature raster (target)
    temp_data = 20 + 0.01 * X + 0.005 * Y + np.random.normal(0, 2, (n, n))
    
    # Building density covariate
    building_density = 0.0001 * X * Y + np.random.normal(0, 0.1, (n, n))
    
    # Tree cover covariate
    tree_cover = 0.5 - 0.0002 * X + np.random.normal(0, 0.1, (n, n))
    
    # Road density covariate
    road_density = 0.00015 * Y + np.random.normal(0, 0.05, (n, n))
    
    # Save as simple numpy files (simulating GeoTIFF stack)
    # In real implementation, these would be GeoTIFFs with CRS info
    data_dir = output_dir / "mock_rasters"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    np.save(data_dir / "temperature.npy", temp_data)
    np.save(data_dir / "building_density.npy", building_density)
    np.save(data_dir / "tree_cover.npy", tree_cover)
    np.save(data_dir / "road_density.npy", road_density)
    
    # Create a mock city boundary GeoJSON
    boundary = gpd.GeoDataFrame(
        geometry=[box(0, 0, 1000, 1000)],
        crs="EPSG:3857",
        data={"name": city_name}
    )
    boundary.to_file(data_dir / "boundary.geojson", driver="GeoJSON")
    
    logger.info("Mock raster data created successfully")
    return data_dir

def _create_mock_processed_data(base_dir: Path):
    """Create the directory structure expected by the modeling pipeline."""
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    results_dir = base_dir / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    return processed_dir, results_dir

@pytest.fixture(scope="module")
def mock_data_setup(tmp_path_factory):
    """Fixture to set up mock data for integration testing."""
    base_dir = tmp_path_factory.mktemp("modeling_integration")
    
    # Create mock data
    data_dir = _create_mock_raster_data(base_dir)
    processed_dir, results_dir = _create_mock_processed_data(base_dir)
    
    # Copy mock data to processed directory (simulating US1 output)
    import shutil
    for f in data_dir.glob("*"):
        shutil.copy(f, processed_dir / f.name)
    
    return {
        "base_dir": base_dir,
        "processed_dir": processed_dir,
        "results_dir": results_dir,
        "data_dir": data_dir
    }

def test_spatial_block_sampling(mock_data_setup):
    """Test spatial block generation and sampling."""
    logger.info("Testing spatial block sampling...")
    
    base_dir = mock_data_setup["base_dir"]
    processed_dir = mock_data_setup["processed_dir"]
    
    # Load mock boundary
    boundary_path = processed_dir / "boundary.geojson"
    boundary = gpd.read_file(boundary_path)
    
    # Generate spatial blocks
    blocks = generate_spatial_blocks(
        boundary, 
        cell_size=100,  # 100m blocks for testing
        crs="EPSG:3857"
    )
    
    assert len(blocks) > 0, "No spatial blocks generated"
    assert "geometry" in blocks.columns, "Blocks missing geometry column"
    
    # Sample blocks (should respect MAX_BLOCKS)
    sampled_blocks = sample_spatial_blocks(
        blocks, 
        max_blocks=MAX_BLOCKS,
        seed=42
    )
    
    assert len(sampled_blocks) <= MAX_BLOCKS, "Sampled blocks exceed MAX_BLOCKS"
    assert len(sampled_blocks) > 0, "No blocks sampled"
    
    logger.info(f"Generated {len(blocks)} blocks, sampled {len(sampled_blocks)}")
    logger.info("Spatial block sampling test PASSED")

def test_ols_model_fitting(mock_data_setup):
    """Test OLS baseline model fitting."""
    logger.info("Testing OLS model fitting...")
    
    processed_dir = mock_data_setup["processed_dir"]
    results_dir = mock_data_setup["results_dir"]
    
    # Load mock data
    temp_data = np.load(processed_dir / "temperature.npy")
    building_density = np.load(processed_dir / "building_density.npy")
    tree_cover = np.load(processed_dir / "tree_cover.npy")
    road_density = np.load(processed_dir / "road_density.npy")
    
    # Flatten to 1D arrays
    y = temp_data.flatten()
    X = np.column_stack([
        building_density.flatten(),
        tree_cover.flatten(),
        road_density.flatten()
    ])
    
    # Fit OLS model
    model_result = modeling.fit_ols_model(
        y=y,
        X=X,
        covariate_names=["building_density", "tree_cover", "road_density"]
    )
    
    assert model_result is not None, "OLS model result is None"
    assert "coefficients" in model_result, "Missing coefficients in OLS result"
    assert "r_squared" in model_result, "Missing R² in OLS result"
    assert "p_values" in model_result, "Missing p-values in OLS result"
    
    logger.info(f"OLS R²: {model_result['r_squared']:.4f}")
    logger.info("OLS model fitting test PASSED")

def test_spatial_cross_validation(mock_data_setup):
    """Test spatial cross-validation pipeline."""
    logger.info("Testing spatial cross-validation...")
    
    processed_dir = mock_data_setup["processed_dir"]
    results_dir = mock_data_setup["results_dir"]
    
    # Load mock data
    temp_data = np.load(processed_dir / "temperature.npy")
    building_density = np.load(processed_dir / "building_density.npy")
    tree_cover = np.load(processed_dir / "tree_cover.npy")
    road_density = np.load(processed_dir / "road_density.npy")
    
    y = temp_data.flatten()
    X = np.column_stack([
        building_density.flatten(),
        tree_cover.flatten(),
        road_density.flatten()
    ])
    
    # Generate spatial blocks for cross-validation
    boundary_path = processed_dir / "boundary.geojson"
    boundary = gpd.read_file(boundary_path)
    blocks = generate_spatial_blocks(boundary, cell_size=100, crs="EPSG:3857")
    
    # Perform spatial cross-validation
    cv_results = modeling.spatial_cross_validate(
        y=y,
        X=X,
        blocks=blocks,
        k_folds=3,  # Small k for testing
        seed=42
    )
    
    assert cv_results is not None, "Cross-validation results are None"
    assert "fold_scores" in cv_results, "Missing fold scores"
    assert "mean_rmse" in cv_results, "Missing mean RMSE"
    assert "mean_r_squared" in cv_results, "Missing mean R²"
    
    logger.info(f"CV Mean RMSE: {cv_results['mean_rmse']:.4f}")
    logger.info(f"CV Mean R²: {cv_results['mean_r_squared']:.4f}")
    logger.info("Spatial cross-validation test PASSED")

def test_full_pipeline_execution(mock_data_setup):
    """Test full modeling pipeline execution."""
    logger.info("Testing full modeling pipeline execution...")
    
    base_dir = mock_data_setup["base_dir"]
    processed_dir = mock_data_setup["processed_dir"]
    results_dir = mock_data_setup["results_dir"]
    
    # Create config for testing
    test_config = {
        "city_name": "nyc",
        "data_dir": str(processed_dir),
        "results_dir": str(results_dir),
        "max_blocks": 50,  # Smaller for testing
        "cv_folds": 3,
        "seed": 42,
        "run_gwr": False,  # Skip GWR for faster testing
        "run_sar": False   # Skip SAR for faster testing
    }
    
    # Execute full pipeline
    pipeline_result = modeling.run_full_pipeline(test_config)
    
    assert pipeline_result is not None, "Pipeline result is None"
    assert "models" in pipeline_result, "Missing models in pipeline result"
    assert "metrics" in pipeline_result, "Missing metrics in pipeline result"
    
    # Verify output files were created
    metrics_path = results_dir / "metrics.csv"
    assert metrics_path.exists(), "metrics.csv was not created"
    
    # Load and verify metrics
    metrics_df = pd.read_csv(metrics_path)
    assert len(metrics_df) > 0, "metrics.csv is empty"
    assert "model_type" in metrics_df.columns, "Missing model_type column"
    assert "r_squared" in metrics_df.columns, "Missing r_squared column"
    
    logger.info(f"Pipeline completed with {len(metrics_df)} model results")
    logger.info("Full pipeline execution test PASSED")

def test_sar_model_degradation_logic(mock_data_setup):
    """Test SAR model degradation when memory constraints are exceeded."""
    logger.info("Testing SAR model degradation logic...")
    
    processed_dir = mock_data_setup["processed_dir"]
    
    # Load mock data
    temp_data = np.load(processed_dir / "temperature.npy")
    building_density = np.load(processed_dir / "building_density.npy")
    tree_cover = np.load(processed_dir / "tree_cover.npy")
    road_density = np.load(processed_dir / "road_density.npy")
    
    y = temp_data.flatten()
    X = np.column_stack([
        building_density.flatten(),
        tree_cover.flatten(),
        road_density.flatten()
    ])
    
    # Test with very small dataset (should attempt SAR)
    small_y = y[:100]
    small_X = X[:100]
    
    result = modeling.fit_sar_model(
        y=small_y,
        X=small_X,
        covariate_names=["building_density", "tree_cover", "road_density"]
    )
    
    # Result should exist (either SAR or degraded OLS)
    assert result is not None, "SAR model result is None"
    assert "model_type" in result, "Missing model_type in SAR result"
    assert result["model_type"] in ["SAR", "OLS_DEGRADED"], f"Unexpected model type: {result['model_type']}"
    
    logger.info(f"SAR model type: {result['model_type']}")
    logger.info("SAR model degradation logic test PASSED")

def test_metrics_output_format(mock_data_setup):
    """Test that metrics output follows the required format."""
    logger.info("Testing metrics output format...")
    
    processed_dir = mock_data_setup["processed_dir"]
    results_dir = mock_data_setup["results_dir"]
    
    # Run a minimal pipeline
    test_config = {
        "city_name": "nyc",
        "data_dir": str(processed_dir),
        "results_dir": str(results_dir),
        "max_blocks": 20,
        "cv_folds": 2,
        "seed": 42,
        "run_gwr": False,
        "run_sar": False
    }
    
    modeling.run_full_pipeline(test_config)
    
    # Verify metrics.csv structure
    metrics_path = results_dir / "metrics.csv"
    metrics_df = pd.read_csv(metrics_path)
    
    # Check required columns (from SC-001, SC-002, SC-003, SC-005, SC-006)
    required_columns = [
        "model_type",
        "r_squared",
        "rmse",
        "mae",
        "n_samples",
        "n_features"
    ]
    
    for col in required_columns:
        assert col in metrics_df.columns, f"Missing required column: {col}"
    
    logger.info("Metrics output format test PASSED")

if __name__ == "__main__":
    # Run tests manually if executed as script
    pytest.main([__file__, "-v", "--tb=short"])
