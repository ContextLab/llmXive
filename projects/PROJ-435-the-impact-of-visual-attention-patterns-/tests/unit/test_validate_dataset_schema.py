import os
import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validate_dataset_schema import validate_dataset_schema, DataInvalidError

class TestValidateDatasetSchema:
    def test_validate_dataset_schema_valid(self):
        df = pd.DataFrame({
            'headline_text': ['A', 'B'],
            'belief_rating': [1, 2],
            'cognitive_reflection_score': [3, 4],
            'fixation_duration': [5, 6],
            'source_attribution': ['S1', 'S2'],
            'headline_body': ['B1', 'B2']
        })
        
        result = validate_dataset_schema(df, ['headline_text', 'belief_rating'])
        assert result is True

    def test_validate_dataset_schema_missing_columns(self):
        df = pd.DataFrame({
            'headline_text': ['A', 'B'],
            'other_col': [1, 2]
        })
        
        with pytest.raises(DataInvalidError):
            validate_dataset_schema(df, ['headline_text', 'belief_rating'])

    def test_validate_dataset_schema_missing_roi(self):
        df = pd.DataFrame({
            'headline_text': ['A', 'B'],
            'belief_rating': [1, 2],
            'cognitive_reflection_score': [3, 4],
            'fixation_duration': [5, 6]
            # Missing source_attribution, headline_body
        })
        
        with pytest.raises(DataInvalidError):
            validate_dataset_schema(df, ['headline_text', 'belief_rating'], require_roi=True)
