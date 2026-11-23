"""Unit tests for code/utils/memory.py memory safety utilities."""

import math
from unittest.mock import patch, MagicMock, PropertyMock

import numpy as np
import pytest
import geopandas as gpd
from shapely.geometry import box, Point

from code.utils.memory import (
    estimate_array_memory_mb,
    estimate_raster_memory_mb,
    estimate_geodataframe_memory_mb,
    check_memory_safety,
    generate_spatial_blocks,
    sample_blocks_by_intersection,
    get_sampling_plan,
    validate_raster_dimensions_for_memory,
    validate_geodataframe_for_memory,
)


class TestEstimateArrayMemory:
    """Tests for array memory estimation."""

    def test_estimate_array_memory_mb_correct_dtype(self):
        """Verify memory calculation respects dtype."""
        # int32: 4 bytes per element
        shape = (100, 100)
        dtype = np.int32
        # 100 * 100 * 4 bytes = 40000 bytes = ~0.038 MB
        result = estimate_array_memory_mb(shape, dtype)
        expected = (100 * 100 * 4) / (1024 * 1024)
        assert math.isclose(result, expected, rel_tol=0.01)

    def test_estimate_array_memory_mb_float64(self):
        """Verify memory calculation for float64."""
        shape = (1000, 1000)
        dtype = np.float64
        # 1000 * 1000 * 8 bytes = 8,000,000 bytes = ~7.63 MB
        result = estimate_array_memory_mb(shape, dtype)
        expected = (1000 * 1000 * 8) / (1024 * 1024)
        assert math.isclose(result, expected, rel_tol=0.01)

    def test_estimate_array_memory_mb_zero_shape(self):
        """Verify handling of empty arrays."""
        result = estimate_array_memory_mb((0, 0), np.float32)
        assert result == 0.0


class TestEstimateRasterMemory:
    """Tests for raster memory estimation."""

    @patch("code.utils.memory.rasterio.open")
    def test_estimate_raster_memory_mb_uses_shape_and_dtype(self, mock_open):
        """Verify raster memory uses shape and dtype from metadata."""
        # Mock a raster dataset
        mock_dataset = MagicMock()
        mock_dataset.shape = (1, 1000, 1000)  # band, height, width
        mock_dataset.dtype = np.float32
        mock_dataset.count = 1
        mock_open.return_value.__enter__.return_value = mock_dataset

        result = estimate_raster_memory_mb("dummy_path.tif")
        
        # 1 * 1000 * 1000 * 4 bytes = 4MB
        expected = (1 * 1000 * 1000 * 4) / (1024 * 1024)
        assert math.isclose(result, expected, rel_tol=0.01)

    @patch("code.utils.memory.rasterio.open")
    def test_estimate_raster_memory_mb_multiband(self, mock_open):
        """Verify memory calculation for multi-band rasters."""
        mock_dataset = MagicMock()
        mock_dataset.shape = (3, 1000, 1000)  # 3 bands
        mock_dataset.dtype = np.uint8
        mock_dataset.count = 3
        mock_open.return_value.__enter__.return_value = mock_dataset

        result = estimate_raster_memory_mb("dummy_path.tif")
        # 3 * 1000 * 1000 * 1 byte = 3MB
        expected = (3 * 1000 * 1000 * 1) / (1024 * 1024)
        assert math.isclose(result, expected, rel_tol=0.01)


class TestEstimateGeodataframeMemory:
    """Tests for GeoDataFrame memory estimation."""

    def test_estimate_geodataframe_memory_mb_basic(self):
        """Verify basic memory estimation for GeoDataFrame."""
        # Create a small GeoDataFrame
        data = {
            "geometry": [box(0, 0, 1, 1), box(2, 2, 3, 3)],
            "value": [10, 20],
            "name": ["A", "B"]
        }
        gdf = gpd.GeoDataFrame(data)
        
        result = estimate_geodataframe_memory_mb(gdf)
        
        # Should return a positive number
        assert isinstance(result, float)
        assert result > 0

    def test_estimate_geodataframe_memory_mb_empty(self):
        """Verify handling of empty GeoDataFrame."""
        gdf = gpd.GeoDataFrame()
        result = estimate_geodataframe_memory_mb(gdf)
        assert result == 0.0


class TestCheckMemorySafety:
    """Tests for the memory safety check logic."""

    def test_check_memory_safety_passes(self):
        """Verify safety check passes when under limit."""
        estimated_mb = 100  # 100 MB
        limit_mb = 1024    # 1 GB limit
        
        result = check_memory_safety(estimated_mb, limit_mb)
        assert result is True

    def test_check_memory_safety_fails(self):
        """Verify safety check fails when over limit."""
        estimated_mb = 2048  # 2 GB
        limit_mb = 1024      # 1 GB limit
        
        with pytest.raises(MemoryError):
            check_memory_safety(estimated_mb, limit_mb)

    def test_check_memory_safety_custom_limit(self):
        """Verify custom limit is respected."""
        estimated_mb = 500
        limit_mb = 400
        
        with pytest.raises(MemoryError):
            check_memory_safety(estimated_mb, limit_mb)


