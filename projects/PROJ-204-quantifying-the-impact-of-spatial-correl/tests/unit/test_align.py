"""
Unit tests for the align.py module.

Tests cover:
- Target grid shape calculation with various methods
- Resampling with different interpolation methods
- Map alignment with dimension mismatches
- Validation of aligned maps
"""

import numpy as np
import pytest
from pathlib import Path
import sys

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.align import (
    calculate_target_grid_shape,
    resample_map,
    align_maps,
    validate_alignment,
    create_aligned_dataset,
)


class TestCalculateTargetGridShape:
    def test_empty_shapes_raises_error(self):
        with pytest.raises(ValueError, match="At least one map shape must be provided"):
            calculate_target_grid_shape([])

    def test_min_method(self):
        shapes = [(100, 100), (50, 80), (120, 90)]
        target = calculate_target_grid_shape(shapes, method="min")
        assert target == (50, 80)

    def test_max_method(self):
        shapes = [(100, 100), (50, 80), (120, 90)]
        target = calculate_target_grid_shape(shapes, method="max")
        assert target == (120, 90)

    def test_median_method(self):
        shapes = [(100, 100), (50, 80), (120, 90)]
        target = calculate_target_grid_shape(shapes, method="median")
        # Median of [100, 50, 120] is 100
        # Median of [100, 80, 90] is 90
        assert target == (100, 90)

    def test_average_method(self):
        shapes = [(100, 100), (50, 80), (120, 90)]
        target = calculate_target_grid_shape(shapes, method="average")
        # Average height: (100+50+120)/3 = 90
        # Average width: (100+80+90)/3 = 90
        assert target == (90, 90)

    def test_unknown_method_raises_error(self):
        shapes = [(100, 100)]
        with pytest.raises(ValueError, match="Unknown alignment method"):
            calculate_target_grid_shape(shapes, method="unknown")

    def test_minimum_size_enforcement(self):
        shapes = [(1, 1)]
        target = calculate_target_grid_shape(shapes, method="min")
        assert target == (2, 2)  # Enforced minimum


class TestResampleMap:
    def test_same_shape_returns_copy(self):
        data = np.random.rand(10, 10)
        result = resample_map(data, (10, 10))
        assert result.shape == data.shape
        np.testing.assert_array_equal(result, data)

    def test_upsampling_linear(self):
        data = np.ones((2, 2))
        result = resample_map(data, (4, 4), method="linear")
        assert result.shape == (4, 4)
        # Upsampled values should be close to 1.0
        assert np.allclose(result, 1.0, atol=0.1)

    def test_downsampling_linear(self):
        data = np.ones((4, 4))
        result = resample_map(data, (2, 2), method="linear")
        assert result.shape == (2, 2)
        assert np.allclose(result, 1.0, atol=0.1)

    def test_nearest_neighbor(self):
        data = np.array([[0.0, 1.0], [2.0, 3.0]])
        result = resample_map(data, (4, 4), method="nearest")
        assert result.shape == (4, 4)

    def test_cubic_interpolation(self):
        data = np.random.rand(10, 10)
        result = resample_map(data, (20, 20), method="cubic")
        assert result.shape == (20, 20)

    def test_spline_interpolation(self):
        data = np.random.rand(10, 10)
        result = resample_map(data, (20, 20), method="spline")
        assert result.shape == (20, 20)

    def test_invalid_input_dimension(self):
        data = np.random.rand(10, 10, 10)
        with pytest.raises(ValueError, match="Input data must be 2D"):
            resample_map(data, (20, 20))

    def test_unknown_interpolation_method(self):
        data = np.random.rand(10, 10)
        with pytest.raises(ValueError, match="Unknown interpolation method"):
            resample_map(data, (20, 20), method="unknown")


