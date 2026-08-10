import pytest
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
from geopandas import GeoDataFrame
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import SpatialWeightMatrixError, build_spatial_weights

class TestSpatialWeightMatrixFailureHandling:
    """
    Tests for T025: Weight matrix failure handling.
    Verifies that if both Queen and KNN fail, a SpatialWeightMatrixError is raised.
    """

    def test_queen_fails_knn_succeeds(self):
        """
        Test that if Queen fails but KNN succeeds, KNN is returned.
        """
        # Create a valid GeoDataFrame
        data = {
            'geometry': [Point(0, 0), Point(1, 0), Point(0, 1), Point(1, 1)] * 100, # Enough points for KNN
            'val': [1] * 400
        }
        gdf = GeoDataFrame(data, crs="EPSG:4326")

        # Mock Queen.from_dataframe to raise an exception
        with patch('libpysal.weights.Queen.from_dataframe', side_effect=Exception("Queen failed")):
            # Mock KNN.from_dataframe to succeed
            with patch('libpysal.weights.KNN.from_dataframe', return_value=MagicMock(n=400, n_links=100, mean_neighbors=MagicMock(return_value=2.5), n_components=1)) as mock_knn:
                w = build_spatial_weights(gdf)
                
                # Verify KNN was called
                assert mock_knn.called
                assert isinstance(w, MagicMock) # Or check specific mock attributes

    def test_queen_fails_knn_fails_raises_error(self):
        """
        Test that if BOTH Queen and KNN fail, SpatialWeightMatrixError is raised.
        """
        # Create a valid GeoDataFrame (geometry is valid, but we mock the failure)
        data = {
            'geometry': [Point(0, 0), Point(1, 0)],
            'val': [1, 2]
        }
        gdf = GeoDataFrame(data, crs="EPSG:4326")

        # Mock both to fail
        with patch('libpysal.weights.Queen.from_dataframe', side_effect=Exception("Queen failed")):
            with patch('libpysal.weights.KNN.from_dataframe', side_effect=Exception("KNN failed")):
                with pytest.raises(SpatialWeightMatrixError) as excinfo:
                    build_spatial_weights(gdf)
                
                assert "Both Queen and KNN failed" in str(excinfo.value)

    def test_insufficient_points_for_knn(self):
        """
        Test that KNN fails gracefully if not enough points, and triggers the error if Queen also fails.
        """
        # Create a GeoDataFrame with only 2 points (insufficient for K=8)
        data = {
            'geometry': [Point(0, 0), Point(1, 0)],
            'val': [1, 2]
        }
        gdf = GeoDataFrame(data, crs="EPSG:4326")

        # Mock Queen to fail
        with patch('libpysal.weights.Queen.from_dataframe', side_effect=Exception("Queen failed")):
            # KNN should fail due to insufficient points (handled in code or libpysal)
            # We expect the code to catch this and raise our custom error
            with pytest.raises(SpatialWeightMatrixError) as excinfo:
                build_spatial_weights(gdf)
            
            assert "Both Queen and KNN failed" in str(excinfo.value)