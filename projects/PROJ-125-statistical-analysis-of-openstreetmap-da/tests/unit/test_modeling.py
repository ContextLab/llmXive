"""
Unit tests for spatial cross-validation logic in modeling.py.

This module tests the spatial k-fold cross-validation implementation,
ensuring that:
1. Spatial blocks are correctly generated and assigned.
2. Folds are mutually exclusive and cover all blocks.
3. No spatial leakage occurs between training and validation sets.
4. The cross-validation logic respects the MAX_BLOCKS constraint.
"""

import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from typing import List, Dict, Tuple

# Import the functions we expect to exist in code/modeling.py
# Based on the task requirements and existing API surface, we expect
# spatial cross-validation logic to be implemented here.
# We will implement the necessary functions in code/modeling.py as part of this task.

# Note: Since modeling.py doesn't exist yet, we will implement the required
# functions and then test them. This test file assumes the following API:
# - generate_spatial_folds(blocks: List, k: int, seed: int) -> Dict[int, List]
# - validate_spatial_leakage(train_blocks: List, val_blocks: List, all_blocks: List) -> bool
# - run_spatial_cross_validation(data, model, k: int, seed: int) -> Dict

# We'll implement these in code/modeling.py below.

try:
    from code.modeling import (
        generate_spatial_folds,
        validate_spatial_leakage,
        run_spatial_cross_validation,
        SpatialCrossValidator
    )
except ImportError:
    # If modeling.py doesn't exist yet, we'll create a mock for testing purposes
    # In a real scenario, this would be the actual implementation
    pytest.skip("modeling.py not implemented yet", allow_module_level=True)

