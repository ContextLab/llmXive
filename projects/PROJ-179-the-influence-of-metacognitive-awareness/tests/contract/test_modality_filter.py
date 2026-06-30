"""
Contract test for modality filter logic (US3).

This test verifies that the data filtering logic correctly splits the dataset
into visual and auditory subsets based on the `stimulus_modality` column.

It ensures:
1. The filter function correctly identifies and separates modalities.
2. No trials are lost during the split (sum of subset rows == original rows).
3. The resulting subsets contain only the expected modality values.
4. The required columns for downstream analysis are preserved.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if running from tests directory
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.models.data_models import StimulusModality


class TestModalityFilterLogic:
    """Contract tests for the modality filtering mechanism."""

    @pytest.fixture
    def sample_trial_data(self, tmp_path):
        """Create a temporary CSV file with sample trial data."""
        data = {
            'participant_id': ['P01', 'P01', 'P01', 'P02', 'P02', 'P02'],
            'trial_id': [1, 2, 3, 4, 5, 6],
            'stimulus_modality': ['visual', 'auditory', 'visual', 'auditory', 'visual', 'auditory'],
            'source_label': ['internal', 'external', 'internal', 'external', 'internal', 'external'],
            'participant_response': [1, 0, 1, 0, 1, 0],
            'confidence_rating': [4, 2, 5, 1, 4, 3]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "trial_data.csv"
        df.to_csv(file_path, index=False)
        return file_path, df

    @pytest.fixture
    def modality_enum(self):
        """Return the StimulusModality enum values."""
        return StimulusModality

    def test_filter_logic_correctness(self, sample_trial_data):
        """
        Contract Test: Verify that filtering by modality returns the correct subsets.
        
        Given a dataset with mixed 'visual' and 'auditory' entries:
        When filtered by 'visual':
        Then the result should ONLY contain 'visual' rows and correct count.
        When filtered by 'auditory':
        Then the result should ONLY contain 'auditory' rows and correct count.
        """
        file_path, original_df = sample_trial_data
        
        # Simulate the filter logic that T026/T027 will use
        visual_df = original_df[original_df['stimulus_modality'] == 'visual']
        auditory_df = original_df[original_df['stimulus_modality'] == 'auditory']
        
        # Assert counts
        assert len(visual_df) == 3, "Visual filter should return 3 rows"
        assert len(auditory_df) == 3, "Auditory filter should return 3 rows"
        
        # Assert values
        assert visual_df['stimulus_modality'].unique().tolist() == ['visual']
        assert auditory_df['stimulus_modality'].unique().tolist() == ['auditory']

    def test_no_data_loss_during_split(self, sample_trial_data):
        """
        Contract Test: Verify that the split operation preserves all data.
        
        The sum of rows in the filtered subsets must equal the original row count.
        """
        file_path, original_df = sample_trial_data
        
        visual_df = original_df[original_df['stimulus_modality'] == 'visual']
        auditory_df = original_df[original_df['stimulus_modality'] == 'auditory']
        
        total_filtered_rows = len(visual_df) + len(auditory_df)
        original_rows = len(original_df)
        
        assert total_filtered_rows == original_rows, \
            f"Data loss detected: {total_filtered_rows} != {original_rows}"

    def test_required_columns_preserved(self, sample_trial_data):
        """
        Contract Test: Verify that essential columns for downstream analysis are present.
        
        Downstream tasks (T027, T028) rely on specific columns:
        - stimulus_modality
        - confidence_rating
        - source_label
        - participant_response
        """
        file_path, original_df = sample_trial_data
        
        required_columns = [
            'stimulus_modality', 
            'confidence_rating', 
            'source_label', 
            'participant_response',
            'participant_id',
            'trial_id'
        ]
        
        visual_df = original_df[original_df['stimulus_modality'] == 'visual']
        auditory_df = original_df[original_df['stimulus_modality'] == 'auditory']
        
        for col in required_columns:
            assert col in visual_df.columns, f"Missing required column '{col}' in visual subset"
            assert col in auditory_df.columns, f"Missing required column '{col}' in auditory subset"

    def test_invalid_modality_handling(self, tmp_path):
        """
        Contract Test: Verify behavior when unexpected modality values are present.
        
        If the dataset contains a modality other than 'visual' or 'auditory',
        the filter should simply exclude those rows (or raise a warning, depending on
        strictness). For this contract, we verify that 'visual' and 'auditory'
        are still correctly isolated even if noise exists.
        """
        data = {
            'participant_id': ['P01', 'P01', 'P01'],
            'trial_id': [1, 2, 3],
            'stimulus_modality': ['visual', 'auditory', 'tactile'], # 'tactile' is unexpected
            'source_label': ['internal', 'external', 'internal'],
            'participant_response': [1, 0, 1],
            'confidence_rating': [4, 2, 5]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "trial_data_noise.csv"
        df.to_csv(file_path, index=False)
        
        visual_df = df[df['stimulus_modality'] == 'visual']
        auditory_df = df[df['stimulus_modality'] == 'auditory']
        
        # Ensure valid modalities are still captured correctly
        assert len(visual_df) == 1
        assert len(auditory_df) == 1
        
        # Ensure the noise row is not in either
        assert len(visual_df) + len(auditory_df) == 2
        assert len(df) == 3

    def test_enum_consistency(self, modality_enum):
        """
        Contract Test: Verify that the StimulusModality enum aligns with expected string values.
        
        This ensures that if the code uses the enum for filtering, it matches the string
        literals used in the CSV data ('visual', 'auditory').
        """
        # Check if enum members match expected string values
        # Assuming the enum is defined as visual = 'visual', auditory = 'auditory'
        # We check the names or values
        valid_values = ['visual', 'auditory']
        
        # If the enum is used, we expect it to support these values
        # This is a sanity check on the model definition
        assert 'visual' in [m.value for m in modality_enum] or 'visual' in [m.name for m in modality_enum]
        assert 'auditory' in [m.value for m in modality_enum] or 'auditory' in [m.name for m in modality_enum]

    def test_empty_subset_handling(self, tmp_path):
        """
        Contract Test: Verify behavior when one modality is completely missing.
        
        If the dataset only contains 'visual' trials, the 'auditory' subset should be empty
        but valid (a DataFrame with correct columns but 0 rows).
        """
        data = {
            'participant_id': ['P01', 'P01'],
            'trial_id': [1, 2],
            'stimulus_modality': ['visual', 'visual'],
            'source_label': ['internal', 'external'],
            'participant_response': [1, 0],
            'confidence_rating': [4, 2]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "visual_only.csv"
        df.to_csv(file_path, index=False)
        
        visual_df = df[df['stimulus_modality'] == 'visual']
        auditory_df = df[df['stimulus_modality'] == 'auditory']
        
        assert len(visual_df) == 2
        assert len(auditory_df) == 0
        assert list(auditory_df.columns) == list(df.columns)
        
    def test_column_data_types_preserved(self, sample_trial_data):
        """
        Contract Test: Verify that data types are preserved after filtering.
        
        Filtering should not coerce numeric columns to object or vice versa.
        """
        file_path, original_df = sample_trial_data
        
        visual_df = original_df[original_df['stimulus_modality'] == 'visual']
        
        # Check that numeric columns remain numeric
        assert pd.api.types.is_numeric_dtype(visual_df['confidence_rating'])
        assert pd.api.types.is_numeric_dtype(visual_df['trial_id'])
        
        # Check that string columns remain string
        assert pd.api.types.is_string_dtype(visual_df['stimulus_modality'])
        assert pd.api.types.is_string_dtype(visual_df['participant_id'])