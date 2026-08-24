import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingest import validate_schema
from exceptions import DataValidationError

class TestIngestion:
    def test_schema_validation_raises_error_on_missing_column(self):
        """Test that validate_schema raises DataValidationError if a required column is missing."""
        # Create a dataframe with missing required columns
        df = pd.DataFrame({
            'news_exposure_freq': [1, 2, 3],
            'anxiety_score': [10, 20, 30]
            # Missing 'baseline_anxiety', 'age', 'gender'
        })
        
        with pytest.raises(DataValidationError):
            validate_schema(df)

    def test_schema_validation_passes_on_complete_columns(self):
        """Test that validate_schema returns True if all required columns are present."""
        df = pd.DataFrame({
            'news_exposure_freq': [1, 2, 3],
            'anxiety_score': [10, 20, 30],
            'baseline_anxiety': [5, 15, 25],
            'age': [20, 30, 40],
            'gender': ['M', 'F', 'M']
        })
        
        assert validate_schema(df) is True