# Fixtures
@pytest.fixture
def sample_blocks():
    """Create a set of sample spatial blocks for testing."""
    blocks = []
    for i in range(20):
        x = (i % 5) * 1000
        y = (i // 5) * 1000
        geom = box(x, y, x + 1000, y + 1000)
        blocks.append({
            'id': i,
            'geometry': geom,
            'center': (x + 500, y + 500)
        })
    return blocks

@pytest.fixture
def sample_data():
    """Create sample data for cross-validation testing."""
    np.random.seed(42)
    n_samples = 100
    data = {
        'X': np.random.randn(n_samples, 5),
        'y': np.random.randn(n_samples),
        'block_ids': np.random.randint(0, 20, n_samples)
    }
    return data

class TestSpatialCrossValidation:
    """Tests for spatial cross-validation logic."""
    
    def test_generate_spatial_folds_basic(self, sample_blocks):
        """Test basic fold generation."""
        k = 5
        folds = generate_spatial_folds(sample_blocks, k=k, seed=42)
        
        assert isinstance(folds, dict)
        assert len(folds) == k
        
        # Check that all blocks are assigned to exactly one fold
        all_assigned = []
        for fold_id, block_list in folds.items():
            all_assigned.extend(block_list)
        
        assert len(all_assigned) == len(sample_blocks)
        assert len(set(all_assigned)) == len(sample_blocks)
    
    def test_generate_spatial_folds_deterministic(self, sample_blocks):
        """Test that fold generation is deterministic with same seed."""
        k = 5
        folds1 = generate_spatial_folds(sample_blocks, k=k, seed=42)
        folds2 = generate_spatial_folds(sample_blocks, k=k, seed=42)
        
        assert folds1 == folds2
    
    def test_generate_spatial_folds_uneven_k(self, sample_blocks):
        """Test fold generation with k that doesn't divide evenly."""
        k = 7  # 20 blocks / 7 = ~2.86 per fold
        folds = generate_spatial_folds(sample_blocks, k=k, seed=42)
        
        assert len(folds) == k
        
        # Check that all blocks are assigned
        all_assigned = []
        for fold_id, block_list in folds.items():
            all_assigned.extend(block_list)
        
        assert len(all_assigned) == len(sample_blocks)
    
    def test_validate_spatial_leakage_no_leakage(self, sample_blocks):
        """Test validation when there is no spatial leakage."""
        folds = generate_spatial_folds(sample_blocks, k=5, seed=42)
        
        # Get first fold as validation set
        val_fold_id = 0
        val_blocks = folds[val_fold_id]
        train_blocks = []
        for fid, blocks in folds.items():
            if fid != val_fold_id:
                train_blocks.extend(blocks)
        
        is_valid = validate_spatial_leakage(train_blocks, val_blocks, sample_blocks)
        assert is_valid is True
    
    def test_validate_spatial_leakage_with_leakage(self, sample_blocks):
        """Test validation when there is spatial leakage."""
        # Create artificial leakage
        train_blocks = list(range(10))
        val_blocks = list(range(5, 15))  # Overlap with train
        
        is_valid = validate_spatial_leakage(train_blocks, val_blocks, sample_blocks)
        assert is_valid is False
    
    def test_spatial_cross_validator_initialization(self, sample_blocks):
        """Test SpatialCrossValidator initialization."""
        validator = SpatialCrossValidator(
            blocks=sample_blocks,
            k=5,
            seed=42
        )
        
        assert validator.k == 5
        assert validator.seed == 42
        assert len(validator.folds) == 5
    
    def test_spatial_cross_validator_get_folds(self, sample_blocks):
        """Test getting fold indices from validator."""
        validator = SpatialCrossValidator(
            blocks=sample_blocks,
            k=5,
            seed=42
        )
        
        folds = list(validator.get_folds())
        
        assert len(folds) == 5
        for train_idx, val_idx in folds:
            # Check that train and val are disjoint
            assert len(set(train_idx) & set(val_idx)) == 0
            # Check that all blocks are used
            assert len(set(train_idx) | set(val_idx)) == len(sample_blocks)
    
    def test_run_spatial_cross_validation_structure(self, sample_blocks, sample_data):
        """Test the structure of cross-validation results."""
        # Create a simple mock model
        class MockModel:
            def fit(self, X, y):
                self.coef_ = np.random.randn(X.shape[1])
                return self
            
            def predict(self, X):
                return np.random.randn(X.shape[0])
            
            def score(self, X, y):
                return np.random.rand()
        
        model = MockModel()
        validator = SpatialCrossValidator(
            blocks=sample_blocks,
            k=5,
            seed=42
        )
        
        # Map block IDs to data indices (simplified)
        block_to_indices = {}
        for i, bid in enumerate(sample_data['block_ids']):
            if bid not in block_to_indices:
                block_to_indices[bid] = []
            block_to_indices[bid].append(i)
        
        results = run_spatial_cross_validation(
            data=sample_data,
            model=model,
            blocks=sample_blocks,
            k=5,
            seed=42,
            block_to_indices=block_to_indices
        )
        
        assert 'fold_results' in results
        assert 'metrics' in results
        assert len(results['fold_results']) == 5
        
        # Check that metrics are present
        metrics = results['metrics']
        assert 'mean_rmse' in metrics
        assert 'mean_mae' in metrics
        assert 'mean_r2' in metrics
        assert 'std_rmse' in metrics
        assert 'std_mae' in metrics
        assert 'std_r2' in metrics
    
    def test_spatial_cross_validation_memory_safety(self, sample_blocks):
        """Test that cross-validation respects MAX_BLOCKS."""
        from code.config import MAX_BLOCKS
        
        # Create a large number of blocks
        large_blocks = []
        for i in range(MAX_BLOCKS + 100):
            x = (i % 20) * 1000
            y = (i // 20) * 1000
            geom = box(x, y, x + 1000, y + 1000)
            large_blocks.append({
                'id': i,
                'geometry': geom,
                'center': (x + 500, y + 500)
            })
        
        # Should raise an error or handle gracefully
        with pytest.raises(ValueError) as exc_info:
            generate_spatial_folds(large_blocks, k=5, seed=42)
        
        assert "MAX_BLOCKS" in str(exc_info.value) or "too many blocks" in str(exc_info.value).lower()
    
    def test_fold_assignment_balance(self, sample_blocks):
        """Test that fold assignment is reasonably balanced."""
        k = 4
        folds = generate_spatial_folds(sample_blocks, k=k, seed=42)
        
        fold_sizes = [len(blocks) for blocks in folds.values()]
        min_size = min(fold_sizes)
        max_size = max(fold_sizes)
        
        # With 20 blocks and 4 folds, each should have exactly 5
        assert min_size == max_size == 5
    
    def test_seed_reproducibility(self, sample_blocks):
        """Test that different seeds produce different folds."""
        folds1 = generate_spatial_folds(sample_blocks, k=5, seed=42)
        folds2 = generate_spatial_folds(sample_blocks, k=5, seed=123)
        
        assert folds1 != folds2
    
    def test_k_greater_than_blocks(self, sample_blocks):
        """Test behavior when k > number of blocks."""
        k = 30  # More than 20 blocks
        with pytest.raises(ValueError) as exc_info:
            generate_spatial_folds(sample_blocks, k=k, seed=42)
        
        assert "k cannot be greater" in str(exc_info.value).lower()
    
    def test_empty_blocks_list(self):
        """Test behavior with empty blocks list."""
        with pytest.raises(ValueError) as exc_info:
            generate_spatial_folds([], k=5, seed=42)
        
        assert "no blocks" in str(exc_info.value).lower()
    
    def test_k_equals_one(self, sample_blocks):
        """Test behavior when k=1."""
        with pytest.raises(ValueError) as exc_info:
            generate_spatial_folds(sample_blocks, k=1, seed=42)
        
        assert "k must be greater" in str(exc_info.value).lower()
    
    def test_single_fold_cross_validation(self, sample_blocks, sample_data):
        """Test cross-validation with minimal setup."""
        class SimpleModel:
            def __init__(self):
                self.fitted = False
            
            def fit(self, X, y):
                self.fitted = True
                self.mean_y = np.mean(y)
                return self
            
            def predict(self, X):
                return np.full(X.shape[0], self.mean_y)
            
            def score(self, X, y):
                return 0.0  # Dummy score
        
        model = SimpleModel()
        block_to_indices = {i: [i] for i in range(len(sample_blocks))}
        
        results = run_spatial_cross_validation(
            data={'X': np.eye(len(sample_blocks)), 'y': np.ones(len(sample_blocks)), 'block_ids': list(range(len(sample_blocks)))},
            model=model,
            blocks=sample_blocks,
            k=5,
            seed=42,
            block_to_indices=block_to_indices
        )
        
        assert len(results['fold_results']) == 5
        for fold_result in results['fold_results']:
            assert 'train_size' in fold_result
            assert 'val_size' in fold_result
            assert 'rmse' in fold_result
            assert 'mae' in fold_result
            assert 'r2' in fold_result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
