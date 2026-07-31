"""
Unit tests for the scoring_saver module.
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import tempfile
import json

from code.services.scoring_saver import save_scoring_results, run_scoring_saver_pipeline
from code.config import CONFIG


class TestSaveScoringResults:
    """Tests for the save_scoring_results function."""

    def test_save_scoring_results_creates_file(self, tmp_path):
        """Test that the function creates the output file."""
        data = [
            {"text": "Test post 1", "anxiety_score": 0.8, "confidence_score": 0.9},
            {"text": "Test post 2", "anxiety_score": 0.2, "confidence_score": 0.85}
        ]
        output_path = tmp_path / "scoring_results.csv"
        
        result_path = save_scoring_results(data, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert "text" in df.columns
        assert "anxiety_score" in df.columns
        assert "confidence_score" in df.columns
        assert df["text"].iloc[0] == "Test post 1"
        assert df["anxiety_score"].iloc[0] == 0.8

    def test_save_scoring_results_with_post_id(self, tmp_path):
        """Test that post_id is included if present in input."""
        data = [
            {"post_id": "123", "text": "Test post 1", "anxiety_score": 0.8, "confidence_score": 0.9}
        ]
        output_path = tmp_path / "scoring_results.csv"
        
        result_path = save_scoring_results(data, output_path)
        
        df = pd.read_csv(output_path)
        assert "post_id" in df.columns
        assert df["post_id"].iloc[0] == "123"
        # Check order: post_id should be first if present
        assert df.columns.tolist() == ["post_id", "text", "anxiety_score", "confidence_score"]

    def test_save_scoring_results_empty_data_raises_error(self, tmp_path):
        """Test that empty data raises ValueError."""
        output_path = tmp_path / "scoring_results.csv"
        
        with pytest.raises(ValueError, match="Input data is empty"):
            save_scoring_results([], output_path)
        
        with pytest.raises(ValueError, match="Input data is empty"):
            save_scoring_results(None, output_path)

    def test_save_scoring_results_missing_columns_raises_error(self, tmp_path):
        """Test that missing required columns raises ValueError."""
        data = [
            {"text": "Test", "anxiety_score": 0.5} # missing confidence_score
        ]
        output_path = tmp_path / "scoring_results.csv"
        
        with pytest.raises(ValueError, match="Missing required columns"):
            save_scoring_results(data, output_path)

    def test_save_scoring_results_creates_directory(self, tmp_path):
        """Test that the function creates the directory if it doesn't exist."""
        data = [
            {"text": "Test", "anxiety_score": 0.5, "confidence_score": 0.8}
        ]
        output_path = tmp_path / "subdir" / "scoring_results.csv"
        
        result_path = save_scoring_results(data, output_path)
        
        assert result_path.exists()


class TestRunScoringSaverPipeline:
    """Tests for the run_scoring_saver_pipeline function."""

    @patch('code.services.scoring_saver.run_full_scoring_pipeline')
    @patch('code.services.scoring_saver.save_scoring_results')
    def test_run_pipeline_calls_scoring_and_save(self, mock_save, mock_run_scoring, tmp_path):
        """Test that the pipeline calls the scoring function and save function."""
        mock_data = [{"text": "Test", "anxiety_score": 0.5, "confidence_score": 0.8}]
        mock_run_scoring.return_value = mock_data
        mock_save.return_value = tmp_path / "scoring_results.csv"
        
        # Temporarily override CONFIG.PROCESSED_DATA_DIR for the test
        with patch.object(CONFIG, 'PROCESSED_DATA_DIR', tmp_path):
            result = run_scoring_saver_pipeline()
        
        mock_run_scoring.assert_called_once()
        mock_save.assert_called_once()
        assert mock_save.call_args[0][0] == mock_data

    @patch('code.services.scoring_saver.run_full_scoring_pipeline')
    def test_run_pipeline_handles_empty_upstream(self, mock_run_scoring, tmp_path):
        """Test that the pipeline raises an error if upstream returns no data."""
        mock_run_scoring.return_value = []
        
        with patch.object(CONFIG, 'PROCESSED_DATA_DIR', tmp_path):
            with pytest.raises(ValueError, match="Upstream anxiety scoring pipeline returned no data"):
                run_scoring_saver_pipeline()