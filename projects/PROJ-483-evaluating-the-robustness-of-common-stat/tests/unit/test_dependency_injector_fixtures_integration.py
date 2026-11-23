"""
Integration tests for dependency injection fixtures.

These tests ensure that the fixtures work correctly with the actual
dependency injection pipeline.
"""
import numpy as np
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dependency_injector import ar1_inject, block_bootstrap, generate_spatial_proxy
from tests.unit.test_dependency_injector_fixtures import (
    create_ar1_fixture,
    create_independent_fixture,
    create_block_bootstrap_fixture,
    create_spatial_proxy_fixture,
    assert_autocorrelation_matches
)


class TestFixtureIntegration:
    """Integration tests ensuring fixtures work with real injection logic."""
    
    def test_ar1_fixture_workflow(self):
        """Test complete workflow: independent fixture -> AR(1) injection -> validation."""
        # Arrange
        n = 500
        target_rho = 0.4
        seed = 42
        
        # Act 1: Create independent data
        independent_data, meta = create_independent_fixture(n=n, seed=seed)
        
        # Act 2: Inject dependency
        injected_data = ar1_inject(independent_data, rho=target_rho, seed=seed)
        
        # Act 3: Validate
        is_valid, actual_rho, _ = validate_ar1_injection(injected_data, target_rho)
        
        # Assert
        assert is_valid
        assert abs(actual_rho - target_rho) < 0.05
    
    def test_block_bootstrap_fixture_workflow(self):
        """Test complete workflow: block fixture -> bootstrap -> structure check."""
        # Arrange
        n = 200
        block_size = 10
        seed = 42
        
        # Act 1: Create block-structured data
        original_data, meta = create_block_bootstrap_fixture(
            n=n, block_size=block_size, seed=seed
        )
        
        # Act 2: Bootstrap
        resampled = block_bootstrap(original_data, block_size=block_size, n_replicates=1, seed=seed)
        
        # Assert: Length preserved
        assert len(resampled) == n
    
    def test_spatial_proxy_fixture_workflow(self):
        """Test complete workflow: feature fixture -> spatial proxy -> validation."""
        # Arrange
        n_points = 100
        n_clusters = 3
        seed = 42
        
        # Act 1: Create feature data
        feature_df, meta = create_spatial_proxy_fixture(
            n_points=n_points, n_clusters=n_clusters, seed=seed
        )
        
        # Act 2: Generate proxy
        proxy_df = generate_spatial_proxy(feature_df, n_clusters=n_clusters, seed=seed)
        
        # Assert: Proxy has coordinates
        assert 'x' in proxy_df.columns
        assert 'y' in proxy_df.columns
        assert len(proxy_df) == n_points
