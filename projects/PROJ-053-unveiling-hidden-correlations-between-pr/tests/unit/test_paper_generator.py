import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Mock config paths before importing paper_generator
@pytest.fixture(autouse=True)
def mock_config_paths():
    """Mock config paths to avoid dependency on real file structure."""
    with patch('code.utils.paper_generator.get_project_root') as mock_root, \
         patch('code.utils.paper_generator.get_results_dir') as mock_results, \
         patch('code.utils.paper_generator.get_figures_dir') as mock_figures, \
         patch('code.utils.paper_generator.get_processed_data_dir') as mock_processed, \
         patch('code.utils.paper_generator.get_raw_data_dir') as mock_raw, \
         patch('code.utils.paper_generator.get_logs_dir') as mock_logs, \
         patch('code.utils.paper_generator.get_docs_dir') as mock_docs, \
         patch('code.utils.paper_generator.ensure_directories'):
        
        mock_root.return_value = "/fake/project"
        mock_results.return_value = "/fake/project/results"
        mock_figures.return_value = "/fake/project/figures"
        mock_processed.return_value = "/fake/project/data/processed"
        mock_raw.return_value = "/fake/project/data/raw"
        mock_logs.return_value = "/fake/project/logs"
        mock_docs.return_value = "/fake/project/docs"
        
        yield

class TestPaperGenerator:
    def test_load_metrics_success(self, mock_config_paths):
        """Test loading metrics from a valid JSON file."""
        from code.utils.paper_generator import load_metrics
        
        mock_metrics = {"gpr_metrics": {"r2": 0.85}, "baseline_metrics": {"r2": 0.60}}
        
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_metrics)
            with patch('os.path.exists', return_value=True):
                result = load_metrics()
                assert result == mock_metrics
    
    def test_load_metrics_file_not_found(self, mock_config_paths):
        """Test that FileNotFoundError is raised when metrics file is missing."""
        from code.utils.paper_generator import load_metrics
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Metrics file not found"):
                load_metrics()
    
    def test_check_scope_reduction_detected(self, mock_config_paths):
        """Test scope reduction detection when log entry exists."""
        from code.utils.paper_generator import check_scope_reduction
        
        mock_log_content = "[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility."
        
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = mock_log_content
            with patch('os.path.exists', return_value=True):
                result = check_scope_reduction()
                assert result is not None
                assert "fatigue_life was not present" in result
    
    def test_check_scope_reduction_not_detected(self, mock_config_paths):
        """Test scope reduction returns None when log entry is absent."""
        from code.utils.paper_generator import check_scope_reduction
        
        mock_log_content = "INFO: Preprocessing complete."
        
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = mock_log_content
            with patch('os.path.exists', return_value=True):
                result = check_scope_reduction()
                assert result is None
    
    def test_check_scope_reduction_file_missing(self, mock_config_paths):
        """Test scope reduction returns None when log file is missing."""
        from code.utils.paper_generator import check_scope_reduction
        
        with patch('os.path.exists', return_value=False):
            result = check_scope_reduction()
            assert result is None
    
    def test_generate_paper_content_basic(self, mock_config_paths):
        """Test basic paper content generation."""
        from code.utils.paper_generator import generate_paper_content
        
        metrics = {
            "gpr_metrics": {"r2": 0.9, "rmse": 1.5, "mae": 1.2, "rmse_percentage_of_range": 5.0},
            "baseline_metrics": {"r2": 0.7, "rmse": 2.5, "mae": 2.0, "rmse_percentage_of_range": 8.0},
            "gpr_vs_baseline_delta": {"delta_r2": 0.2, "delta_rmse": -1.0, "delta_mae": -0.8}
        }
        bounds = {"laser_power": {"min": 100, "max": 500}}
        
        content = generate_paper_content(metrics, bounds, None)
        
        assert "## Abstract" in content
        assert "Gaussian Process Regression" in content
        assert "0.9000" in content  # R2 value
        assert "Data Provenance" in content
    
    def test_generate_paper_content_with_scope_note(self, mock_config_paths):
        """Test paper content includes scope limitation note."""
        from code.utils.paper_generator import generate_paper_content
        
        metrics = {"gpr_metrics": {}, "baseline_metrics": {}}
        scope_note = "fatigue_life was not present in the raw dataset."
        
        content = generate_paper_content(metrics, {}, scope_note)
        
        assert "### Scope Limitation" in content
        assert scope_note in content
    
    def test_generate_paper_content_with_feasibility_status(self, mock_config_paths):
        """Test paper includes feasibility status when present in metrics."""
        from code.utils.paper_generator import generate_paper_content
        
        metrics = {
            "gpr_metrics": {},
            "baseline_metrics": {},
            "feasibility_status": "FAILED",
            "runtime_seconds": 25000
        }
        
        content = generate_paper_content(metrics, {}, None)
        
        assert "Feasibility Check" in content
        assert "FAILED" in content
        assert "25000" in content
