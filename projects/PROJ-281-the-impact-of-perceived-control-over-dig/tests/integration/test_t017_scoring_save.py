"""
Integration test for T017: Scoring Saver Pipeline.

This test verifies the end-to-end flow of the scoring saver:
1. Loads preprocessed data (simulated or real if available).
2. Runs the scoring logic (mocked or real depending on environment).
3. Saves the results to data/processed/scoring_results.csv.
4. Validates the output file exists and matches the schema.

Note: This test mocks the heavy model inference to ensure it runs quickly
in CI environments, but validates the file I/O and data flow logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from code.services.scoring_saver import run_scoring_saver_pipeline
from code.services.anxiety_scoring import run_full_scoring_pipeline
from code.config import CONFIG


class TestT017ScoringSaveIntegration:
    """Integration tests for T017."""

    @pytest.fixture
    def mock_preprocessed_data(self, tmp_path):
        """Create a mock preprocessed_text.csv file."""
        data = {
            'post_id': ['1', '2', '3'],
            'text': ['Anxious feeling today.', 'Happy and relaxed.', 'Scared of the future.']
        }
        df = pd.DataFrame(data)
        mock_path = tmp_path / "preprocessed_text.csv"
        df.to_csv(mock_path, index=False)
        return mock_path

    @patch('code.services.anxiety_scoring.load_anxiety_model')
    @patch('code.services.anxiety_scoring.compute_anxiety_scores')
    def test_full_pipeline_execution(self, mock_compute, mock_load_model, tmp_path, monkeypatch):
        """Test that the full scoring saver pipeline runs and produces the output file."""
        
        # Setup mock model
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model

        # Setup mock scoring results (simulating T015 + T016 output)
        # Must include confidence filtering logic simulation
        mock_results = pd.DataFrame({
            'text': ['Anxious feeling today.', 'Happy and relaxed.', 'Scared of the future.'],
            'anxiety_score': [0.85, 0.10, 0.75],
            'confidence_score': [0.92, 0.88, 0.65],  # All >= 0.6
            'post_id': ['1', '2', '3']
        })
        
        # Filter out low confidence in mock to simulate T016
        # In this case, all pass, but we simulate the filtering
        filtered_results = mock_results[mock_results['confidence_score'] >= 0.6].drop(columns=['post_id'])
        
        mock_compute.return_value = filtered_results

        # Patch CONFIG to use tmp_path for processed dir
        original_processed_dir = CONFIG.PROCESSED_DIR
        monkeypatch.setattr(CONFIG, 'PROCESSED_DIR', tmp_path)

        # Act
        output_path = run_scoring_saver_pipeline()

        # Assert
        assert output_path.exists()
        assert output_path.name == "scoring_results.csv"
        
        # Verify content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 3
        assert list(saved_df.columns) == ['text', 'anxiety_score', 'confidence_score']
        
        # Verify specific values
        assert saved_df.loc[0, 'anxiety_score'] == 0.85
        assert saved_df.loc[0, 'confidence_score'] == 0.92

    def test_pipeline_fails_on_empty_scoring_results(self, tmp_path, monkeypatch):
        """Test that pipeline fails gracefully if scoring returns empty data."""
        
        # Patch scoring pipeline to return empty DF
        empty_df = pd.DataFrame(columns=['text', 'anxiety_score', 'confidence_score'])
        
        with patch('code.services.scoring_saver.run_full_scoring_pipeline', return_value=empty_df):
            monkeypatch.setattr(CONFIG, 'PROCESSED_DIR', tmp_path)
            
            with pytest.raises(RuntimeError) as exc_info:
                run_scoring_saver_pipeline()
            
            assert "failed to produce valid data" in str(exc_info.value).lower()