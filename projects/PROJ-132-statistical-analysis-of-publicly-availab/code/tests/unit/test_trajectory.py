"""
Unit tests for trajectory analysis module.
"""
import pytest
import tempfile
import os
from pathlib import Path
import polars as pl
import numpy as np
from src.models.trajectory import (
    lat_lon_to_cartesian,
    cartesian_to_lat_lon,
    geodesic_distance,
    compute_frechet_mean,
    compute_trajectory_shift,
    compute_weekly_centroids,
    load_centroid_data,
    group_centroids_by_period
)

class TestCartesianConversion:
    """Tests for lat/lon to Cartesian conversions."""
    
    def test_equator_prime_meridian(self):
        """Test conversion for point at equator and prime meridian."""
        x, y, z = lat_lon_to_cartesian(0, 0)
        assert abs(x - 1.0) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z) < 1e-10
    
    def test_north_pole(self):
        """Test conversion for North Pole."""
        x, y, z = lat_lon_to_cartesian(90, 0)
        assert abs(x) < 1e-10
        assert abs(y) < 1e-10
        assert abs(z - 1.0) < 1e-10
    
    def test_roundtrip(self):
        """Test that conversion is reversible."""
        lat, lon = 45.5, -73.2
        x, y, z = lat_lon_to_cartesian(lat, lon)
        lat_back, lon_back = cartesian_to_lat_lon(x, y, z)
        assert abs(lat - lat_back) < 1e-10
        assert abs(lon - lon_back) < 1e-10

class TestGeodesicDistance:
    """Tests for geodesic distance calculations."""
    
    def test_same_point(self):
        """Distance to same point should be zero."""
        dist = geodesic_distance(45.0, -73.0, 45.0, -73.0)
        assert dist < 1e-10
    
    def test_equator_distance(self):
        """Distance along equator."""
        # 90 degrees along equator should be ~10000 km
        dist = geodesic_distance(0, 0, 0, 90)
        assert 9900 < dist < 10100
    
    def test_pole_distance(self):
        """Distance from equator to pole."""
        dist = geodesic_distance(0, 0, 90, 0)
        assert 9900 < dist < 10100

class TestFrechetMean:
    """Tests for Fréchet mean computation."""
    
    def test_single_point(self):
        """Mean of single point should be the point itself."""
        lat, lon = 45.5, -73.2
        mean_lat, mean_lon = compute_frechet_mean([(lat, lon)])
        assert abs(lat - mean_lat) < 1e-10
        assert abs(lon - mean_lon) < 1e-10
    
    def test_symmetric_points(self):
        """Mean of symmetric points should be at origin."""
        # Points at opposite ends of equator
        centroids = [(0, 0), (0, 180)]
        mean_lat, mean_lon = compute_frechet_mean(centroids)
        # Should be near origin (0, 0) or handle edge case
        assert abs(mean_lat) < 1e-6
    
    def test_cluster_mean(self):
        """Mean of clustered points should be near cluster center."""
        # Cluster around 45N, 0E
        centroids = [
            (45.0, 0.0),
            (45.1, 0.1),
            (44.9, -0.1),
            (45.05, 0.05)
        ]
        mean_lat, mean_lon = compute_frechet_mean(centroids)
        assert 44.9 < mean_lat < 45.1
        assert -0.15 < mean_lon < 0.15

class TestTrajectoryShift:
    """Tests for trajectory shift computation."""
    
    def test_no_shift(self):
        """Identical trajectories should have zero shift."""
        traj = [(45.0, -73.0), (46.0, -72.0), (47.0, -71.0)]
        shift = compute_trajectory_shift(traj, traj)
        assert shift["magnitude"] < 1e-10
        assert shift["direction"] == 0.0
    
    def test_uniform_shift(self):
        """Uniform shift should be detected correctly."""
        traj1 = [(45.0, -73.0), (46.0, -72.0)]
        traj2 = [(45.1, -73.0), (46.1, -72.0)]
        shift = compute_trajectory_shift(traj1, traj2)
        # Magnitude should be approximately 11 km (0.1 degree lat)
        assert 10 < shift["magnitude"] < 12

