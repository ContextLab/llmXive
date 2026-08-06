"""
Unit tests for the Ingest Pipeline Orchestrator (T015).
"""
import os
import sys
import tempfile
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.data.ingest_pipeline import (
    adjust_batch_size,
    save_predictions_to_csv,
    validate_predictions,
    run_ingest_pipeline
)
from src.models.prediction_result import PredictionResultSchema

class TestAdjustBatchSize:
    def test_reduce_on_high_memory(self):
        # Memory > 85%, should reduce
        new_batch = adjust_batch_size(16, 0.90)
        assert new_batch == 8
    
    def test_increase_on_low_memory(self):
        # Memory < 50%, should increase
        new_batch = adjust_batch_size(4, 0.40)
        assert new_batch == 8
    
    def test_stay_same_on_medium_memory(self):
        # Medium memory, should stay same
        new_batch = adjust_batch_size(8, 0.60)
        assert new_batch == 8
    
    def test_respect_min_batch(self):
        # Should not go below min
        new_batch = adjust_batch_size(1, 0.95)
        assert new_batch == 1
    
    def test_respect_max_batch(self):
        # Should not go above max
        new_batch = adjust_batch_size(64, 0.40)
        assert new_batch == 64

class TestSavePredictions:
    def test_save_to_csv(self, tmp_path):
        output_path = tmp_path / "predictions.csv"
        predictions = [
            {"snippet_id": "1", "predicted_label": "vulnerable", "confidence": 0.9, "is_correct": True},
            {"snippet_id": "2", "predicted_label": "safe", "confidence": 0.8, "is_correct": False}
        ]
        
        save_predictions_to_csv(predictions, output_path)
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert list(df.columns) == ["snippet_id", "predicted_label", "confidence", "is_correct"]

class TestValidatePredictions:
    @pytest.fixture
    def valid_csv(self, tmp_path):
        path = tmp_path / "valid_predictions.csv"
        data = [
            {"snippet_id": "1", "predicted_label": "vulnerable", "confidence": 0.95, "is_correct": True, "inference_time_ms": 100},
            {"snippet_id": "2", "predicted_label": "safe", "confidence": 0.85, "is_correct": False, "inference_time_ms": 120}
        ]
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        return path

    @pytest.fixture
    def invalid_csv(self, tmp_path):
        path = tmp_path / "invalid_predictions.csv"
        # Missing required field 'is_correct'
        data = [
            {"snippet_id": "1", "predicted_label": "vulnerable", "confidence": 0.95, "inference_time_ms": 100}
        ]
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        return path

    def test_validate_valid_csv(self, valid_csv):
        assert validate_predictions(valid_csv) is True

    def test_validate_invalid_csv(self, invalid_csv):
        assert validate_predictions(invalid_csv) is False

    def test_validate_missing_file(self, tmp_path):
        assert validate_predictions(tmp_path / "nonexistent.csv") is False

class TestIngestPipelineOrchestration:
    @patch('src.data.ingest_pipeline.task_download_main')
    @patch('src.data.ingest_pipeline.task_preprocess_main')
    @patch('src.data.ingest_pipeline.task_inference_main')
    @patch('src.data.ingest_pipeline.validate_predictions')
    @patch('src.data.ingest_pipeline.get_data_processed_path')
    @patch('src.data.ingest_pipeline.get_data_results_path')
    @patch('src.data.ingest_pipeline.get_data_logs_path')
    def test_run_pipeline_success(
        self, mock_logs, mock_results, mock_processed, mock_validate, mock_infer, mock_preprocess, mock_download, tmp_path
    ):
        # Setup paths
        mock_processed.return_value = tmp_path / "processed"
        mock_results.return_value = tmp_path / "results"
        mock_logs.return_value = tmp_path / "logs"
        
        # Create necessary directories
        mock_processed.return_value.mkdir(parents=True, exist_ok=True)
        
        # Create a mock predictions file
        preds_path = mock_processed.return_value / "predictions.csv"
        data = [
            {"snippet_id": "1", "predicted_label": "vulnerable", "confidence": 0.95, "is_correct": True, "inference_time_ms": 100}
        ]
        pd.DataFrame(data).to_csv(preds_path, index=False)
        
        mock_validate.return_value = True
        
        success = run_ingest_pipeline()
        
        assert success is True
        mock_download.assert_called_once()
        mock_preprocess.assert_called_once()
        mock_infer.assert_called_once()
        mock_validate.assert_called_once()

    @patch('src.data.ingest_pipeline.task_download_main')
    @patch('src.data.ingest_pipeline.task_preprocess_main')
    @patch('src.data.ingest_pipeline.task_inference_main')
    @patch('src.data.ingest_pipeline.validate_predictions')
    @patch('src.data.ingest_pipeline.get_data_processed_path')
    @patch('src.data.ingest_pipeline.get_data_results_path')
    @patch('src.data.ingest_pipeline.get_data_logs_path')
    def test_run_pipeline_validation_fails(
        self, mock_logs, mock_results, mock_processed, mock_validate, mock_infer, mock_preprocess, mock_download, tmp_path
    ):
        mock_processed.return_value = tmp_path / "processed"
        mock_results.return_value = tmp_path / "results"
        mock_logs.return_value = tmp_path / "logs"
        
        mock_processed.return_value.mkdir(parents=True, exist_ok=True)
        
        preds_path = mock_processed.return_value / "predictions.csv"
        data = [
            {"snippet_id": "1", "predicted_label": "vulnerable", "confidence": 0.95, "is_correct": True, "inference_time_ms": 100}
        ]
        pd.DataFrame(data).to_csv(preds_path, index=False)
        
        mock_validate.return_value = False
        
        success = run_ingest_pipeline()
        
        assert success is False
        mock_validate.assert_called_once()
    
    @patch('src.data.ingest_pipeline.task_download_main')
    @patch('src.data.ingest_pipeline.task_preprocess_main')
    @patch('src.data.ingest_pipeline.task_inference_main')
    @patch('src.data.ingest_pipeline.get_data_processed_path')
    @patch('src.data.ingest_pipeline.get_data_results_path')
    @patch('src.data.ingest_pipeline.get_data_logs_path')
    def test_run_pipeline_inference_missing(
        self, mock_logs, mock_results, mock_processed, mock_infer, mock_preprocess, mock_download, tmp_path
    ):
        mock_processed.return_value = tmp_path / "processed"
        mock_results.return_value = tmp_path / "results"
        mock_logs.return_value = tmp_path / "logs"
        
        mock_processed.return_value.mkdir(parents=True, exist_ok=True)
        
        # Do not create predictions.csv
        
        success = run_ingest_pipeline()
        
        assert success is False
        mock_infer.assert_called_once()
        # validate_predictions should not be called if file is missing
        # (Logic inside run_ingest_pipeline checks existence before calling validate)