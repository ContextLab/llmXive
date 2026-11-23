import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import DataIngestionPipeline
from exceptions import MissingDataError, DataAcquisitionError
from logger import setup_logging, get_logger

logger = get_logger(__name__)

class TestIngestionValidation:
    """Tests for T018: Validation logic for required variables."""

    def setup_method(self):
        """Set up test fixtures."""
        setup_logging()
        self.sample_data_valid = [
            {"jurisdiction_id": "001", "precinct_votes": 100, "county_total": 105, "state": "CA"},
            {"jurisdiction_id": "002", "precinct_votes": 200, "county_total": 200, "state": "CA"},
            {"jurisdiction_id": "003", "precinct_votes": 150, "county_total": 148, "state": "CA"}
        ]
        
        self.sample_data_missing_precinct = [
            {"jurisdiction_id": "001", "county_total": 105, "state": "CA"},
            {"jurisdiction_id": "002", "county_total": 200, "state": "CA"}
        ]
        
        self.sample_data_missing_county = [
            {"jurisdiction_id": "001", "precinct_votes": 100, "state": "CA"},
            {"jurisdiction_id": "002", "precinct_votes": 200, "state": "CA"}
        ]
        
        self.sample_data_missing_id = [
            {"precinct_votes": 100, "county_total": 105, "state": "CA"},
            {"precinct_votes": 200, "county_total": 200, "state": "CA"}
        ]

    def test_validate_required_fields_present(self):
        """Test that validation passes when all required fields are present."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        # This should not raise
        pipeline._validate_required_fields(self.sample_data_valid)
        assert True

    def test_validate_missing_precinct_votes(self):
        """Test that MissingDataError is raised when precinct_votes is missing."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        with pytest.raises(MissingDataError) as exc_info:
            pipeline._validate_required_fields(self.sample_data_missing_precinct)
        assert "precinct_votes" in str(exc_info.value)

    def test_validate_missing_county_total(self):
        """Test that MissingDataError is raised when county_total is missing."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        with pytest.raises(MissingDataError) as exc_info:
            pipeline._validate_required_fields(self.sample_data_missing_county)
        assert "county_total" in str(exc_info.value)

    def test_validate_missing_jurisdiction_id(self):
        """Test that MissingDataError is raised when jurisdiction_id is missing."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        with pytest.raises(MissingDataError) as exc_info:
            pipeline._validate_required_fields(self.sample_data_missing_id)
        assert "jurisdiction_id" in str(exc_info.value)

    def test_validate_empty_data(self):
        """Test that MissingDataError is raised when data is empty."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        with pytest.raises(MissingDataError) as exc_info:
            pipeline._validate_required_fields([])
        assert "No data provided" in str(exc_info.value)

    def test_normalize_handles_variations(self):
        """Test that normalization handles common column name variations."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        
        # Data with alternative column names
        alt_data = [
            {"id": "001", "votes": 100, "county_reported": 105, "state": "CA"},
            {"id": "002", "total_votes": 200, "official_total": 200, "state": "CA"}
        ]
        
        df = pipeline._normalize_data(alt_data)
        
        # Check that standard columns exist
        assert "precinct_votes" in df.columns
        assert "county_total" in df.columns
        assert "jurisdiction_id" in df.columns
        assert len(df) == 2

    def test_normalize_handles_missing_values(self):
        """Test that missing values are flagged correctly."""
        pipeline = DataIngestionPipeline(source_id="test_source")
        
        data_with_nulls = [
            {"jurisdiction_id": "001", "precinct_votes": 100, "county_total": 105, "state": "CA"},
            {"jurisdiction_id": "002", "precinct_votes": None, "county_total": 200, "state": "CA"},
            {"jurisdiction_id": "003", "precinct_votes": 150, "county_total": None, "state": "CA"}
        ]
        
        df = pipeline._normalize_data(data_with_nulls)
        
        assert "missing_data" in df.columns
        assert df.loc[0, "missing_data"] == False
        assert df.loc[1, "missing_data"] == True
        assert df.loc[2, "missing_data"] == True

    def test_schema_validation_integration(self):
        """Integration test: full pipeline validation flow."""
        # Mock the source verification to avoid file dependencies
        pipeline = DataIngestionPipeline(source_id="test_source")
        
        # Simulate the validation step in run()
        try:
            pipeline._validate_required_fields(self.sample_data_valid)
            pipeline._normalize_data(self.sample_data_valid)
            # If we get here without error, validation passed
            assert True
        except Exception as e:
            pytest.fail(f"Validation failed unexpectedly: {e}")