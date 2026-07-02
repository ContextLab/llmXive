"""
Unit tests for T044: Save feature importance CSV and top 5 correlation plots.

These tests verify that the output files are created correctly and contain valid data.
"""
import os
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the functions to test
from save_analysis_outputs import (
    save_feature_importance_csv,
    generate_and_save_top5_plot,
    ensure_output_dir,
    main
)

class TestEnsureOutputDir:
    def test_creates_directory(self, tmp_path):
        """Test that the output directory is created."""
        test_dir = tmp_path / "test_output"
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            ensure_output_dir()
            assert test_dir.exists()
            assert test_dir.is_dir()

class TestSaveFeatureImportanceCsv:
    def test_saves_valid_dataframe(self, tmp_path):
        """Test saving a valid feature importance DataFrame."""
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()
        
        # Create a mock DataFrame
        df = pd.DataFrame({
            'feature': ['feat1', 'feat2', 'feat3'],
            'importance': [0.5, 0.3, 0.2]
        })
        
        csv_path = test_dir / "feature_importance.csv"
        
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            with patch('save_analysis_outputs.FEATURE_IMPORTANCE_CSV', str(csv_path)):
                result = save_feature_importance_csv(df)
                
                assert result is True
                assert csv_path.exists()
                
                # Verify the saved content
                saved_df = pd.read_csv(csv_path)
                assert len(saved_df) == 3
                assert 'feature' in saved_df.columns
                assert 'importance' in saved_df.columns
                # Check sorting (should be descending by importance)
                assert saved_df.iloc[0]['importance'] >= saved_df.iloc[1]['importance']

    def test_returns_false_on_empty_dataframe(self, tmp_path):
        """Test that function returns False for empty DataFrame."""
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()
        
        df = pd.DataFrame()
        
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            result = save_feature_importance_csv(df)
            assert result is False

    def test_returns_false_on_missing_columns(self, tmp_path):
        """Test that function returns False when required columns are missing."""
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()
        
        df = pd.DataFrame({
            'feature': ['feat1', 'feat2'],
            'other_col': [0.5, 0.3]
        })
        
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            result = save_feature_importance_csv(df)
            assert result is False

class TestGenerateAndSaveTop5Plot:
    def test_generates_plot(self, tmp_path):
        """Test that the function generates and saves a plot."""
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()
        
        # Create mock DataFrames
        correlation_df = pd.DataFrame({
            'feature': ['feat1', 'feat2', 'feat3'],
            'correlation': [0.8, 0.6, 0.4],
            'p_value': [0.01, 0.05, 0.1]
        })
        
        importance_df = pd.DataFrame({
            'feature': ['feat1', 'feat2', 'feat3'],
            'importance': [0.5, 0.3, 0.2]
        })
        
        data_df = pd.DataFrame({
            'feat1': np.random.randn(100),
            'feat2': np.random.randn(100),
            'feat3': np.random.randn(100),
            'log_conductivity': np.random.randn(100)
        })
        
        png_path = test_dir / "corr_plot_top5.png"
        
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            with patch('save_analysis_outputs.CORR_PLOT_PNG', str(png_path)):
                result = generate_and_save_top5_plot(correlation_df, importance_df, data_df)
                
                assert result is True
                assert png_path.exists()
                assert png_path.stat().st_size > 0  # File should have content

    def test_returns_false_on_empty_correlation_df(self, tmp_path):
        """Test that function returns False for empty correlation DataFrame."""
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()
        
        correlation_df = pd.DataFrame()
        importance_df = pd.DataFrame({'feature': ['feat1'], 'importance': [0.5]})
        data_df = pd.DataFrame({'feat1': [1, 2, 3], 'log_conductivity': [1, 2, 3]})
        
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            result = generate_and_save_top5_plot(correlation_df, importance_df, data_df)
            assert result is False

    def test_returns_false_on_empty_importance_df(self, tmp_path):
        """Test that function returns False for empty feature importance DataFrame."""
        test_dir = tmp_path / "test_output"
        test_dir.mkdir()
        
        correlation_df = pd.DataFrame({'feature': ['feat1'], 'correlation': [0.8], 'p_value': [0.01]})
        importance_df = pd.DataFrame()
        data_df = pd.DataFrame({'feat1': [1, 2, 3], 'log_conductivity': [1, 2, 3]})
        
        with patch('save_analysis_outputs.OUTPUT_DIR', str(test_dir)):
            result = generate_and_save_top5_plot(correlation_df, importance_df, data_df)
            assert result is False

class TestMain:
    @pytest.mark.skip(reason="Requires full pipeline setup with real data")
    def test_main_execution(self):
        """Test the main function execution (requires real data)."""
        # This test is skipped because it requires the full pipeline to be set up
        # with real data files in the expected locations.
        pass