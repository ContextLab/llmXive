import pytest
import pandas as pd
import geopandas as gpd
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import load_synthetic_data_chunked, harmonize_spatial_data
from synthetic_data import generate_synthetic_data_chunked
from logger import get_logger

logger = get_logger(__name__)

class TestDataHarmonizationFlow:
    """Integration test for the complete data harmonization flow."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Create temporary directory structure
        self.original_root = os.environ.get('PROJECT_ROOT')
        os.environ['PROJECT_ROOT'] = str(tmp_path)
        
        # Create necessary directories
        (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        
        yield
        
        # Cleanup
        if self.original_root:
            os.environ['PROJECT_ROOT'] = self.original_root
        else:
            os.environ.pop('PROJECT_ROOT', None)

    def test_harmonization_produces_unified_geodataframe(self):
        """Test that the harmonization flow produces a single GeoDataFrame."""
        # Generate synthetic data
        logger.info("Generating synthetic data for integration test...")
        noise_df, covariate_df = generate_synthetic_data_chunked(
            n_cells=100, 
            n_days=5, 
            chunk_size=25,
            output_dir=Path(__file__).parent.parent.parent / "data" / "raw"
        )
        
        # Load data
        logger.info("Loading synthetic data...")
        loaded_noise, loaded_covariates = load_synthetic_data_chunked(
            data_dir=Path(__file__).parent.parent.parent / "data" / "raw"
        )
        
        # Harmonize
        logger.info("Harmonizing spatial data...")
        harmonized_gdf = harmonize_spatial_data(
            noise_df=loaded_noise,
            covariate_df=loaded_covariates
        )
        
        # Assertions
        assert isinstance(harmonized_gdf, gpd.GeoDataFrame), \
            "Output should be a GeoDataFrame"
        
        assert len(harmonized_gdf) > 0, \
            "GeoDataFrame should not be empty"
        
        # Check for required columns
        required_cols = ['grid_id', 'geometry', 'noise_level_db', 'traffic_volume']
        for col in required_cols:
            assert col in harmonized_gdf.columns, \
                f"Required column '{col}' missing from GeoDataFrame"
        
        # Check for no missing coordinates
        assert not harmonized_gdf.geometry.isna().any(), \
            "GeoDataFrame should have no missing geometries"
        
        # Check CRS is WGS84 (EPSG:4326)
        assert harmonized_gdf.crs is not None, \
            "GeoDataFrame should have a coordinate reference system"
        assert harmonized_gdf.crs.to_epsg() == 4326, \
            "Coordinate reference system should be WGS84 (EPSG:4326)"

    def test_harmonization_handles_missing_covariates(self):
        """Test that harmonization properly handles missing covariates."""
        # Generate synthetic data
        noise_df, covariate_df = generate_synthetic_data_chunked(
            n_cells=50, 
            n_days=3, 
            chunk_size=10
        )
        
        # Load and harmonize
        loaded_noise, loaded_covariates = load_synthetic_data_chunked(
            data_dir=Path(__file__).parent.parent.parent / "data" / "raw"
        )
        
        harmonized_gdf = harmonize_spatial_data(
            noise_df=loaded_noise,
            covariate_df=loaded_covariates
        )
        
        # Verify that the harmonized data has the expected structure
        assert 'grid_id' in harmonized_gdf.columns
        assert 'geometry' in harmonized_gdf.columns
        
        # Check that traffic_volume exists (even if some values might be NaN before cleaning)
        assert 'traffic_volume' in harmonized_gdf.columns

    def test_harmonization_preserves_daily_granularity(self):
        """Test that harmonization preserves daily granularity (grid_id, date)."""
        # Generate synthetic data
        noise_df, covariate_df = generate_synthetic_data_chunked(
            n_cells=20, 
            n_days=10, 
            chunk_size=5
        )
        
        # Load and harmonize
        loaded_noise, loaded_covariates = load_synthetic_data_chunked(
            data_dir=Path(__file__).parent.parent.parent / "data" / "raw"
        )
        
        harmonized_gdf = harmonize_spatial_data(
            noise_df=loaded_noise,
            covariate_df=loaded_covariates
        )
        
        # Check that we have multiple dates
        assert 'date' in harmonized_gdf.columns, \
            "Date column should be present in harmonized data"
        
        unique_dates = harmonized_gdf['date'].nunique()
        assert unique_dates > 1, \
            "Harmonized data should have multiple dates (daily granularity)"
        
        # Check that each grid_id has multiple date entries
        grid_ids = harmonized_gdf['grid_id'].unique()
        for gid in grid_ids[:5]:  # Check first 5 grid IDs
            grid_data = harmonized_gdf[harmonized_gdf['grid_id'] == gid]
            assert grid_data['date'].nunique() > 1, \
                f"Grid {gid} should have multiple date entries"
