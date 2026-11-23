"""
Unit tests for data schema validation.

This module validates the structure and types of survey response data,
ensuring compliance with the project's data model requirements.

Tests validate the schema for:
- participant_id (string/integer, non-empty)
- image_id (string, non-empty)
- salience (string, one of: 'low', 'medium', 'high')
- rating (integer, range 1-7)
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import Response, SalienceLevel
from config import seed_everything


# Fix seed for reproducibility
seed_everything(42)


class TestDataSchemaValidation:
    """Test suite for validating survey response data schema."""

    def test_valid_schema_basic(self):
        """Test that a valid schema passes validation."""
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'image_id': ['img_001', 'img_002'],
            'salience': ['low', 'high'],
            'rating': [3, 5]
        })
        
        # Should not raise
        validate_survey_schema(df)

    def test_missing_column(self):
        """Test that missing required columns raise ValueError."""
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'image_id': ['img_001'],
            'rating': [3]
            # Missing 'salience'
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'salience' in str(exc_info.value).lower()

    def test_extra_column(self):
        """Test that extra columns are allowed (future-proofing)."""
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'image_id': ['img_001'],
            'salience': ['low'],
            'rating': [3],
            'timestamp': ['2023-01-01']  # Extra column
        })
        
        # Should not raise - extra columns are allowed
        validate_survey_schema(df)

    def test_invalid_salience_value(self):
        """Test that invalid salience values raise ValueError."""
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'image_id': ['img_001'],
            'salience': ['invalid_level'],
            'rating': [3]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'salience' in str(exc_info.value).lower()
        assert 'invalid_level' in str(exc_info.value)

    def test_rating_out_of_range(self):
        """Test that ratings outside 1-7 raise ValueError."""
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'image_id': ['img_001'],
            'salience': ['low'],
            'rating': [0]  # Out of range
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'rating' in str(exc_info.value).lower()
        assert '0' in str(exc_info.value)

    def test_rating_float(self):
        """Test that float ratings are rejected."""
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'image_id': ['img_001'],
            'salience': ['low'],
            'rating': [3.5]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'rating' in str(exc_info.value).lower()

    def test_empty_string_id(self):
        """Test that empty string IDs raise ValueError."""
        df = pd.DataFrame({
            'participant_id': [''],
            'image_id': ['img_001'],
            'salience': ['low'],
            'rating': [3]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'participant_id' in str(exc_info.value).lower()

    def test_null_values(self):
        """Test that null values raise ValueError."""
        df = pd.DataFrame({
            'participant_id': [None],
            'image_id': ['img_001'],
            'salience': ['low'],
            'rating': [3]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'participant_id' in str(exc_info.value).lower()

    def test_all_valid_salience_levels(self):
        """Test that all valid salience levels are accepted."""
        for level in ['low', 'medium', 'high']:
            df = pd.DataFrame({
                'participant_id': ['P001'],
                'image_id': ['img_001'],
                'salience': [level],
                'rating': [3]
            })
            validate_survey_schema(df)  # Should not raise

    def test_boundary_ratings(self):
        """Test that boundary ratings (1 and 7) are accepted."""
        for rating in [1, 7]:
            df = pd.DataFrame({
                'participant_id': ['P001'],
                'image_id': ['img_001'],
                'salience': ['low'],
                'rating': [rating]
            })
            validate_survey_schema(df)  # Should not raise

    def test_integer_type_for_rating(self):
        """Test that integer type is enforced for rating."""
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'image_id': ['img_001'],
            'salience': ['low'],
            'rating': [3]  # Integer
        })
        
        # Convert to float explicitly
        df['rating'] = df['rating'].astype(float)
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'rating' in str(exc_info.value).lower()

    def test_empty_dataframe(self):
        """Test that an empty dataframe raises ValueError."""
        df = pd.DataFrame(columns=['participant_id', 'image_id', 'salience', 'rating'])
        
        with pytest.raises(ValueError) as exc_info:
            validate_survey_schema(df)
        
        assert 'empty' in str(exc_info.value).lower()

    def test_large_dataset(self):
        """Test schema validation on a larger dataset."""
        n = 1000
        df = pd.DataFrame({
            'participant_id': [f'P{i:03d}' for i in range(n)],
            'image_id': [f'img_{i:03d}' for i in range(n)],
            'salience': np.random.choice(['low', 'medium', 'high'], n),
            'rating': np.random.randint(1, 8, n)
        })
        
        validate_survey_schema(df)  # Should not raise

    def test_schema_matches_model(self):
        """Verify schema matches the Response model definition."""
        # Create a valid response using the model
        response = Response(
            id='R001',
            participant_id='P001',
            stimulus_id='img_001',
            rating=5,
            timestamp='2023-01-01T00:00:00'
        )
        
        # Convert to dataframe format
        df = pd.DataFrame([{
            'participant_id': response.participant_id,
            'image_id': response.stimulus_id,
            'salience': 'low',  # Not in model but required in survey data
            'rating': response.rating
        }])
        
        validate_survey_schema(df)  # Should not raise


def validate_survey_schema(df: pd.DataFrame) -> None:
    """
    Validate survey response data schema.
    
    Args:
        df: DataFrame containing survey responses
    
    Raises:
        ValueError: If schema validation fails
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    required_columns = ['participant_id', 'image_id', 'salience', 'rating']
    
    # Check for required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check for empty/null values in required columns
    for col in required_columns:
        if df[col].isnull().any():
            raise ValueError(f"Column '{col}' contains null values")
        if df[col].astype(str).str.strip().eq('').any():
            raise ValueError(f"Column '{col}' contains empty strings")
    
    # Validate salience values
    valid_salience = {'low', 'medium', 'high'}
    invalid_salience = set(df['salience'].unique()) - valid_salience
    if invalid_salience:
        raise ValueError(f"Invalid salience values: {invalid_salience}")
    
    # Validate rating range and type
    if not pd.api.types.is_integer_dtype(df['rating']):
        raise ValueError(f"Column 'rating' must be integer type, got {df['rating'].dtype}")
    
    if df['rating'].min() < 1 or df['rating'].max() > 7:
        raise ValueError(f"Rating values must be between 1 and 7, got range [{df['rating'].min()}, {df['rating'].max()}]")

    # Validate participant_id and image_id are strings
    if not pd.api.types.is_string_dtype(df['participant_id']):
        raise ValueError(f"Column 'participant_id' must be string type")
    
    if not pd.api.types.is_string_dtype(df['image_id']):
        raise ValueError(f"Column 'image_id' must be string type")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])