class TestAlignMaps:
    def test_empty_maps_raises_error(self):
        with pytest.raises(ValueError, match="Maps dictionary cannot be empty"):
            align_maps({})

    def test_single_map_unchanged_if_same_shape(self):
        data = np.random.rand(10, 10)
        maps = {"Pb": data}
        result = align_maps(maps)
        assert result["Pb"].shape == (10, 10)

    def test_multiple_maps_aligned_to_min(self):
        data1 = np.random.rand(100, 100)
        data2 = np.random.rand(50, 80)
        maps = {"Pb": data1, "I": data2}
        result = align_maps(maps, alignment_method="min")
        assert result["Pb"].shape == (50, 80)
        assert result["I"].shape == (50, 80)

    def test_multiple_maps_aligned_to_max(self):
        data1 = np.random.rand(100, 100)
        data2 = np.random.rand(50, 80)
        maps = {"Pb": data1, "I": data2}
        result = align_maps(maps, alignment_method="max")
        assert result["Pb"].shape == (100, 100)
        assert result["I"].shape == (100, 100)

    def test_explicit_target_shape(self):
        data1 = np.random.rand(100, 100)
        data2 = np.random.rand(50, 80)
        maps = {"Pb": data1, "I": data2}
        result = align_maps(maps, target_shape=(60, 70))
        assert result["Pb"].shape == (60, 70)
        assert result["I"].shape == (60, 70)

    def test_non_2d_array_raises_error(self):
        data = np.random.rand(10, 10, 10)
        maps = {"Pb": data}
        with pytest.raises(ValueError, match="must be 2D"):
            align_maps(maps)

    def test_non_numpy_array_raises_error(self):
        maps = {"Pb": [[1, 2], [3, 4]]}
        with pytest.raises(ValueError, match="must be a numpy array"):
            align_maps(maps)


class TestValidateAlignment:
    def test_empty_dict_returns_false(self):
        assert validate_alignment({}) is False

    def test_consistent_shapes_returns_true(self):
        maps = {
            "Pb": np.random.rand(10, 10),
            "I": np.random.rand(10, 10),
            "MA": np.random.rand(10, 10),
        }
        assert validate_alignment(maps) is True

    def test_inconsistent_shapes_returns_false(self):
        maps = {
            "Pb": np.random.rand(10, 10),
            "I": np.random.rand(20, 20),
        }
        assert validate_alignment(maps) is False

    def test_nan_tolerance(self):
        data_with_nans = np.random.rand(10, 10)
        data_with_nans[0, 0] = np.nan
        maps = {"Pb": data_with_nans}
        # Default tolerance is 0.0, so this should log a warning but return True
        # (implementation logs warning, doesn't fail on NaN by default)
        assert validate_alignment(maps, tolerance=0.0) is True
        # With very low tolerance, it should still pass if we only log
        assert validate_alignment(maps, tolerance=0.01) is True


class TestCreateAlignedDataset:
    def test_single_sample(self):
        raw_maps = {
            "sample_001": {"Pb": np.random.rand(100, 100), "I": np.random.rand(50, 80)}
        }
        aligned = create_aligned_dataset(
            raw_maps, ["sample_001"], alignment_method="min"
        )
        assert "sample_001" in aligned
        assert aligned["sample_001"]["Pb"].shape == (50, 80)
        assert aligned["sample_001"]["I"].shape == (50, 80)

    def test_multiple_samples(self):
        raw_maps = {
            "sample_001": {"Pb": np.random.rand(100, 100), "I": np.random.rand(50, 80)},
            "sample_002": {"Pb": np.random.rand(80, 80), "I": np.random.rand(40, 60)},
        }
        aligned = create_aligned_dataset(
            raw_maps, ["sample_001", "sample_002"], alignment_method="min"
        )
        # Each sample aligned to its own min
        assert aligned["sample_001"]["Pb"].shape == (50, 80)
        assert aligned["sample_002"]["Pb"].shape == (40, 60)

    def test_global_target_shape(self):
        raw_maps = {
            "sample_001": {"Pb": np.random.rand(100, 100), "I": np.random.rand(50, 80)},
            "sample_002": {"Pb": np.random.rand(80, 80), "I": np.random.rand(40, 60)},
        }
        aligned = create_aligned_dataset(
            raw_maps,
            ["sample_001", "sample_002"],
            target_shape=(30, 40),
        )
        assert aligned["sample_001"]["Pb"].shape == (30, 40)
        assert aligned["sample_002"]["Pb"].shape == (30, 40)

    def test_missing_sample_id(self):
        raw_maps = {
            "sample_001": {"Pb": np.random.rand(100, 100)},
        }
        aligned = create_aligned_dataset(raw_maps, ["sample_001", "missing_sample"])
        assert "sample_001" in aligned
        assert "missing_sample" not in aligned
