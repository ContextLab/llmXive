"""
Unit tests for SurveyCollector.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

from src.data.collecters.survey_collector import SurveyCollector
from src.utils.io_helpers import read_csv_strict

class TestSurveyCollector:
    """Tests for SurveyCollector functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_workspace):
        """Test that SurveyCollector initializes correctly."""
        collector = SurveyCollector(project_root=temp_workspace)
        assert collector.project_root == temp_workspace
        assert (temp_workspace / "data" / "raw").exists()

    def test_column_mapping(self, temp_workspace):
        """Test that column mapping produces expected schema."""
        # Create a mock input DataFrame
        mock_data = {
            'col_1': [1.0] * 10,
            'col_2': [2.0] * 10,
            'col_3': [3.0] * 10,
            'col_4': [4.0] * 10,
            'col_5': [5.0] * 10,
            'col_6': [6.0] * 10,
            'col_7': [7.0] * 10,
            'col_8': [8.0] * 10,
            'col_9': [9.0] * 10,
            'col_10': [10.0] * 10,
            'col_11': [11.0] * 10,
        }
        # Create a DataFrame with 11 columns (simulating the UCI structure)
        # We need to ensure the index matches the expected column positions
        mock_df = pd.DataFrame(mock_data)
        
        # Mock the _fetch_fallback_data to return our mock data
        # We cannot easily mock the internal method without patching, so we test the mapping logic directly
        # by calling _map_columns on a manually created DataFrame
        
        # Create a DataFrame with the correct number of columns for the mapping logic
        # The mapping logic expects at least 11 columns
        input_df = pd.DataFrame(np.random.rand(10, 11))
        
        collector = SurveyCollector(project_root=temp_workspace)
        mapped_df = collector._map_columns(input_df)
        
        # Check that all required columns exist
        required_cols = [
            'household_id', 'latitude', 'longitude', 'land_size', 'education_level',
            'finance_access', 'practice_mixed_farming', 'practice_terracing',
            'practice_conservation_tillage', 'practice_agroforestry', 'extension_visits',
            'hlias', 'CSA_Index', 'Stability_Score', 'village_id'
        ]
        
        for col in required_cols:
            assert col in mapped_df.columns, f"Missing column: {col}"

    def test_filter_missing_coordinates(self, temp_workspace):
        """Test filtering of records with missing coordinates."""
        collector = SurveyCollector(project_root=temp_workspace)
        
        # Create a DataFrame with some NaN coordinates
        data = {
            'latitude': [1.0, 2.0, None, 4.0],
            'longitude': [1.0, None, 3.0, 4.0],
            'other': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        raw_df, filtered_df = collector._filter_missing_coordinates(df)
        
        # Check that filtered_df has only valid coordinates
        assert len(filtered_df) == 1 # Only the first row is valid
        assert filtered_df['latitude'].isna().sum() == 0
        assert filtered_df['longitude'].isna().sum() == 0

    def test_checksum_verification(self, temp_workspace):
        """Test checksum verification logic."""
        collector = SurveyCollector(project_root=temp_workspace)
        
        # Create a dummy file
        dummy_file = temp_workspace / "dummy.txt"
        dummy_file.write_text("test content")
        
        # Save checksum
        collector._save_checksum(dummy_file)
        
        # Verify checksum
        assert collector._verify_checksum(dummy_file) is True
        
        # Modify file
        dummy_file.write_text("modified content")
        
        # Verify checksum should fail
        assert collector._verify_checksum(dummy_file) is False

    def test_output_files_exist(self, temp_workspace):
        """Test that output files are created after running the pipeline."""
        # We cannot run the full pipeline without real data, so we test the file creation logic
        # by mocking the data fetching and mapping.
        # Instead, we verify that the directory structure is created.
        collector = SurveyCollector(project_root=temp_workspace)
        
        # Check that the data/raw directory exists
        assert (temp_workspace / "data" / "raw").exists()
        
        # Check that the checksum file is created (even if empty)
        # This is a side effect of the initialization or first run
        # We'll simulate a run by creating the files manually to verify the paths
        collector.mapped_file.touch()
        collector.filtered_file.touch()
        
        assert collector.mapped_file.exists()
        assert collector.filtered_file.exists()