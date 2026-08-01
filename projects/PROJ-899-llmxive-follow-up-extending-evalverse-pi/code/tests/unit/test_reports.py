import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Import the functions we are testing
# We need to mock the path helpers to use temp directories
from unittest.mock import patch, MagicMock
from src.reports.generate import load_feasibility_results, generate_feasibility_report, save_feasibility_report

class TestFeasibilityReportGeneration:
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory with mock profiling and timing data."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create mock profiling_logs.json
        profiling_data = {
            "results": [
                {"clip_id": "clip_001", "peak_memory_mb": 2048, "cpu_time_seconds": 10.5},
                {"clip_id": "clip_002", "peak_memory_mb": 3072, "cpu_time_seconds": 12.0},
                {"clip_id": "clip_003", "peak_memory_mb": 2560, "cpu_time_seconds": 11.0}
            ]
        }
        with open(data_dir / "profiling_logs.json", 'w') as f:
            json.dump(profiling_data, f)
        
        # Create mock timing_profile.csv
        timing_df = pd.DataFrame({
            "clip_id": ["clip_001", "clip_002", "clip_003"],
            "time_seconds": [10.5, 12.0, 11.0],
            "projected_total_hours": [0.003, 0.0033, 0.0033] # Mock projection
        })
        # Add a row for the 10k projection
        projection_row = pd.DataFrame({
            "clip_id": ["total_projection"],
            "time_seconds": [10000], # dummy
            "projected_total_hours": [0.0033] # Mock projection for 10k
        })
        timing_df = pd.concat([timing_df, projection_row], ignore_index=True)
        timing_df.to_csv(data_dir / "timing_profile.csv", index=False)
        
        return data_dir

    def test_load_feasibility_results_with_data(self, temp_data_dir):
        """Test loading feasibility results from mock data."""
        with patch('src.reports.generate.get_data_root', return_value=temp_data_dir):
            results = load_feasibility_results()
            
            assert results["status"] == "MEASURED"
            # Peak memory should be max of [2048, 3072, 2560] / 1024 = 3.0
            assert abs(results["peak_memory_gb"] - 3.0) < 0.01
            # Projected hours should be from the last row
            assert results["projected_total_hours"] == 0.0033

    def test_generate_feasibility_report_pass(self, temp_data_dir):
        """Test report generation when constraints are met."""
        with patch('src.reports.generate.get_data_root', return_value=temp_data_dir):
            report = generate_feasibility_report()
            
            assert report["metrics"]["status"] == "MEASURED"
            assert report["pass"] is True
            assert "All feasibility constraints satisfied" in report["notes"]

    def test_generate_feasibility_report_fail_memory(self, temp_data_dir):
        """Test report generation when memory constraint fails."""
        # Modify the mock data to have high memory
        high_mem_data = {
            "results": [{"clip_id": "c1", "peak_memory_mb": 8192}] # 8GB > 7GB
        }
        (temp_data_dir / "profiling_logs.json").write_text(json.dumps(high_mem_data))
        
        # Reset timing to pass
        timing_df = pd.DataFrame({
            "clip_id": ["total"],
            "projected_total_hours": [1.0]
        })
        timing_df.to_csv(temp_data_dir / "timing_profile.csv", index=False)

        with patch('src.reports.generate.get_data_root', return_value=temp_data_dir):
            report = generate_feasibility_report()
            
            assert report["pass"] is False
            assert "Memory constraint failed" in str(report["notes"])

    def test_save_feasibility_report(self, temp_data_dir, tmp_path):
        """Test saving the report to a file."""
        report = {
            "task_id": "T025",
            "metrics": {"peak_memory_gb": 1.0, "projected_total_hours": 1.0, "status": "MEASURED"},
            "pass": True,
            "notes": ["OK"]
        }
        
        output_path = tmp_path / "reports" / "feasibility_profile.json"
        saved_path = save_feasibility_report(report, output_path)
        
        assert saved_path.exists()
        with open(saved_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["pass"] is True
        assert loaded["metrics"]["peak_memory_gb"] == 1.0