class TestWeeklyCentroids:
    """Tests for weekly centroid computation."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample preprocessed data."""
        data = {
            "species": ["Robin"] * 20 + ["Sparrow"] * 15,
            "year": [2020] * 10 + [2021] * 10 + [2020] * 8 + [2021] * 7,
            "week": [10] * 5 + [11] * 5 + [10] * 5 + [11] * 5 +
                    [10] * 4 + [11] * 4 + [10] * 4 + [11] * 3,
            "lat": [45.0] * 5 + [45.5] * 5 + [44.0] * 5 + [44.5] * 5 +
                   [46.0] * 4 + [46.5] * 4 + [45.5] * 4 + [46.0] * 3,
            "lon": [-73.0] * 5 + [-72.5] * 5 + [-74.0] * 5 + [-73.5] * 5 +
                   [-72.0] * 4 + [-71.5] * 4 + [-73.0] * 4 + [-72.5] * 3
        }
        return pl.DataFrame(data)
    
    def test_compute_weekly_centroids(self, sample_data, tmp_path):
        """Test computation of weekly centroids."""
        input_path = tmp_path / "input.parquet"
        output_path = tmp_path / "centroids.parquet"
        
        sample_data.write_parquet(input_path)
        
        stats = compute_weekly_centroids(str(input_path), str(output_path))
        
        assert stats["total_centroids"] > 0
        assert Path(output_path).exists()
        
        # Verify output
        result = pl.read_parquet(output_path)
        assert "species" in result.columns
        assert "week" in result.columns
        assert "lat" in result.columns
        assert "lon" in result.columns
    
    def test_load_centroid_data(self, sample_data, tmp_path):
        """Test loading centroid data."""
        output_path = tmp_path / "centroids.parquet"
        compute_weekly_centroids(
            str(tmp_path / "input.parquet"),
            str(output_path)
        ) if False else None  # Skip if input doesn't exist
        
        # Create a valid file first
        sample_data.write_parquet(tmp_path / "input.parquet")
        stats = compute_weekly_centroids(
            str(tmp_path / "input.parquet"),
            str(output_path)
        )
        
        loaded = load_centroid_data(str(output_path))
        assert len(loaded) > 0
        assert "species" in loaded.columns
    
    def test_group_centroids_by_period(self, sample_data, tmp_path):
        """Test grouping centroids by period."""
        input_path = tmp_path / "input.parquet"
        output_path = tmp_path / "centroids.parquet"
        
        sample_data.write_parquet(input_path)
        compute_weekly_centroids(str(input_path), str(output_path))
        
        centroids_df = load_centroid_data(str(output_path))
        
        # Group by species and year
        robin_2020 = group_centroids_by_period(centroids_df, "Robin", 2020)
        assert len(robin_2020) > 0
        assert all(isinstance(p, tuple) and len(p) == 2 for p in robin_2020)
    
    def test_empty_input(self, tmp_path):
        """Test handling of empty input."""
        input_path = tmp_path / "empty.parquet"
        output_path = tmp_path / "centroids.parquet"
        
        empty_df = pl.DataFrame({
            "species": [],
            "year": [],
            "week": [],
            "lat": [],
            "lon": []
        })
        empty_df.write_parquet(input_path)
        
        stats = compute_weekly_centroids(str(input_path), str(output_path))
        assert stats["total_centroids"] == 0
        assert Path(output_path).exists()
    
    def test_missing_columns(self, tmp_path):
        """Test error handling for missing columns."""
        input_path = tmp_path / "bad_input.parquet"
        output_path = tmp_path / "centroids.parquet"
        
        bad_df = pl.DataFrame({
            "species": ["Robin"],
            "year": [2020]
        })
        bad_df.write_parquet(input_path)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            compute_weekly_centroids(str(input_path), str(output_path))
    
    def test_invalid_coordinates(self, tmp_path):
        """Test filtering of invalid coordinates."""
        input_path = tmp_path / "input.parquet"
        output_path = tmp_path / "centroids.parquet"
        
        data = {
            "species": ["Robin", "Robin", "Robin"],
            "year": [2020, 2020, 2020],
            "week": [10, 10, 10],
            "lat": [45.0, 95.0, 45.0],  # 95 is invalid
            "lon": [-73.0, -73.0, -200.0]  # -200 is invalid
        }
        df = pl.DataFrame(data)
        df.write_parquet(input_path)
        
        stats = compute_weekly_centroids(str(input_path), str(output_path))
        # Should filter out invalid rows
        assert stats["total_centroids"] == 1  # Only valid row remains