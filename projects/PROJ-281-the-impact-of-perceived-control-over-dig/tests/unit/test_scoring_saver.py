"""
Unit tests for the Scoring Saver service (T017).

Verifies that save_scoring_results correctly writes the CSV with the required
columns and handles edge cases (empty data, missing columns).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.services.scoring_saver import save_scoring_results


class TestSaveScoringResults:
    """Tests for the save_scoring_results function."""

    def test_save_valid_data(self, tmp_path):
        """Test saving a valid DataFrame with required columns."""
        # Arrange
        data = {
            'text': ['Sample text 1', 'Sample text 2'],
            'anxiety_score': [0.85, 0.45],
            'confidence_score': [0.92, 0.78]
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "scoring_results.csv"

        # Act
        result_path = save_scoring_results(df, output_path)

        # Assert
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify file contents
        saved_df = pd.read_csv(result_path)
        assert len(saved_df) == 2
        assert list(saved_df.columns) == ['text', 'anxiety_score', 'confidence_score']
        assert saved_df.loc[0, 'anxiety_score'] == 0.85
        assert saved_df.loc[0, 'confidence_score'] == 0.92

    def test_missing_required_columns(self, tmp_path):
        """Test that missing required columns raise ValueError."""
        # Arrange
        data = {
            'text': ['Sample text'],
            'anxiety_score': [0.85]
            # Missing 'confidence_score'
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "scoring_results.csv"

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            save_scoring_results(df, output_path)
        
        assert "missing required columns" in str(exc_info.value).lower()
        assert "confidence_score" in str(exc_info.value)

    def test_empty_dataframe(self, tmp_path):
        """Test that an empty DataFrame raises FileNotFoundError."""
        # Arrange
        data = {
            'text': [],
            'anxiety_score': [],
            'confidence_score': []
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "scoring_results.csv"

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            save_scoring_results(df, output_path)
        
        assert "no data to save" in str(exc_info.value).lower()

    def test_null_values_handling(self, tmp_path):
        """Test that rows with null scores are dropped before saving."""
        # Arrange
        data = {
            'text': ['Valid', 'Null Score', 'Valid 2'],
            'anxiety_score': [0.85, np.nan, 0.50],
            'confidence_score': [0.90, 0.80, np.nan]
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "scoring_results.csv"

        # Act
        result_path = save_scoring_results(df, output_path)

        # Assert
        saved_df = pd.read_csv(result_path)
        # Only the first row should remain (both scores valid)
        assert len(saved_df) == 1
        assert saved_df.loc[0, 'text'] == 'Valid'

    def test_column_order(self, tmp_path):
        """Test that columns are saved in the specific order: text, anxiety_score, confidence_score."""
        # Arrange
        # Create df with different column order
        data = {
            'confidence_score': [0.90],
            'text': ['Test'],
            'anxiety_score': [0.85]
        }
        df = pd.DataFrame(data)
        output_path = tmp_path / "scoring_results.csv"

        # Act
        save_scoring_results(df, output_path)

        # Assert
        # Read the raw CSV to check header order
        with open(output_path, 'r') as f:
            header = f.readline().strip()
        
        assert header == "text,anxiety_score,confidence_score"
