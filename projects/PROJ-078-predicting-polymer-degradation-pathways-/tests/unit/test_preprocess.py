"""Unit tests for preprocessing logic."""
import pytest
from preprocess import filter_missing_environmental_data

class TestMissingDataExclusion:
    def test_missing_env_excludes_record(self, sample_env_data):
        """Test that records with missing environmental data are excluded."""
        # Valid record
        valid_record = {
            "id": 1,
            "smiles": "CC(=O)O",
            "environment": sample_env_data,
            "label": "hydrolysis"
        }

        # Record with missing temperature
        missing_temp = {
            "id": 2,
            "smiles": "CC(=O)O",
            "environment": {**sample_env_data, "temperature": None},
            "label": "hydrolysis"
        }

        # Record with missing pH
        missing_ph = {
            "id": 3,
            "smiles": "CC(=O)O",
            "environment": {**sample_env_data, "ph": None},
            "label": "hydrolysis"
        }

        input_data = [valid_record, missing_temp, missing_ph]

        # Filter
        filtered = filter_missing_environmental_data(input_data)

        # Assert only valid record remains
        assert len(filtered) == 1
        assert filtered[0]["id"] == 1

    def test_all_missing_excludes_all(self, sample_env_data):
        """Test that if all records have missing data, all are excluded."""
        bad_record = {
            "id": 1,
            "smiles": "CC(=O)O",
            "environment": {**sample_env_data, "temperature": None},
            "label": "hydrolysis"
        }
        input_data = [bad_record]

        filtered = filter_missing_environmental_data(input_data)
        assert len(filtered) == 0
