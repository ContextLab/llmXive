import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from src.orchestration.orchestrator import run_orchestration, validate_predictions_schema

class TestOrchestrator:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure simulating the project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create required dirs
            (root / "data" / "logs").mkdir(parents=True)
            (root / "data" / "raw").mkdir(parents=True)
            (root / "data" / "processed").mkdir(parents=True)
            (root / "data" / "results").mkdir(parents=True)
            yield root
    
    def test_validate_predictions_schema_missing_file(self, temp_project_root):
        """Test validation when file does not exist."""
        missing_path = temp_project_root / "data" / "processed" / "nonexistent.csv"
        report = validate_predictions_schema(missing_path)
        assert report["valid"] is False
        assert "not found" in report["errors"][0]

    def test_validate_predictions_schema_valid_csv(self, temp_project_root):
        """Test validation with a valid CSV matching schema."""
        import pandas as pd
        df = pd.DataFrame({
            "id": [1, 2],
            "predicted_label": ["SQLi", "XSS"],
            "confidence": [0.9, 0.8],
            "is_correct": [True, False],
            "inference_time_ms": [1.5, 2.0]
        })
        path = temp_project_root / "data" / "processed" / "predictions.csv"
        df.to_csv(path, index=False)
        
        report = validate_predictions_schema(path)
        assert report["valid"] is True
        assert report["count"] == 2

    def test_validate_predictions_schema_missing_columns(self, temp_project_root):
        """Test validation when CSV is missing required columns."""
        import pandas as pd
        df = pd.DataFrame({
            "id": [1],
            "predicted_label": ["SQLi"]
        })
        path = temp_project_root / "data" / "processed" / "predictions.csv"
        df.to_csv(path, index=False)
        
        report = validate_predictions_schema(path)
        assert report["valid"] is False
        assert "Missing columns" in report["errors"][0]

    @patch('src.orchestration.orchestrator.get_available_ram_gb')
    @patch('src.orchestration.orchestrator.get_config')
    @patch('src.orchestration.orchestrator.get_logger')
    @patch('src.orchestration.orchestrator.run_ingest_pipeline')
    @patch('src.orchestration.orchestrator.validate_predictions_schema')
    def test_run_orchestration_success_flow(self, mock_validate, mock_ingest, mock_logger, mock_config, mock_ram, temp_project_root):
        """Test successful orchestration flow when data exists."""
        # Setup mocks
        mock_logger.return_value = MagicMock()
        mock_config.return_value = {}
        mock_ram.return_value = 16.0
        mock_ingest.return_value = None
        mock_validate.return_value = {"valid": True, "count": 100, "errors": []}
        
        # Create dummy processed file to pass the T012 check
        processed_file = temp_project_root / "data" / "processed" / "sampled_snippets.parquet"
        processed_file.touch()
        
        # Create dummy predictions file for validation
        predictions_file = temp_project_root / "data" / "processed" / "predictions.csv"
        predictions_file.touch()
        
        # Change CWD to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            # Mock get_project_root to return temp dir
            with patch('src.orchestration.orchestrator.get_project_root', return_value=temp_project_root):
                exit_code = run_orchestration()
            
            assert exit_code == 0
            mock_ingest.assert_called_once()
            mock_validate.assert_called_once()
        finally:
            os.chdir(original_cwd)

    @patch('src.orchestration.orchestrator.get_available_ram_gb')
    @patch('src.orchestration.orchestrator.get_config')
    @patch('src.orchestration.orchestrator.get_logger')
    @patch('src.orchestration.orchestrator.get_project_root')
    def test_run_orchestration_missing_raw_data(self, mock_root, mock_logger, mock_config, mock_ram, temp_project_root):
        """Test orchestration fails when raw data is missing."""
        mock_logger.return_value = MagicMock()
        mock_config.return_value = {}
        mock_ram.return_value = 16.0
        mock_root.return_value = temp_project_root
        
        # Ensure raw dir is empty
        raw_dir = temp_project_root / "data" / "raw"
        # No files created
        
        exit_code = run_orchestration()
        assert exit_code == 1 # Blocked status
        
        # Verify log was written
        log_path = temp_project_root / "data" / "logs" / "orchestration_log.json"
        assert log_path.exists()
        with open(log_path) as f:
            log_data = json.load(f)
        assert log_data["status"] == "blocked_missing_data"

    @patch('src.orchestration.orchestrator.get_available_ram_gb')
    @patch('src.orchestration.orchestrator.get_config')
    @patch('src.orchestration.orchestrator.get_logger')
    @patch('src.orchestration.orchestrator.get_project_root')
    def test_run_orchestration_missing_processed_data(self, mock_root, mock_logger, mock_config, mock_ram, temp_project_root):
        """Test orchestration fails when processed data is missing."""
        mock_logger.return_value = MagicMock()
        mock_config.return_value = {}
        mock_ram.return_value = 16.0
        mock_root.return_value = temp_project_root
        
        # Create raw dir with a dummy file to pass T010 check
        (temp_project_root / "data" / "raw" / "dummy.txt").touch()
        
        exit_code = run_orchestration()
        assert exit_code == 1 # Blocked status
        
        log_path = temp_project_root / "data" / "logs" / "orchestration_log.json"
        assert log_path.exists()
        with open(log_path) as f:
            log_data = json.load(f)
        assert log_data["status"] == "blocked_missing_processed"