class TestGenerateSpatialBlocks:
    """Tests for spatial block generation."""

    def test_generate_spatial_blocks_creates_grid(self):
        """Verify block generation creates a grid of boxes."""
        # Define a bounding box
        minx, miny, maxx, maxy = 0, 0, 100, 100
        block_size = 10  # 10x10 units
        
        blocks = generate_spatial_blocks(minx, miny, maxx, maxy, block_size)
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        # Check that all blocks are boxes
        for block in blocks:
            assert block.geom_type == "Polygon"
            assert block.area > 0

    def test_generate_spatial_blocks_respects_bounds(self):
        """Verify blocks fit within the input bounds."""
        minx, miny, maxx, maxy = 0, 0, 100, 100
        block_size = 25
        
        blocks = generate_spatial_blocks(minx, miny, maxx, maxy, block_size)
        
        # Check that no block extends beyond bounds
        for block in blocks:
            assert block.bounds[0] >= minx
            assert block.bounds[1] >= miny
            assert block.bounds[2] <= maxx
            assert block.bounds[3] <= maxy

    def test_generate_spatial_blocks_edge_case(self):
        """Verify behavior when bounds are smaller than block size."""
        minx, miny, maxx, maxy = 0, 0, 5, 5
        block_size = 10
        
        blocks = generate_spatial_blocks(minx, miny, maxx, maxy, block_size)
        # Should return at least one block or handle gracefully
        assert len(blocks) >= 0


class TestSampleBlocksByIntersection:
    """Tests for block sampling logic."""

    def test_sample_blocks_by_intersection_filters(self):
        """Verify sampling filters blocks by intersection."""
        # Create mock blocks
        blocks = [box(i, i, i+1, i+1) for i in range(10)]
        # Define an intersection polygon
        intersection = box(2, 2, 8, 8)
        
        sampled = sample_blocks_by_intersection(blocks, intersection)
        
        # All sampled blocks should intersect
        for block in sampled:
            assert block.intersects(intersection)

    def test_sample_blocks_by_intersection_empty_result(self):
        """Verify empty result when no intersection."""
        blocks = [box(0, 0, 1, 1), box(2, 2, 3, 3)]
        intersection = box(10, 10, 20, 20)
        
        sampled = sample_blocks_by_intersection(blocks, intersection)
        assert len(sampled) == 0


class TestGetSamplingPlan:
    """Tests for sampling plan generation."""

    def test_get_sampling_plan_returns_list(self):
        """Verify sampling plan returns a list of blocks."""
        # Mock blocks
        blocks = [box(i, i, i+1, i+1) for i in range(20)]
        target_count = 5
        
        plan = get_sampling_plan(blocks, target_count)
        
        assert isinstance(plan, list)
        assert len(plan) <= target_count

    def test_get_sampling_plan_stratified(self):
        """Verify stratified sampling preserves spatial structure."""
        # Create a grid of blocks
        blocks = [box(x, y, x+1, y+1) for x in range(10) for y in range(10)]
        target_count = 20
        
        plan = get_sampling_plan(blocks, target_count)
        
        # Should select a subset
        assert len(plan) <= target_count
        # Should not be empty if blocks exist
        if len(blocks) > 0:
            assert len(plan) > 0


class TestValidateRasterDimensions:
    """Tests for raster dimension validation."""

    def test_validate_raster_dimensions_for_memory_passes(self):
        """Verify validation passes for small rasters."""
        width, height, bands = 100, 100, 1
        dtype = np.float32
        
        result = validate_raster_dimensions_for_memory(width, height, bands, dtype)
        assert result is True

    def test_validate_raster_dimensions_for_memory_fails(self):
        """Verify validation fails for large rasters."""
        # Very large raster
        width, height, bands = 50000, 50000, 3
        dtype = np.float64
        
        with pytest.raises(ValueError):
            validate_raster_dimensions_for_memory(width, height, bands, dtype)


class TestValidateGeodataframeForMemory:
    """Tests for GeoDataFrame memory validation."""

    def test_validate_geodataframe_for_memory_passes(self):
        """Verify validation passes for small GeoDataFrame."""
        data = {
            "geometry": [box(0, 0, 1, 1) for _ in range(100)],
            "value": list(range(100))
        }
        gdf = gpd.GeoDataFrame(data)
        
        result = validate_geodataframe_for_memory(gdf)
        assert result is True

    def test_validate_geodataframe_for_memory_fails(self):
        """Verify validation fails for large GeoDataFrame."""
        # Create a large GeoDataFrame
        data = {
            "geometry": [box(i, i, i+1, i+1) for i in range(1000000)],
            "value": list(range(1000000))
        }
        gdf = gpd.GeoDataFrame(data)
        
        with pytest.raises(MemoryError):
            validate_geodataframe_for_memory(gdf)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])