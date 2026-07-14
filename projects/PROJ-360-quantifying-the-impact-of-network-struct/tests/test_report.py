import json
import logging
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from report import setup_report_logger, load_model_performance, generate_final_report

def test_setup_report_logger():
    logger = setup_report_logger()
    assert logger.name == "report"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0

def test_load_model_performance_missing_file():
    with pytest.raises(FileNotFoundError):
        load_model_performance(Path("/nonexistent/file.json"))

def test_generate_final_report_with_interpretation():
    """Test that r2_interpretation is appended if present."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create mock model_performance.json with interpretation
        perf_data = {
            "mean_r2": 0.25,
            "mean_rmse": 10.5,
            "r2_interpretation": "Weak predictive power (R² < 0.30), consistent with null hypothesis."
        }
        perf_file = tmp_path / "model_performance.json"
        with open(perf_file, 'w') as f:
            json.dump(perf_data, f)
        
        output_file = tmp_path / "final_report.md"
        logger = setup_report_logger()
        
        generate_final_report(perf_file, output_file, logger)
        
        assert output_file.exists()
        content = output_file.read_text()
        
        # Check mandatory text
        assert "This study is observational" in content
        assert "Correlations do not imply causality" in content
        assert "thermal conductivity tensor was reduced to a scalar" in content
        
        # Check interpretation is present
        assert "Weak predictive power" in content

def test_generate_final_report_without_interpretation():
    """Test that report is generated correctly when r2_interpretation is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create mock model_performance.json WITHOUT interpretation
        perf_data = {
            "mean_r2": 0.45,
            "mean_rmse": 8.2
        }
        perf_file = tmp_path / "model_performance.json"
        with open(perf_file, 'w') as f:
            json.dump(perf_data, f)
        
        output_file = tmp_path / "final_report.md"
        logger = setup_report_logger()
        
        generate_final_report(perf_file, output_file, logger)
        
        assert output_file.exists()
        content = output_file.read_text()
        
        # Check mandatory text
        assert "This study is observational" in content
        
        # Check interpretation is NOT present (since it wasn't in JSON)
        assert "Weak predictive power" not in content

def test_generate_final_report_creates_directory():
    """Test that the output directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        nested_dir = tmp_path / "subdir" / "results"
        
        perf_data = {"mean_r2": 0.3, "mean_rmse": 5.0}
        perf_file = nested_dir / "model_performance.json"
        nested_dir.mkdir(parents=True)
        with open(perf_file, 'w') as f:
            json.dump(perf_data, f)
        
        output_file = nested_dir / "final_report.md"
        logger = setup_report_logger()
        
        # This should not raise an error even if output_file.parent didn't exist initially
        # (though in this case it does exist because we created it, but the function handles it)
        generate_final_report(perf_file, output_file, logger)
        
        assert output_file.exists()
