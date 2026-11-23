"""
Unit tests for spatial proxy generation and validation logic.

Tests the generate_spatial_proxy and related functions from
code/dependency_injector.py using mock data fixtures.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dependency_injector import (
    generate_spatial_proxy,
    validate_feature_space_proxy,
    save_spatial_proxy_report
)
from tests.unit.test_dependency_injector_fixtures import (
    create_spatial_proxy_fixture,
    assert_cluster_separation
)


class TestSpatialProxy:
    """Tests for spatial proxy generation functionality."""
    
    def test_generate_spatial_proxy_creates_coordinates(self):
        """Test that spatial proxy generates valid coordinate data."""
        # Arrange
        n_points = 100
        n_features = 5
        n_clusters = 3
        seed = 42
        
        df, _ = create_spatial_proxy_fixture(
            n_points=n_points, 
            n_features=n_features, 
            n_clusters=n_clusters, 
            seed=seed
        )
        
        # Act
        proxy_df = generate_spatial_proxy(df, n_clusters=n_clusters, seed=seed)
        
        # Assert
        assert 'x' in proxy_df.columns
        assert 'y' in proxy_df.columns
        assert len(proxy_df) == n_points
    
    def test_generate_spatial_proxy_preserves_rows(self):
        """Test that proxy generation preserves the number of rows."""
        # Arrange
        n_points = 50
        df, _ = create_spatial_proxy_fixture(n_points=n_points, seed=42)
        
        # Act
        proxy_df = generate_spatial_proxy(df, n_clusters=2, seed=42)
        
        # Assert
        assert len(proxy_df) == n_points
    
    def test_validate_feature_space_proxy_success(self):
        """Test validation passes for well-structured proxy."""
        # Arrange
        n_points = 100
        df, _ = create_spatial_proxy_fixture(n_points=n_points, n_clusters=3, seed=42)
        proxy_df = generate_spatial_proxy(df, n_clusters=3, seed=42)
        
        # Act
        is_valid, metrics = validate_feature_space_proxy(proxy_df, df)
        
        # Assert
        assert is_valid
    
    def test_generate_spatial_proxy_with_single_cluster(self):
        """Test proxy generation with only one cluster."""
        # Arrange
        n_points = 50
        df, _ = create_spatial_proxy_fixture(n_points=n_points, n_clusters=1, seed=42)
        
        # Act
        proxy_df = generate_spatial_proxy(df, n_clusters=1, seed=42)
        
        # Assert
        assert len(proxy_df) == n_points
        assert 'x' in proxy_df.columns
        assert 'y' in proxy_df.columns
    
    def test_spatial_proxy_report_generation(self):
        """Test that spatial proxy report can be generated and saved."""
        # Arrange
        n_points = 100
        df, metadata = create_spatial_proxy_fixture(n_points=n_points, n_clusters=3, seed=42)
        proxy_df = generate_spatial_proxy(df, n_clusters=3, seed=42)
        
        # Act
        report = {
            'n_points': n_points,
            'n_clusters': 3,
            'proxy_columns': list(proxy_df.columns),
            'validation_status': 'passed'
        }
        save_spatial_proxy_report(report, 'data/manifests/test_spatial_proxy_report.json')
        
        # Assert: File exists and is valid JSON
        report_path = Path('data/manifests/test_spatial_proxy_report.json')
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report['n_points'] == n_points
        
        # Cleanup
        report_path.unlink()
    
    def test_generate_spatial_proxy_deterministic(self):
        """Test that proxy generation is deterministic with same seed."""
        # Arrange
        n_points = 50
        df, _ = create_spatial_proxy_fixture(n_points=n_points, seed=42)
        
        # Act
        proxy1 = generate_spatial_proxy(df, n_clusters=2, seed=123)
        proxy2 = generate_spatial_proxy(df, n_clusters=2, seed=123)
        
        # Assert
        assert np.allclose(proxy1['x'], proxy2['x'])
        assert np.allclose(proxy1['y'], proxy2['y'])
    
    def test_generate_spatial_proxy_with_large_n(self):
        """Test proxy generation with a larger dataset."""
        # Arrange
        n_points = 1000
        df, _ = create_spatial_proxy_fixture(n_points=n_points, n_clusters=5, seed=42)
        
        # Act
        proxy_df = generate_spatial_proxy(df, n_clusters=5, seed=42)
        
        # Assert
        assert len(proxy_df) == n_points
        assert proxy_df['x'].notna().all()
        assert proxy_df['y'].notna().all()
