"""
Unit tests for memory safety utilities.
"""
import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from unittest.mock import patch
from config import get_city_crs

from utils.memory import (
    estimate_array_memory_mb,
    estimate_raster_memory_mb,
    estimate_geodataframe_memory_mb,
    check_memory_safety,
    generate_spatial_blocks,
    sample_blocks_by_intersection,
    get_sampling_plan,
    validate_raster_dimensions_for_memory,
    validate_geodataframe_for_memory
)

class TestEstimateArrayMemory:
    def test_estimate_array_memory_mb(self):
        """Test memory estimation for numpy arrays."""
        # Create a small array: 100x100 float64 = 80,000 bytes = ~0.076 MB
        arr = np.zeros((100, 100), dtype=np.float64)
        expected_mb = 80000 / (1024 * 1024)
        assert abs(estimate_array_memory_mb(arr) - expected_mb) < 0.001

    def test_estimate_array_memory_mb_int32(self):
        """Test memory estimation for int32 arrays."""
        # 100x100 int32 = 40,000 bytes
        arr = np.zeros((100, 100), dtype=np.int32)
        expected_mb = 40000 / (1024 * 1024)
        assert abs(estimate_array_memory_mb(arr) - expected_mb) < 0.001

class TestEstimateRasterMemory:
    def test_estimate_raster_memory_mb(self):
        """Test memory estimation for rasters."""
        # 1000x1000 pixels, 1 band, float32 = 4 bytes per pixel
        # Total: 1000 * 1000 * 1 * 4 = 4,000,000 bytes = ~3.81 MB
        width, height, bands = 1000, 1000, 1
        dtype = np.float32
        expected_mb = (width * height * bands * 4) / (1024 * 1024)
        assert abs(estimate_raster_memory_mb(width, height, bands, dtype) - expected_mb) < 0.01

    def test_estimate_raster_memory_mb_multiband(self):
        """Test memory estimation for multi-band rasters."""
        width, height, bands = 1000, 1000, 3
        dtype = np.uint8
        expected_mb = (width * height * bands * 1) / (1024 * 1024)
        assert abs(estimate_raster_memory_mb(width, height, bands, dtype) - expected_mb) < 0.01

class TestEstimateGeodataframeMemory:
    def test_estimate_geodataframe_memory_mb(self):
        """Test memory estimation for GeoDataFrames."""
        # Create a simple GeoDataFrame
        data = {
            'id': range(100),
            'geometry': [box(i, i, i+1, i+1) for i in range(100)]
        }
        gdf = gpd.GeoDataFrame(data, crs=get_city_crs())
        mem_mb = estimate_geodataframe_memory_mb(gdf)
        assert mem_mb > 0

class TestCheckMemorySafety:
    def test_check_memory_safety_pass(self):
        """Test that check_memory_safety passes when within limits."""
        # Should not raise
        check_memory_safety(100.0, max_memory_mb=1000.0, context="Test")

    def test_check_memory_safety_fail(self):
        """Test that check_memory_safety raises MemoryError when exceeded."""
        with pytest.raises(MemoryError) as exc_info:
            check_memory_safety(1000.0, max_memory_mb=100.0, context="Test")
        assert "exceeds the safety limit" in str(exc_info.value)

    def test_check_memory_safety_default_limit(self):
        """Test that check_memory_safety uses default limit when not specified."""
        # Default is 5GB = 5120 MB
        # Should pass with 100 MB
        check_memory_safety(100.0, context="Test")
        
        # Should fail with 6000 MB (exceeds 5120 MB default)
        with pytest.raises(MemoryError):
            check_memory_safety(6000.0, context="Test")

class TestValidateRasterDimensions:
    def test_validate_raster_dimensions_pass(self):
        """Test validation passes for small raster."""
        # Small raster should pass
        validate_raster_dimensions_for_memory(
            width=100, height=100, bands=1, dtype=np.float32,
            max_memory_mb=1000.0
        )

    def test_validate_raster_dimensions_fail(self):
        """Test validation fails for large raster."""
        with pytest.raises(MemoryError):
            validate_raster_dimensions_for_memory(
                width=10000, height=10000, bands=10, dtype=np.float64,
                max_memory_mb=10.0
            )

