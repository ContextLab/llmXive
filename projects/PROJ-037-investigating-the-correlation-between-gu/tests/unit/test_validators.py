import pytest
import pandas as pd
import numpy as np
from code.utils.validators import validate_schema, validate_non_null, validate_merged_cohort
from code.schemas import get_schema, get_required_columns, get_optional_columns

class TestValidateSchema:
    def test_valid_schema(self):
        """Test that a dataframe matching the schema passes validation."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'shannon': [3.5, 4.1],
            'age': [25, 30],
            'bmi': [22.0, 25.5],
            'sleep_duration': [7.0, 6.5],
            'antibiotic_use': ['No', 'Yes']
        })
        schema = get_schema()
        result = validate_schema(df, schema)
        assert result is True

    def test_invalid_schema_missing_column(self):
        """Test that a dataframe missing a required column fails validation."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'shannon': [3.5, 4.1],
            'age': [25, 30]
        })
        schema = get_schema()
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(df, schema)

    def test_invalid_schema_wrong_type(self):
        """Test that a dataframe with wrong column types fails validation."""
        df = pd.DataFrame({
            'participant_id': [1, 2],  # Should be str
            'shannon': [3.5, 4.1],
            'age': [25, 30],
            'bmi': [22.0, 25.5],
            'sleep_duration': [7.0, 6.5],
            'antibiotic_use': ['No', 'Yes']
        })
        schema = get_schema()
        with pytest.raises(ValueError, match="Column 'participant_id' has incorrect type"):
            validate_schema(df, schema)

class TestValidateNonNull:
    def test_valid_non_null(self):
        """Test that a dataframe with no missing values in required columns passes."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'shannon': [3.5, 4.1],
            'sleep_duration': [7.0, 6.5]
        })
        result = validate_non_null(df)
        assert result is True

    def test_invalid_non_null_missing_value(self):
        """Test that a dataframe with missing values in required columns fails."""
        df = pd.DataFrame({
            'participant_id': ['P1', None],
            'shannon': [3.5, 4.1],
            'sleep_duration': [7.0, 6.5]
        })
        with pytest.raises(ValueError, match="Missing values in required columns"):
            validate_non_null(df)

class TestValidateMergedCohort:
    def test_valid_merged_cohort(self):
        """Test that a valid merged cohort passes all checks."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'shannon': [3.5, 4.1, 3.8],
            'simpson': [0.92, 0.95, 0.90],
            'age': [25, 30, 35],
            'bmi': [22.0, 25.5, 28.0],
            'sleep_duration': [7.0, 6.5, 8.0],
            'sleep_quality': [0.8, 0.6, 0.9],
            'chronotype': ['Morning', 'Evening', 'Morning'],
            'antibiotic_use': ['No', 'Yes', 'No']
        })
        result = validate_merged_cohort(df)
        assert result is True

    def test_invalid_merged_cohort_missing_required(self):
        """Test that a merged cohort missing required columns fails."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'shannon': [3.5, 4.1],
            'age': [25, 30]
        })
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_merged_cohort(df)

    def test_invalid_merged_cohort_wrong_types(self):
        """Test that a merged cohort with wrong column types fails."""
        df = pd.DataFrame({
            'participant_id': [1, 2],  # Should be str
            'shannon': [3.5, 4.1],
            'simpson': [0.92, 0.95],
            'age': [25, 30],
            'bmi': [22.0, 25.5],
            'sleep_duration': [7.0, 6.5],
            'sleep_quality': [0.8, 0.6],
            'chronotype': ['Morning', 'Evening'],
            'antibiotic_use': ['No', 'Yes']
        })
        with pytest.raises(ValueError, match="Column 'participant_id' has incorrect type"):
            validate_merged_cohort(df)

    def test_invalid_merged_cohort_null_values(self):
        """Test that a merged cohort with null values in required columns fails."""
        df = pd.DataFrame({
            'participant_id': ['P1', None],
            'shannon': [3.5, 4.1],
            'simpson': [0.92, 0.95],
            'age': [25, 30],
            'bmi': [22.0, 25.5],
            'sleep_duration': [7.0, 6.5],
            'sleep_quality': [0.8, 0.6],
            'chronotype': ['Morning', 'Evening'],
            'antibiotic_use': ['No', 'Yes']
        })
        with pytest.raises(ValueError, match="Missing values in required columns"):
            validate_merged_cohort(df)