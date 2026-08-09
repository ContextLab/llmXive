"""Unit tests for data matching logic (T016)."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.data_matching import (
    _normalize_gps,
    _parse_date,
    match_samples_to_disease,
    validate_matches
)


class TestGPSNormalization:
    def test_normalize_valid_coordinates(self):
        lat, lon = _normalize_gps(45.123456, -90.987654)
        assert lat == 45.12
        assert lon == -90.99

    def test_normalize_nan_coordinates(self):
        lat, lon = _normalize_gps(np.nan, -90.0)
        assert pd.isna(lat)
        assert pd.isna(lon)

    def test_normalize_string_coordinates(self):
        lat, lon = _normalize_gps("45.123", "-90.987")
        assert lat == 45.12
        assert lon == -90.99


class TestDateParsing:
    def test_parse_standard_format(self):
        result = _parse_date("2023-05-15")
        assert result == "2023-05-15"

    def test_parse_slash_format(self):
        result = _parse_date("2023/05/15")
        assert result == "2023-05-15"

    def test_parse_invalid_date(self):
        result = _parse_date("not-a-date")
        assert result is None

    def test_parse_nan(self):
        result = _parse_date(np.nan)
        assert result is None


class TestMatchingLogic:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'latitude': [45.123, 45.456, 45.123],
            'longitude': [-90.987, -90.123, -90.987],
            'collection_date': ['2023-05-15', '2023-05-16', '2023-05-15']
        })

    @pytest.fixture
    def disease_df(self):
        return pd.DataFrame({
            'disease_id': ['D1', 'D2'],
            'latitude': [45.12, 45.45],
            'longitude': [-90.99, -90.12],
            'measurement_date': ['2023-05-15', '2023-05-16'],
            'disease_incidence_rate': [0.1, 0.5]
        })

    def test_match_by_location_and_date(self, sample_df, disease_df):
        merged = match_samples_to_disease(sample_df, disease_df)
        # S1 matches D1 (45.12, -90.99, 2023-05-15)
        # S2 matches D2 (45.45, -90.12, 2023-05-16)
        # S3 matches D1 (same coords/date as S1)
        assert len(merged) == 3
        assert 'sample_id' in merged.columns
        assert 'disease_id' in merged.columns

    def test_no_match_if_date_mismatch(self):
        samples = pd.DataFrame({
            'sample_id': ['S1'],
            'latitude': [45.12],
            'longitude': [-90.99],
            'collection_date': ['2023-05-15']
        })
        diseases = pd.DataFrame({
            'disease_id': ['D1'],
            'latitude': [45.12],
            'longitude': [-90.99],
            'measurement_date': ['2023-05-16']
        })
        merged = match_samples_to_disease(samples, diseases)
        assert len(merged) == 0

    def test_no_match_if_location_mismatch(self):
        samples = pd.DataFrame({
            'sample_id': ['S1'],
            'latitude': [45.12],
            'longitude': [-90.99],
            'collection_date': ['2023-05-15']
        })
        diseases = pd.DataFrame({
            'disease_id': ['D1'],
            'latitude': [45.00],
            'longitude': [-90.00],
            'measurement_date': ['2023-05-15']
        })
        merged = match_samples_to_disease(samples, diseases)
        assert len(merged) == 0


class TestValidation:
    def test_validate_complete_data(self):
        df = pd.DataFrame({
            'sample_id': ['S1'],
            'plant_species': ['Corn'],
            'latitude': [45.12],
            'longitude': [-90.99],
            'soil_type': ['Clay'],
            'disease_incidence_rate': [0.5]
        })
        report = validate_matches(df)
        assert report['validation_status'] == 'passed'
        assert report['target_met'] == False # Only 1 sample, target is 30

    def test_validate_missing_field(self):
        df = pd.DataFrame({
            'sample_id': ['S1'],
            'plant_species': ['Corn'],
            'latitude': [45.12],
            'longitude': [-90.99],
            'soil_type': [None], # Missing
            'disease_incidence_rate': [0.5]
        })
        report = validate_matches(df)
        assert report['validation_status'] == 'failed_missing_metadata'
        assert 'soil_type' in report.get('missing_fields', [])