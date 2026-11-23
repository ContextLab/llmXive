import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
from shapely.geometry import Point

# Import functions to test
from code.validation import (
    generate_spatial_blocks,
    spatial_kfold_split,
    run_spatial_block_permutation_test
)

@pytest.fixture
def sample_spatial_data():
    """Create sample spatial data for testing."""
    n_cells = 100
    np.random.seed(42)
    
    # Create a grid of points
    x_coords = np.linspace(0, 10, 10)
    y_coords = np.linspace(0, 10, 10)
    grid_x, grid_y = np.meshgrid(x_coords, y_coords)
    
    data = {
        'grid_id': [f'cell_{i}' for i in range(n_cells)],
        'geometry': [Point(x, y) for x, y in zip(grid_x.flatten(), grid_y.flatten())],
        'noise_level': np.random.normal(50, 10, n_cells),
        'traffic_volume': np.random.normal(1000, 200, n_cells),
        'population_density': np.random.normal(500, 100, n_cells),
        'land_use_residential': np.random.binomial(1, 0.5, n_cells),
        'land_use_commercial': np.random.binomial(1, 0.3, n_cells)
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def dummy_model_fn():
    """Dummy model function for testing."""
    def model_fn(X_train, y_train, X_test):
        # Simple mean prediction
        return np.full(X_test.shape[0], np.mean(y_train))
    return model_fn

def test_generate_spatial_blocks(sample_spatial_data):
    """Test that spatial blocks are generated correctly and are disjoint."""
    blocks = generate_spatial_blocks(sample_spatial_data, n_blocks=5)
    
    # Check that we have 5 blocks
    assert len(blocks) == 5
    
    # Check that all grid_ids are assigned to exactly one block
    all_ids = []
    for block_ids in blocks.values():
        all_ids.extend(block_ids)
        
    assert len(all_ids) == len(sample_spatial_data)
    assert len(set(all_ids)) == len(all_ids)  # No duplicates
    
    # Check that blocks are non-empty
    for block_ids in blocks.values():
        assert len(block_ids) > 0

def test_spatial_kfold_split(sample_spatial_data):
    """Test that k-fold splits are spatially disjoint."""
    blocks = generate_spatial_blocks(sample_spatial_data, n_blocks=5)
    splits = spatial_kfold_split(blocks, n_folds=5)
    
    # Check that we have 5 splits
    assert len(splits) == 5
    
    # Check that train and test sets are disjoint in each split
    for train_ids, test_ids in splits:
        assert len(set(train_ids) & set(test_ids)) == 0
        
        # Check that all IDs are covered
        all_ids = set(train_ids) | set(test_ids)
        assert len(all_ids) == len(sample_spatial_data)

def test_run_spatial_block_permutation_test(sample_spatial_data, dummy_model_fn):
    """Test the full permutation test logic."""
    # Run with a small number of permutations for speed
    result = run_spatial_block_permutation_test(
        data=sample_spatial_data,
        model_fn=dummy_model_fn,
        n_permutations=10,  # Small number for testing
        n_folds=5,
        target_col='noise_level',
        feature_cols=['traffic_volume', 'population_density'],
        random_state=42
    )
    
    # Check that all expected keys are present
    expected_keys = [
        'observed_rmse', 'permuted_rmse_mean', 'permuted_rmse_std',
        'p_value_one_tailed', 'p_value_two_tailed', 'n_permutations',
        'significant_at_0.05'
    ]
    
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
        
    # Check that values are reasonable
    assert result['observed_rmse'] > 0
    assert result['permuted_rmse_mean'] > 0
    assert 0 <= result['p_value_one_tailed'] <= 1
    assert 0 <= result['p_value_two_tailed'] <= 1
    assert result['n_permutations'] == 10
    assert isinstance(result['significant_at_0.05'], bool)

def test_permutation_test_output_file(sample_spatial_data, dummy_model_fn, tmp_path):
    """Test that permutation test writes results to file."""
    # Change to temp directory to avoid writing to project root
    original_cwd = Path.cwd()
    import os
    os.chdir(tmp_path)
    
    try:
        # Create a mock get_project_root function
        import code.validation as validation_module
        original_get_project_root = validation_module.get_project_root
        
        def mock_get_project_root():
            return tmp_path
            
        validation_module.get_project_root = mock_get_project_root
        
        # Create required directory structure
        (tmp_path / "data" / "processed").mkdir(parents=True)
        
        # Save sample data
        data_path = tmp_path / "data" / "processed" / "harmonized.parquet"
        sample_spatial_data.to_parquet(data_path)
        
        # Run main
        validation_module.main()
        
        # Check that results file was created
        results_path = tmp_path / "data" / "processed" / "permutation_test_results.json"
        assert results_path.exists(), "Results file not created"
        
        # Check that results can be loaded and are valid
        with open(results_path, 'r') as f:
            results = json.load(f)
            
        assert 'observed_rmse' in results
        assert 'p_value_one_tailed' in results
        
    finally:
        os.chdir(original_cwd)
        validation_module.get_project_root = original_get_project_root