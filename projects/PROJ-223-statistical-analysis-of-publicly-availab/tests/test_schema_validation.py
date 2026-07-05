"""
Tests for schema validation helpers.
"""
import pytest
import pandas as pd
import numpy as np
from code.schema_validation import (
    validate_raw_fars,
    validate_raw_noaa,
    validate_merged_dataset,
    validate_schema,
    get_missing_columns,
    get_null_counts,
    SchemaValidationError
)

class TestValidateRawFars:
    def test_valid_fars_data(self):
        """Test validation passes for valid FARS data."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        is_valid, errors = validate_raw_fars(df)
        assert is_valid
        assert len(errors) == 0

    def test_missing_columns(self):
        """Test validation fails when columns are missing."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022]
        })
        
        is_valid, errors = validate_raw_fars(df)
        assert not is_valid
        assert any("Missing required columns" in error for error in errors)

    def test_null_required_columns(self):
        """Test validation fails when required columns have nulls."""
        df = pd.DataFrame({
            "CASEID": [1, None, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        is_valid, errors = validate_raw_fars(df)
        assert not is_valid
        assert any("CASEID" in error and "null" in error for error in errors)

    def test_invalid_severity_range(self):
        """Test validation catches severity outside expected range."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 5],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        is_valid, errors = validate_raw_fars(df)
        assert not is_valid
        assert any("SEVERITY" in error and "range" in error for error in errors)

class TestValidateRawNoaa:
    def test_valid_noaa_data(self):
        """Test validation passes for valid NOAA data."""
        df = pd.DataFrame({
            "STATION": ["US1", "US2", "US3"],
            "DATE": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "TOBS": [10.0, 11.0, 12.0],
            "PRCP": [0.0, 0.1, 0.2],
            "SNOW": [0, 0, 0],
            "SNWD": [0, 0, 0],
            "WESF": [0, 0, 0],
            "WESD": [0, 0, 0],
            "TMAX": [15.0, 16.0, 17.0],
            "TMIN": [5.0, 6.0, 7.0]
        })
        
        is_valid, errors = validate_raw_noaa(df)
        assert is_valid
        assert len(errors) == 0

    def test_missing_columns(self):
        """Test validation fails when columns are missing."""
        df = pd.DataFrame({
            "STATION": ["US1", "US2", "US3"],
            "DATE": ["2020-01-01", "2020-01-02", "2020-01-03"]
        })
        
        is_valid, errors = validate_raw_noaa(df)
        assert not is_valid
        assert any("Missing required columns" in error for error in errors)

    def test_invalid_date_format(self):
        """Test validation fails for invalid date format."""
        df = pd.DataFrame({
            "STATION": ["US1", "US2", "US3"],
            "DATE": ["invalid", "2020-01-02", "2020-01-03"],
            "TOBS": [10.0, 11.0, 12.0],
            "PRCP": [0.0, 0.1, 0.2],
            "SNOW": [0, 0, 0],
            "SNWD": [0, 0, 0],
            "WESF": [0, 0, 0],
            "WESD": [0, 0, 0],
            "TMAX": [15.0, 16.0, 17.0],
            "TMIN": [5.0, 6.0, 7.0]
        })
        
        is_valid, errors = validate_raw_noaa(df)
        assert not is_valid
        assert any("DATE" in error and "invalid" in error for error in errors)

class TestValidateMergedDataset:
    def test_valid_merged_data(self):
        """Test validation passes for valid merged data."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "STATION": ["US1", "US2", "US3"],
            "DATE": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "TOBS": [10.0, 11.0, 12.0],
            "PRCP": [0.0, 0.1, 0.2],
            "SNOW": [0, 0, 0],
            "SNWD": [0, 0, 0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        is_valid, errors = validate_merged_dataset(df)
        assert is_valid
        assert len(errors) == 0

    def test_duplicate_caseids(self):
        """Test validation fails for duplicate CASEIDs."""
        df = pd.DataFrame({
            "CASEID": [1, 1, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "STATION": ["US1", "US2", "US3"],
            "DATE": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "TOBS": [10.0, 11.0, 12.0],
            "PRCP": [0.0, 0.1, 0.2],
            "SNOW": [0, 0, 0],
            "SNWD": [0, 0, 0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        is_valid, errors = validate_merged_dataset(df)
        assert not is_valid
        assert any("duplicate" in error for error in errors)

    def test_invalid_latitude_range(self):
        """Test validation fails for invalid latitude range."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 95.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "STATION": ["US1", "US2", "US3"],
            "DATE": ["2020-01-01", "2020-01-02", "2020-01-03"],
            "TOBS": [10.0, 11.0, 12.0],
            "PRCP": [0.0, 0.1, 0.2],
            "SNOW": [0, 0, 0],
            "SNWD": [0, 0, 0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        is_valid, errors = validate_merged_dataset(df)
        assert not is_valid
        assert any("LATITUDE" in error and "range" in error for error in errors)

class TestValidateSchema:
    def test_validate_schema_fars_raw(self):
        """Test validate_schema function for FARS raw data."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        assert validate_schema(df, "fars_raw") is True

    def test_validate_schema_invalid(self):
        """Test validate_schema raises exception for invalid data."""
        df = pd.DataFrame({
            "CASEID": [1, None, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        with pytest.raises(SchemaValidationError):
            validate_schema(df, "fars_raw")

class TestGetMissingColumns:
    def test_get_missing_columns_fars(self):
        """Test get_missing_columns for FARS data."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3]
        })
        
        missing = get_missing_columns(df, "fars_raw")
        assert "YEAR" in missing
        assert "SEVERITY" in missing

    def test_get_missing_columns_no_columns(self):
        """Test get_missing_columns returns empty list when all columns present."""
        df = pd.DataFrame({
            "CASEID": [1, 2, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        missing = get_missing_columns(df, "fars_raw")
        assert len(missing) == 0

class TestGetNullCounts:
    def test_get_null_counts(self):
        """Test get_null_counts returns correct null counts."""
        df = pd.DataFrame({
            "CASEID": [1, None, 3],
            "STATE": [1, 2, 3],
            "YEAR": [2020, 2021, 2022],
            "MONTH": [1, 2, 3],
            "DAY": [1, 2, 3],
            "HOUR": [12, 13, 14],
            "SEVERITY": [0, 1, 2],
            "LATITUDE": [34.0, 35.0, 36.0],
            "LONGITUDE": [-118.0, -119.0, -120.0],
            "WEATHER_CONDITION": [1, 2, 3],
            "LIGHT_CONDITION": [1, 2, 3],
            "ROADWAY_SURFACE": [1, 2, 3],
            "VEHICLE_COUNT": [1, 2, 3],
            "PERSON_COUNT": [1, 2, 3],
            "FATALITY_COUNT": [0, 1, 2],
            "INJURY_COUNT": [1, 2, 3]
        })
        
        null_counts = get_null_counts(df, "fars_raw")
        assert null_counts["CASEID"] == 1
        assert null_counts["STATE"] == 0
        assert null_counts["YEAR"] == 0
