import pytest
import pandas as pd
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.ingest import load_mfq_data, load_stories_data, merge_datasets, validate_and_save, main
from data.ingest_real import DataFetchError

class TestIngestIntegration:
    """
    Integration tests for the ingest.py module.
    Tests the routing logic, merging, and validation.
    """

    def test_merge_datasets_handles_missing_ids(self):
        """
        Test that merge_datasets correctly handles ID mismatches
        and logs exclusions (verified by return row count).
        """
        # Create mock data with mismatched IDs
        mfq_df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'harm': [1.0, 2.0, 3.0]
        })
        
        stories_df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P4'], # P3 missing, P4 extra
            'story_id': ['S1', 'S2', 'S3'],
            'text': ['Story 1', 'Story 2', 'Story 3']
        })
        
        vr_logs_df = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'story_id': ['S1', 'S2'],
            'judgment_rating': [5, 4]
        })
        
        # P3 is in MFQ but not Stories -> Excluded
        # P4 is in Stories but not MFQ -> Excluded
        # P1, P2 are in all -> Included
        
        result = merge_datasets(mfq_df, stories_df, vr_logs_df)
        
        assert len(result) == 2, "Expected 2 rows after merging (P1, P2)"
        assert list(result['participant_id']) == ['P1', 'P2']

    @patch('data.ingest.generate_synthetic_mfq')
    @patch('data.ingest.generate_moral_stories_dataset')
    @patch('data.ingest.generate_vr_logs_dataset')
    def test_simulation_mode_routing(self, mock_vr, mock_stories, mock_mfq):
        """
        Test that when DATA_MODE is 'simulation', synthetic generators are called.
        """
        mock_mfq.return_value = pd.DataFrame({'participant_id': ['P1'], 'harm': [1.0]})
        mock_stories.return_value = pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'text': ['T1']})
        mock_vr.return_value = pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'judgment_rating': [5]})
        
        with patch.dict(os.environ, {'DATA_MODE': 'simulation'}):
            # These functions internally check env var, but for this test we verify
            # the logic path by mocking the generators and ensuring they are called.
            # Note: The actual check happens inside load_mfq_data etc.
            # We need to ensure the environment variable is set before calling.
            mfq = load_mfq_data()
            stories, vr = load_stories_data()
            
            mock_mfq.assert_called_once()
            mock_stories.assert_called_once()
            mock_vr.assert_called_once()

    @patch('data.ingest.fetch_from_osf')
    @patch('data.ingest.fetch_from_huggingface')
    def test_real_mode_routing(self, mock_hf, mock_osf):
        """
        Test that when DATA_MODE is 'real', real fetchers are called.
        """
        mock_osf.return_value = pd.DataFrame({'participant_id': ['P1'], 'harm': [1.0]})
        mock_hf.side_effect = [
            pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'text': ['T1']}),
            pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'judgment_rating': [5]})
        ]
        
        with patch.dict(os.environ, {'DATA_MODE': 'real'}):
            mfq = load_mfq_data()
            stories, vr = load_stories_data()
            
            mock_osf.assert_called_once_with("mfq")
            # fetch_from_huggingface is called twice (once for stories, once for vr_logs)
            assert mock_hf.call_count == 2

    def test_real_mode_raises_on_fetch_failure(self):
        """
        Test that real mode raises DataFetchError if fetch fails.
        """
        with patch.dict(os.environ, {'DATA_MODE': 'real'}):
            with patch('data.ingest.fetch_from_osf', side_effect=DataFetchError("Network error")):
                with pytest.raises(DataFetchError):
                    load_mfq_data()

    def test_merge_invalidates_missing_columns(self):
        """
        Test that merge_datasets raises ValueError if required columns are missing.
        """
        mfq_df = pd.DataFrame({'wrong_col': [1]})
        stories_df = pd.DataFrame({'participant_id': [1], 'story_id': [1], 'text': ['t']})
        vr_logs_df = pd.DataFrame({'participant_id': [1], 'story_id': [1], 'judgment_rating': [1]})
        
        with pytest.raises(ValueError, match="MFQ data missing required column"):
            merge_datasets(mfq_df, stories_df, vr_logs_df)

    @patch('data.ingest.merge_datasets')
    @patch('data.ingest.load_mfq_data')
    @patch('data.ingest.load_stories_data')
    def test_main_pipeline_execution(self, mock_load_stories, mock_load_mfq, mock_merge):
        """
        Test the full main() pipeline execution flow.
        """
        mock_load_mfq.return_value = pd.DataFrame({'participant_id': ['P1'], 'harm': [1.0]})
        mock_load_stories.return_value = (
            pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'text': ['T1']}),
            pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'judgment_rating': [5]})
        )
        mock_merge.return_value = pd.DataFrame({'participant_id': ['P1'], 'story_id': ['S1'], 'harm': [1.0], 'text': ['T1'], 'judgment_rating': [5]})
        
        with patch.dict(os.environ, {'DATA_MODE': 'simulation'}):
            # Mock validate_and_save to return a path
            with patch('data.ingest.validate_and_save', return_value="data/processed/test.csv") as mock_save:
                result = main()
                
                assert result == "data/processed/test.csv"
                mock_save.assert_called_once()
    
    def test_main_raises_on_invalid_mode(self):
        """
        Test that main() raises ValueError if DATA_MODE is invalid.
        """
        with patch.dict(os.environ, {'DATA_MODE': 'invalid_mode'}):
            with pytest.raises(ValueError, match="Invalid DATA_MODE"):
                main()
