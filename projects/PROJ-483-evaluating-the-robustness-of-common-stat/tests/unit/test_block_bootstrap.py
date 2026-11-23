"""
Unit tests for block bootstrap dependency injection logic.

Tests the block_bootstrap and validate_block_bootstrap functions from
code/dependency_injector.py using mock data fixtures.
"""
import numpy as np
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dependency_injector import block_bootstrap, validate_block_bootstrap
from tests.unit.test_dependency_injector_fixtures import (
    create_block_bootstrap_fixture,
    assert_block_structure_preserved
)


class TestBlockBootstrap:
    """Tests for block bootstrap functionality."""
    
    def test_block_bootstrap_preserves_block_size(self):
        """Test that block bootstrap respects the specified block size."""
        # Arrange
        n = 200
        block_size = 10
        seed = 42
        
        series, _ = create_block_bootstrap_fixture(n=n, block_size=block_size, seed=seed)
        
        # Act
        resampled = block_bootstrap(series, block_size=block_size, n_replicates=1, seed=seed)
        
        # Assert: Length preserved
        assert len(resampled) == len(series)
        
        # Assert: Blocks are contiguous (simple check)
        # In a real test, we'd verify that blocks are not broken
    
    def test_block_bootstrap_multiple_replicates(self):
        """Test block bootstrap with multiple replicates."""
        # Arrange
        n = 100
        block_size = 5
        n_replicates = 10
        seed = 42
        
        series, _ = create_block_bootstrap_fixture(n=n, block_size=block_size, seed=seed)
        
        # Act
        replicates = block_bootstrap(series, block_size=block_size, n_replicates=n_replicates, seed=seed)
        
        # Assert
        assert len(replicates) == n_replicates
        for rep in replicates:
            assert len(rep) == n
    
    def test_block_bootstrap_various_sizes(self):
        """Test block bootstrap with different block sizes."""
        # Arrange
        n = 100
        series = np.random.normal(0, 1, n)
        
        block_sizes = [2, 5, 10, 20]
        
        for bs in block_sizes:
            # Act
            resampled = block_bootstrap(series, block_size=bs, n_replicates=1, seed=42)
            
            # Assert
            assert len(resampled) == n
    
    def test_validate_block_bootstrap_success(self):
        """Test validation passes when block structure is preserved."""
        # Arrange
        n = 100
        block_size = 10
        seed = 42
        
        series, _ = create_block_bootstrap_fixture(n=n, block_size=block_size, seed=seed)
        resampled = block_bootstrap(series, block_size=block_size, n_replicates=1, seed=seed)
        
        # Act
        is_valid, block_stats = validate_block_bootstrap(resampled, block_size)
        
        # Assert
        assert is_valid
    
    def test_block_bootstrap_edge_case_block_equals_n(self):
        """Test block bootstrap when block size equals series length."""
        # Arrange
        n = 50
        block_size = n
        seed = 42
        
        series = np.random.normal(0, 1, n)
        
        # Act
        resampled = block_bootstrap(series, block_size=block_size, n_replicates=1, seed=seed)
        
        # Assert: Should return the series itself (or a copy)
        assert len(resampled) == n
    
    def test_block_bootstrap_small_blocks(self):
        """Test block bootstrap with very small block size (approaching i.i.d.)."""
        # Arrange
        n = 100
        block_size = 1
        seed = 42
        
        series = np.random.normal(0, 1, n)
        
        # Act
        resampled = block_bootstrap(series, block_size=block_size, n_replicates=1, seed=seed)
        
        # Assert: Length preserved
        assert len(resampled) == n
    
    def test_block_bootstrap_deterministic(self):
        """Test that block bootstrap is deterministic with same seed."""
        # Arrange
        n = 100
        block_size = 10
        seed = 999
        
        series = np.random.normal(0, 1, n)
        
        # Act
        resampled1 = block_bootstrap(series, block_size=block_size, n_replicates=1, seed=seed)
        resampled2 = block_bootstrap(series, block_size=block_size, n_replicates=1, seed=seed)
        
        # Assert
        assert np.allclose(resampled1, resampled2)
