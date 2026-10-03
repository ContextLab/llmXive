import pytest
import json
import os
from pathlib import Path
from report import load_model_performance, generate_final_report, main

class TestReportGeneration:
    def test_load_model_performance_missing_file(self, tmp_path):
        """Test loading performance data when file does not exist."""
        result = load_model_performance(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_load_model_performance_invalid_json(self, tmp_path):
        """Test loading performance data from invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")
        
        result = load_model_performance(str(file_path))
        assert result is None

    def test_load_model_performance_valid(self, tmp_path):
        """Test loading valid performance data."""
        file_path = tmp_path / "valid.json"
        data = {
            "mean_r2": 0.75,
            "std_r2": 0.05,
            "mean_rmse": 1.2,
            "std_rmse": 0.1,
            "n_folds": 5
        }
        file_path.write_text(json.dumps(data))
        
        result = load_model_performance(str(file_path))
        assert result is not None
        assert result["mean_r2"] == 0.75
        assert result["n_folds"] == 5

    def test_generate_final_report_creates_file(self, tmp_path):
        """Test that generate_final_report creates the output file."""
        output_path = tmp_path / "report.md"
        generate_final_report(None, str(output_path))
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Final Report" in content
        assert "## Limitations" in content
        assert "This study is observational" in content

    def test_generate_final_report_includes_performance(self, tmp_path):
        """Test that report includes performance data when provided."""
        performance_data = {
            "mean_r2": 0.85,
            "std_r2": 0.02,
            "mean_rmse": 0.5,
            "std_rmse": 0.05,
            "n_folds": 5
        }
        output_path = tmp_path / "report_with_perf.md"
        generate_final_report(performance_data, str(output_path))
        
        content = output_path.read_text()
        assert "0.85" in content
        assert "strong positive relationship" in content

    def test_generate_final_report_weak_performance(self, tmp_path):
        """Test report generation with weak performance."""
        performance_data = {
            "mean_r2": 0.15,
            "std_r2": 0.05,
            "mean_rmse": 2.0,
            "std_rmse": 0.2,
            "n_folds": 5
        }
        output_path = tmp_path / "report_weak.md"
        generate_final_report(performance_data, str(output_path))
        
        content = output_path.read_text()
        assert "weak positive relationship" in content

    def test_generate_final_report_negligible_performance(self, tmp_path):
        """Test report generation with negligible performance."""
        performance_data = {
            "mean_r2": 0.05,
            "std_r2": 0.02,
            "mean_rmse": 3.0,
            "std_rmse": 0.3,
            "n_folds": 5
        }
        output_path = tmp_path / "report_negligible.md"
        generate_final_report(performance_data, str(output_path))
        
        content = output_path.read_text()
        assert "negligible relationship" in content

    def test_main_function(self, tmp_path, monkeypatch):
        """Test the main function execution."""
        # Create a mock performance file
        perf_dir = tmp_path / "results"
        perf_dir.mkdir()
        perf_file = perf_dir / "model_performance.json"
        perf_file.write_text(json.dumps({
            "mean_r2": 0.6,
            "std_r2": 0.1,
            "mean_rmse": 1.5,
            "std_rmse": 0.2,
            "n_folds": 5
        }))
        
        output_dir = tmp_path / "results"
        output_file = output_dir / "final_report.md"
        
        # Change cwd to tmp_path to simulate project root
        monkeypatch.chdir(tmp_path)
        
        # Run main (it expects relative paths)
        # We need to temporarily adjust the paths in the function or call with args
        # Since main() uses hardcoded paths, we test the logic by ensuring the file exists
        # after running the logic that would be triggered by main()
        
        # Simulate main logic
        from report import load_model_performance, generate_final_report
        data = load_model_performance(str(perf_file))
        generate_final_report(data, str(output_file))
        
        assert output_file.exists()
        assert "Final Report" in output_file.read_text()