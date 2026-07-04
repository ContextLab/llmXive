"""
Integration test for the full spatial modeling pipeline (User Story 3).

This test verifies the end-to-end execution of the modeling pipeline:
1. Loading aligned raster data (simulated via synthetic but real-structured data).
2. Generating spatial blocks and folds.
3. Running spatial cross-validation.
4. Validating that metrics are computed and leakage is prevented.
5. Ensuring outputs are written to disk.

Note: Since real raster data ingestion (T012-T016) is a prerequisite,
this test generates a minimal synthetic dataset that strictly adheres
to the expected schema (numpy arrays + geospatial metadata) to verify
the logic of `modeling.py` without requiring external file downloads
during the test run.
"""
import os
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from pathlib import Path

# Import project modules
import sys
# Ensure code/ is in path if running from root
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from modeling import (
    SpatialCrossValidator,
    generate_spatial_folds,
    validate_spatial_leakage,
    run_spatial_cross_validation,
    main as modeling_main
)
from config import MAX_BLOCKS, get_path
from utils.memory import generate_spatial_blocks

# Constants for test data
TEST_GRID_SIZE = 100
N_FEATURES = 5
N_FOLDS = 3
RANDOM_SEED = 42

def _create_synthetic_raster_data(output_dir: Path):
    """
    Creates a minimal synthetic raster stack and metadata to simulate
    the output of the ingestion pipeline (T012-T016).
    """
    # Create a synthetic GeoDataFrame representing the spatial blocks
    # We create a grid of 10x10 blocks to simulate the spatial structure
    n_blocks = 100
    xs = np.linspace(0, 10, 11)
    ys = np.linspace(0, 10, 11)
    geometries = []
    for i in range(10):
        for j in range(10):
            geom = box(xs[i], ys[j], xs[i+1], ys[j+1])
            geometries.append(geom)

    gdf = gpd.GeoDataFrame(
        {'block_id': range(n_blocks), 'geometry': geometries},
        crs="EPSG:3857"
    )

    # Create synthetic raster data (numpy arrays)
    # Shape: (n_blocks, height, width) -> flattened to (n_samples, n_features)
    np.random.seed(RANDOM_SEED)
    # Simulate 1000 points sampled across the 100 blocks
    n_samples = 1000
    X = np.random.rand(n_samples, N_FEATURES)
    y = np.random.rand(n_samples) * 10 + 0.1 * X[:, 0] # Temperature ~ feature 0 + noise

    # Save synthetic data to disk to mimic pipeline output
    data_dir = output_dir / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save features and target as CSV (simulating raster extraction)
    pd.DataFrame(X, columns=[f'covariate_{i}' for i in range(N_FEATURES)]).to_csv(
        data_dir / "synthetic_covariates.csv", index=False
    )
    pd.DataFrame({'temperature': y}).to_csv(
        data_dir / "synthetic_temperature.csv", index=False
    )
    gdf.to_file(data_dir / "synthetic_blocks.geojson", driver='GeoJSON')

    # Create a dummy metadata file
    metadata = {
        "crs": "EPSG:3857",
        "resolution_m": 30,
        "source": "synthetic_for_integration_test",
        "timestamp": "2023-10-27T10:00:00"
    }
    with open(data_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    return data_dir

def test_spatial_cross_validation_pipeline():
    """
    Integration test: Run the full spatial cross-validation logic.
    """
    # Setup temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # 1. Prepare synthetic data
        data_path = _create_synthetic_raster_data(tmp_path)
        
        # 2. Load data into memory (mimicking modeling.py main logic)
        covariates_df = pd.read_csv(data_path / "synthetic_covariates.csv")
        target_df = pd.read_csv(data_path / "synthetic_temperature.csv")
        blocks_gdf = gpd.read_file(data_path / "synthetic_blocks.geojson")
        
        # Merge data
        # Assign random block IDs to samples for this test to simulate spatial structure
        # In a real run, these would be assigned based on raster coordinates
        np.random.seed(RANDOM_SEED)
        sample_block_ids = np.random.choice(blocks_gdf['block_id'].values, size=len(covariates_df))
        
        df = covariates_df.copy()
        df['temperature'] = target_df['temperature']
        df['block_id'] = sample_block_ids
        
        # 3. Test SpatialCrossValidator
        validator = SpatialCrossValidator(
            n_splits=N_FOLDS,
            block_column='block_id',
            random_state=RANDOM_SEED
        )
        
        # Run validation
        results = run_spatial_cross_validation(
            df=df,
            target_col='temperature',
            feature_cols=[f'covariate_{i}' for i in range(N_FEATURES)],
            validator=validator
        )
        
        # 4. Assertions
        assert results is not None, "Cross-validation results should not be None"
        assert 'metrics' in results, "Results must contain 'metrics' key"
        assert 'folds' in results, "Results must contain 'folds' key"
        
        metrics = results['metrics']
        assert 'rmse' in metrics, "Metrics must include RMSE"
        assert 'r2' in metrics, "Metrics must include R2"
        assert 'mae' in metrics, "Metrics must include MAE"
        
        # Verify metrics are numeric
        assert isinstance(metrics['rmse'], (int, float)), "RMSE must be numeric"
        assert isinstance(metrics['r2'], (int, float)), "R2 must be numeric"
        
        # 5. Verify no spatial leakage (conceptual check on the folds)
        # The validator should ensure no block appears in both train and test
        # We check the generator logic directly
        folds = list(validator.split(df))
        assert len(folds) == N_FOLDS, f"Expected {N_FOLDS} folds, got {len(folds)}"
        
        for train_idx, test_idx in folds:
            train_blocks = set(df.iloc[train_idx]['block_id'].unique())
            test_blocks = set(df.iloc[test_idx]['block_id'].unique())
            overlap = train_blocks.intersection(test_blocks)
            assert len(overlap) == 0, f"Spatial leakage detected: blocks {overlap} in both train and test"

def test_leakage_validation_function():
    """
    Test the explicit leakage validation utility.
    """
    # Create a mock dataset with intentional leakage
    df = pd.DataFrame({
        'block_id': [1, 1, 2, 2, 3, 3],
        'value': [10, 11, 20, 21, 30, 31]
    })
    
    train_idx = [0, 2, 4]
    test_idx = [1, 3, 5] # Blocks 1, 2, 3 appear in both
    
    is_safe, leaked_blocks = validate_spatial_leakage(
        df, train_idx, test_idx, block_column='block_id'
    )
    
    assert is_safe is False, "Should detect leakage"
    assert len(leaked_blocks) > 0, "Should identify leaked blocks"

def test_main_entry_point():
    """
    Test the main entry point of modeling.py to ensure it runs without crashing
    and writes output files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Prepare data
        data_path = _create_synthetic_raster_data(tmp_path)
        
        # Mock command line arguments
        original_argv = sys.argv
        try:
            sys.argv = [
                'modeling.py',
                '--data-dir', str(data_path),
                '--output-dir', str(tmp_path / "results"),
                '--n-folds', str(N_FOLDS),
                '--seed', str(RANDOM_SEED)
            ]
            
            # Run main
            modeling_main()
            
            # Check outputs
            results_dir = tmp_path / "results"
            assert results_dir.exists(), "Results directory should be created"
            
            # Check for expected output files
            metrics_file = results_dir / "metrics.json"
            assert metrics_file.exists(), "metrics.json should be created"
            
            with open(metrics_file, 'r') as f:
                content = json.load(f)
                assert 'rmse' in content, "Metrics JSON must contain RMSE"
                
        finally:
            sys.argv = original_argv

if __name__ == "__main__":
    test_spatial_cross_validation_pipeline()
    test_leakage_validation_function()
    test_main_entry_point()
    print("All integration tests passed.")