class TestValidateGeodataframeMemory:
    def test_validate_geodataframe_pass(self):
        """Test validation passes for small GeoDataFrame."""
        data = {
            'id': range(10),
            'geometry': [box(i, i, i+1, i+1) for i in range(10)]
        }
        gdf = gpd.GeoDataFrame(data, crs=get_city_crs())
        validate_geodataframe_for_memory(gdf, max_memory_mb=1000.0)

    def test_validate_geodataframe_fail(self):
        """Test validation fails for large GeoDataFrame."""
        # Create a very large GeoDataFrame
        n = 1000000
        data = {
            'id': range(n),
            'geometry': [box(i, i, i+1, i+1) for i in range(n)]
        }
        gdf = gpd.GeoDataFrame(data, crs=get_city_crs())
        with pytest.raises(MemoryError):
            validate_geodataframe_for_memory(gdf, max_memory_mb=1.0)

class TestGenerateSpatialBlocks:
    def test_generate_spatial_blocks_basic(self):
        """Test basic block generation."""
        bounds = (0, 0, 10000, 10000)  # 10km x 10km
        block_size = 1000.0  # 1km blocks
        blocks = generate_spatial_blocks(bounds, block_size)
        
        assert len(blocks) == 100  # 10x10 grid
        assert 'block_id' in blocks.columns
        assert 'geometry' in blocks.columns

    def test_generate_spatial_blocks_crs(self):
        """Test that blocks have correct CRS."""
        bounds = (0, 0, 10000, 10000)
        blocks = generate_spatial_blocks(bounds, 1000.0)
        assert blocks.crs is not None

class TestSampleBlocksByIntersection:
    def test_sample_blocks_by_intersection_basic(self):
        """Test basic block sampling."""
        # Create data that intersects some blocks
        data = gpd.GeoDataFrame({
            'id': [1, 2, 3],
            'geometry': [box(500, 500, 1500, 1500), box(2500, 2500, 3500, 3500), box(5000, 5000, 6000, 6000)]
        }, crs=get_city_crs())
        
        bounds = (0, 0, 10000, 10000)
        blocks = generate_spatial_blocks(bounds, 1000.0)
        
        sampled = sample_blocks_by_intersection(data, blocks)
        assert len(sampled) > 0
        assert all(bid in blocks['block_id'].values for bid in sampled)

    def test_sample_blocks_by_intersection_max_blocks(self):
        """Test sampling with max_blocks limit."""
        data = gpd.GeoDataFrame({
            'id': range(100),
            'geometry': [box(i*100, i*100, i*100+500, i*100+500) for i in range(100)]
        }, crs=get_city_crs())
        
        bounds = (0, 0, 10000, 10000)
        blocks = generate_spatial_blocks(bounds, 1000.0)
        
        sampled = sample_blocks_by_intersection(data, blocks, max_blocks=5)
        assert len(sampled) <= 5

    def test_sample_blocks_by_intersection_no_intersection(self):
        """Test sampling when no blocks intersect."""
        data = gpd.GeoDataFrame({
            'id': [1],
            'geometry': [box(-10000, -10000, -9000, -9000)]
        }, crs=get_city_crs())
        
        bounds = (0, 0, 10000, 10000)
        blocks = generate_spatial_blocks(bounds, 1000.0)
        
        sampled = sample_blocks_by_intersection(data, blocks)
        assert sampled == []

class TestGetSamplingPlan:
    def test_get_sampling_plan_basic(self):
        """Test basic sampling plan generation."""
        data = gpd.GeoDataFrame({
            'id': [1, 2],
            'geometry': [box(500, 500, 1500, 1500), box(2500, 2500, 3500, 3500)]
        }, crs=get_city_crs())
        
        bounds = (0, 0, 10000, 10000)
        plan = get_sampling_plan(data, bounds, block_size_m=1000.0)
        
        assert len(plan) > 0
        assert all(isinstance(bid, int) for bid in plan)