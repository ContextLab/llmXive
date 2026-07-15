"""
Unit tests for the main orchestrator (T011).
Verifies that the orchestrator correctly routes to synthetic and external flows.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from main import run_full_pipeline, run_synthetic_flow, run_external_flow, ensure_dirs
from pathlib import Path

class TestMainOrchestrator:
    def test_ensure_dirs_creates_directories(self, tmp_path, monkeypatch):
        """Test that ensure_dirs creates the required directory structure."""
        # Mock the Path.mkdir to use tmp_path
        original_mkdir = Path.mkdir
        
        def mock_mkdir(self, parents=True, exist_ok=True):
            if str(self).startswith("data") or str(self) in ["figures", "logs"]:
                # Use tmp_path for testing
                target = tmp_path / self
                target.mkdir(parents=parents, exist_ok=exist_ok)
            else:
                original_mkdir(self, parents=parents, exist_ok=exist_ok)
        
        monkeypatch.setattr(Path, 'mkdir', mock_mkdir)
        
        # Run the function
        ensure_dirs()
        
        # Verify directories were created in tmp_path
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "external").exists()
        assert (tmp_path / "data" / "validation").exists()
        assert (tmp_path / "data" / "models").exists()
        assert (tmp_path / "figures").exists()
        assert (tmp_path / "logs").exists()

    @patch('main.run_synthetic_gen_phase')
    @patch('main.run_preprocess_phase')
    @patch('main.run_train_phase')
    @patch('main.run_evaluation_phase')
    @patch('main.run_shap_phase')
    @patch('main.run_diagnostic_phase')
    def test_run_full_pipeline_synthetic_mode(self, mock_diag, mock_shap, mock_eval, mock_train, mock_pre, mock_syn, tmp_path, monkeypatch):
        """Test that synthetic mode calls the correct phases in order."""
        # Mock ensure_dirs to use tmp_path
        monkeypatch.setattr('main.ensure_dirs', lambda: None)
        
        run_full_pipeline(mode="synthetic")
        
        mock_syn.assert_called_once()
        mock_pre.assert_called_once()
        mock_train.assert_called_once()
        mock_eval.assert_called_once()
        mock_shap.assert_called_once()
        # Diagnostic should be called (logic inside handles R2 check, we just verify it's invoked)
        mock_diag.assert_called_once()

    @patch('main.run_load_external_pipeline')
    @patch('main.validate_consensus')
    @patch('main.retrain_top_features')
    @patch('main.run_preprocess_phase')
    @patch('main.run_train_phase')
    @patch('main.run_evaluation_phase')
    @patch('main.run_shap_analysis_pipeline')
    @patch('main.run_diagnostic_pipeline')
    def test_run_full_pipeline_external_mode(self, mock_diag, mock_shap, mock_eval, mock_train, mock_pre, mock_retrain, mock_consensus, mock_load, tmp_path, monkeypatch):
        """Test that external mode calls load, validation, and training phases."""
        monkeypatch.setattr('main.ensure_dirs', lambda: None)
        
        run_full_pipeline(mode="external")
        
        mock_load.assert_called_once()
        mock_consensus.assert_called_once()
        mock_retrain.assert_called_once()
        mock_pre.assert_called_once()
        mock_train.assert_called_once()
        mock_eval.assert_called_once()
        mock_shap.assert_called_once()
        mock_diag.assert_called_once()

    def test_run_full_pipeline_invalid_mode(self, caplog):
        """Test that invalid mode exits with error."""
        with pytest.raises(SystemExit) as exc_info:
            run_full_pipeline(mode="invalid")
        assert exc_info.value.code == 1
        assert "Unknown mode" in caplog.text

    def test_run_synthetic_flow(self, monkeypatch):
        """Test run_synthetic_flow calls full pipeline with synthetic mode."""
        with patch('main.run_full_pipeline') as mock_full:
            run_synthetic_flow()
            mock_full.assert_called_once_with(mode="synthetic")

    def test_run_external_flow(self, monkeypatch):
        """Test run_external_flow calls full pipeline with external mode."""
        with patch('main.run_full_pipeline') as mock_full:
            run_external_flow()
            mock_full.assert_called_once_with(mode="external")
