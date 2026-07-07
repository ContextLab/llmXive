import json
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.clean import calculate_coverage_rate

class TestCoverageRateCalculation:
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_proc_dir = tmp_path / "data" / "processed"
            data_proc_dir.mkdir(parents=True, exist_ok=True)
            yield tmp_path
    
    def test_coverage_rate_calculation(self, temp_dirs):
        """Test that coverage rate is calculated correctly."""
        total_records_path = temp_dirs / "data" / "processed" / "total_records_count.json"
        metrics_output_path = temp_dirs / "data" / "processed" / "metrics.json"
        
        # Create mock total records file
        mock_total_data = {
            "year_range": [2000, 2020],
            "total_records": 1000,
            "sources": {"test": "data"}
        }
        with open(total_records_path, 'w') as f:
            json.dump(mock_total_data, f)
        
        # Create mock merged dataframe (500 rows)
        mock_df = pd.DataFrame({
            'country': ['A'] * 500,
            'year': list(range(2000, 2020)) * 25
        })
        
        # Run calculation
        result = calculate_coverage_rate(
            merged_df=mock_df,
            total_records_path=str(total_records_path),
            metrics_output_path=str(metrics_output_path)
        )
        
        # Assertions
        assert result['merged_record_count'] == 500
        assert result['total_available_record_count'] == 1000
        assert abs(result['coverage_rate'] - 0.5) < 1e-6
        
        # Verify file was written
        assert metrics_output_path.exists()
        with open(metrics_output_path, 'r') as f:
            saved_metrics = json.load(f)
        
        assert saved_metrics['coverage_rate'] == 0.5
        assert saved_metrics['metric'] == 'coverage_rate'

    def test_coverage_rate_zero_total(self, temp_dirs):
        """Test behavior when total records is 0."""
        total_records_path = temp_dirs / "data" / "processed" / "total_records_count.json"
        metrics_output_path = temp_dirs / "data" / "processed" / "metrics.json"
        
        mock_total_data = {
            "year_range": [2000, 2020],
            "total_records": 0,
            "sources": {}
        }
        with open(total_records_path, 'w') as f:
            json.dump(mock_total_data, f)
        
        mock_df = pd.DataFrame({'country': ['A']})
        
        result = calculate_coverage_rate(
            merged_df=mock_df,
            total_records_path=str(total_records_path),
            metrics_output_path=str(metrics_output_path)
        )
        
        assert result['coverage_rate'] == 0.0

    def test_missing_total_records_file(self, temp_dirs):
        """Test that FileNotFoundError is raised if total records file is missing."""
        total_records_path = temp_dirs / "data" / "processed" / "missing.json"
        metrics_output_path = temp_dirs / "data" / "processed" / "metrics.json"
        
        mock_df = pd.DataFrame({'country': ['A']})
        
        with pytest.raises(FileNotFoundError):
            calculate_coverage_rate(
                merged_df=mock_df,
                total_records_path=str(total_records_path),
                metrics_output_path=str(metrics_output_path)
            )