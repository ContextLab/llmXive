"""
Unit tests for spatial join validation logic (T017c).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

from src.data.processing.spatial_join import verify_linkage_and_trigger_aggregation
from src.utils.io_helpers import FatalError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_raw_survey(temp_dir):
    """Create a sample raw survey CSV with valid coordinates."""
    df = pd.DataFrame({
        'household_id': range(1, 101),
        'latitude': np.random.uniform(-30, -20, 100),
        'longitude': np.random.uniform(30, 40, 100),
        'land_size': np.random.uniform(0.5, 5.0, 100)
    })
    # Add a few null coordinates to test filtering
    df.loc[95, 'latitude'] = np.nan
    df.loc[96, 'longitude'] = np.nan
    
    path = temp_dir / "survey_raw.csv"
    df.to_csv(path, index=False)
    return path, 98  # 100 total - 2 nulls


@pytest.fixture
def sample_spatial_joined(temp_dir, matched_count):
    """Create a sample spatial joined CSV."""
    df = pd.DataFrame({
        'household_id': range(1, matched_count + 1),
        'latitude': np.random.uniform(-30, -20, matched_count),
        'longitude': np.random.uniform(30, 40, matched_count),
        'NDVI_mean': np.random.uniform(0.1, 0.8, matched_count)
    })
    path = temp_dir / "spatial_joined_data.csv"
    df.to_csv(path, index=False)
    return path


class TestVerifyLinkageAndTriggerAggregation:
    
    def test_success_high_linkage(self, temp_dir, sample_raw_survey, sample_spatial_joined):
        """Test case where linkage is > 95% and N >= 300 (simulated)."""
        # We need to adjust counts to meet the threshold for this specific test
        # Let's create a scenario with 100 raw valid, 95 matched (95% linkage)
        # But we need N >= 300 for the "success" path in the task description logic?
        # Task says: "If linkage >= 95% and N >= 300, log success"
        # Let's adjust the fixture to have 400 raw, 380 matched.
        
        # Recreate fixtures for this specific test
        raw_df = pd.DataFrame({
            'household_id': range(1, 401),
            'latitude': np.random.uniform(-30, -20, 400),
            'longitude': np.random.uniform(30, 40, 400)
        })
        raw_path = temp_dir / "survey_raw_success.csv"
        raw_df.to_csv(raw_path, index=False)
        
        joined_df = pd.DataFrame({
            'household_id': range(1, 381),
            'latitude': np.random.uniform(-30, -20, 380),
            'longitude': np.random.uniform(30, 40, 380)
        })
        joined_path = temp_dir / "spatial_joined_success.csv"
        joined_df.to_csv(joined_path, index=False)
        
        output_path = temp_dir / "linkage_validation.json"
        
        result = verify_linkage_and_trigger_aggregation(
            spatial_joined_path=str(joined_path),
            raw_survey_path=str(raw_path),
            linkage_output_path=str(output_path),
            min_linkage_pct=0.95,
            min_households=300
        )
        
        assert result['total_valid_households'] == 400
        assert result['matched_households'] == 380
        assert result['linkage_percentage'] == 95.0
        assert result['triggered_aggregation'] is False
        assert result['exclusion_reason'] is None
        
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
            assert 'linkage_percentage' in data
            assert 'total_valid_households' in data

    def test_trigger_low_linkage(self, temp_dir, sample_raw_survey, sample_spatial_joined):
        """Test case where linkage < 95%."""
        # Create 100 raw valid, 50 matched (50% linkage)
        raw_df = pd.DataFrame({
            'household_id': range(1, 101),
            'latitude': np.random.uniform(-30, -20, 100),
            'longitude': np.random.uniform(30, 40, 100)
        })
        raw_path = temp_dir / "survey_raw_low.csv"
        raw_df.to_csv(raw_path, index=False)
        
        joined_df = pd.DataFrame({
            'household_id': range(1, 51),
            'latitude': np.random.uniform(-30, -20, 50),
            'longitude': np.random.uniform(30, 40, 50)
        })
        joined_path = temp_dir / "spatial_joined_low.csv"
        joined_df.to_csv(joined_path, index=False)
        
        output_path = temp_dir / "linkage_validation_low.json"
        
        result = verify_linkage_and_trigger_aggregation(
            spatial_joined_path=str(joined_path),
            raw_survey_path=str(raw_path),
            linkage_output_path=str(output_path),
            min_linkage_pct=0.95,
            min_households=300
        )
        
        assert result['triggered_aggregation'] is True
        assert 'Linkage' in result['exclusion_reason']

    def test_trigger_low_n(self, temp_dir):
        """Test case where N < 300 even if linkage is high."""
        # Create 400 raw valid, 200 matched (50% linkage, low N)
        raw_df = pd.DataFrame({
            'household_id': range(1, 401),
            'latitude': np.random.uniform(-30, -20, 400),
            'longitude': np.random.uniform(30, 40, 400)
        })
        raw_path = temp_dir / "survey_raw_n.csv"
        raw_df.to_csv(raw_path, index=False)
        
        joined_df = pd.DataFrame({
            'household_id': range(1, 201),
            'latitude': np.random.uniform(-30, -20, 200),
            'longitude': np.random.uniform(30, 40, 200)
        })
        joined_path = temp_dir / "spatial_joined_n.csv"
        joined_df.to_csv(joined_path, index=False)
        
        output_path = temp_dir / "linkage_validation_n.json"
        
        result = verify_linkage_and_trigger_aggregation(
            spatial_joined_path=str(joined_path),
            raw_survey_path=str(raw_path),
            linkage_output_path=str(output_path),
            min_linkage_pct=0.95,
            min_households=300
        )
        
        assert result['triggered_aggregation'] is True
        assert 'N=' in result['exclusion_reason']

    def test_fatal_no_households(self, temp_dir):
        """Test case where raw survey has no valid coordinates."""
        raw_df = pd.DataFrame({
            'household_id': range(1, 11),
            'latitude': [np.nan] * 10,
            'longitude': [np.nan] * 10
        })
        raw_path = temp_dir / "survey_raw_empty.csv"
        raw_df.to_csv(raw_path, index=False)
        
        joined_df = pd.DataFrame({
            'household_id': [],
            'latitude': [],
            'longitude': []
        })
        joined_path = temp_dir / "spatial_joined_empty.csv"
        joined_df.to_csv(joined_path, index=False)
        
        output_path = temp_dir / "linkage_validation_empty.json"
        
        with pytest.raises(FatalError, match="FATAL_NO_HOUSEHOLDS"):
            verify_linkage_and_trigger_aggregation(
                spatial_joined_path=str(joined_path),
                raw_survey_path=str(raw_path),
                linkage_output_path=str(output_path),
                min_linkage_pct=0.95,
                min_households=300
            )

    def test_file_not_found(self, temp_dir):
        """Test case where input files are missing."""
        output_path = temp_dir / "linkage_validation_missing.json"
        
        with pytest.raises(FatalError):
            verify_linkage_and_trigger_aggregation(
                spatial_joined_path=str(temp_dir / "nonexistent.csv"),
                raw_survey_path=str(temp_dir / "nonexistent.csv"),
                linkage_output_path=str(output_path),
                min_linkage_pct=0.95,
                min_households=300
            )
