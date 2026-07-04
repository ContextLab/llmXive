"""
Unit tests for memory safety utilities (code/utils/memory.py).
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.memory import (
    estimate_array_memory_gb,
    estimate_geodataframe_memory_gb,
    generate_spatial_blocks,
    sample_spatial_blocks,
    check_memory_constraint,
    estimate_matrix_size
)
from code.config import MAX_BLOCKS


class TestMemoryEstimation:
    def test_array_memory_gb(self):
        # Create a small array: 1000 * 1000 * 8 bytes = 8MB
        arr = np.zeros((1000, 1000), dtype=np.float64)
        expected_gb = (1000 * 1000 * 8) / (1024 ** 3)
        assert abs(estimate_array_memory_gb(arr) - expected_gb) < 1e-6
        
    def test_array_memory_none(self):
        assert estimate_array_memory_gb(None) == 0.0
        
    def test_geodataframe_memory_gb(self):
        # Create a simple GeoDataFrame
        gdf = gpd.GeoDataFrame({'col1': [1, 2, 3]}, geometry=[box(0,0,1,1), box(1,1,2,2), box(2,2,3,3)])
        assert estimate_geodataframe_memory_gb(gdf) > 0
        
    def test_geodataframe_memory_none(self):
        assert estimate_geodataframe_memory_gb(None) == 0.0
        
    def test_matrix_size(self):
        # 1M elements of float64
        size = estimate_matrix_size(1000, 1000)
        expected = (1000 * 1000 * 8) / (1024 ** 3)
        assert abs(size - expected) < 1e-6


class TestSpatialBlocks:
    def test_generate_blocks_small(self):
        # Generate blocks for a tiny area (10km x 10km) with 1km blocks
        bounds = (0, 0, 0.1, 0.1) # Approx 11km x 11km in degrees at equator
        gdf = generate_spatial_blocks(bounds, block_size_km=1.0)
        assert not gdf.empty
        assert 'block_id' in gdf.columns
        assert gdf.crs == "EPSG:3857"
        
    def test_sample_blocks_full(self):
        # Create 10 blocks
        gdf = generate_spatial_blocks((0, 0, 0.1, 0.1), block_size_km=0.5)
        sampled = sample_spatial_blocks(gdf, max_blocks=100, seed=42)
        assert len(sampled) == len(gdf)
        
    def test_sample_blocks_subset(self):
        # Create many blocks (simulate)
        # We can't easily create 200 blocks in a test without large bounds,
        # so we mock the count or use a larger bounds.
        # Let's use a larger bounds to ensure we get > 10 blocks.
        gdf = generate_spatial_blocks((-74.3, 40.4, -73.7, 40.9), block_size_km=1.0)
        if len(gdf) > 10:
            sampled = sample_spatial_blocks(gdf, max_blocks=10, seed=42)
            assert len(sampled) == 10
            # Check reproducibility
            sampled2 = sample_spatial_blocks(gdf, max_blocks=10, seed=42)
            assert list(sampled['block_id']) == list(sampled2['block_id'])
        else:
            # If not enough blocks, just check it returns all
            sampled = sample_spatial_blocks(gdf, max_blocks=10, seed=42)
            assert len(sampled) == len(gdf)

class TestMemoryConstraint:
    def test_within_limit(self):
        assert check_memory_constraint(5.0, limit_gb=7.0) == True
        
    def test_exceeds_limit(self):
        assert check_memory_constraint(6.5, limit_gb=7.0) == False # 6.5 > 7.0 * 0.8 (5.6)
        
    def test_exactly_limit(self):
        # 5.6 is 80% of 7.0
        assert check_memory_constraint(5.6, limit_gb=7.0) == True