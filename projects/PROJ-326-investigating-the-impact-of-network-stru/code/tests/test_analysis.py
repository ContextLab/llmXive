import json
import pytest
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.src.analysis.aggregate_results import (
    load_simulation_results,
    filter_valid_runs,
    aggregate_metrics,
    load_sensitivity_correlation,
    FAILURE_STATUS_DIVergENCE,
    FAILURE_STATUS_DISCONNECTED
)

class TestAggregateResults:
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary directory structure for testing."""
        analysis_dir = tmp_path / "data" / "analysis"
        analysis_dir.mkdir(parents=True)
        return analysis_dir

    def test_load_simulation_results_valid(self, temp_data_dir):
        """Test loading a valid simulation results file."""
        data = [
            {"network_id": "n1", "diffusion_rate": 0.5, "status": "OK"},
            {"network_id": "n2", "diffusion_rate": 0.6, "status": "OK"}
        ]
        file_path = temp_data_dir / "simulation_results.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_simulation_results(file_path)
        assert len(result) == 2
        assert result[0]["network_id"] == "n1"

    def test_load_simulation_results_missing_file(self, temp_data_dir):
        """Test loading a missing file raises FileNotFoundError."""
        file_path = temp_data_dir / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_simulation_results(file_path)

    def test_filter_valid_runs(self):
        """Test filtering out failed runs."""
        runs = [
            {"network_id": "1", "status": "OK"},
            {"network_id": "2", "status": FAILURE_STATUS_DIVergENCE},
            {"network_id": "3", "status": FAILURE_STATUS_DISCONNECTED},
            {"network_id": "4", "status": "OK"}
        ]
        
        valid, excluded = filter_valid_runs(runs)
        assert len(valid) == 2
        assert excluded == 2
        assert all(r["status"] == "OK" for r in valid)

    def test_aggregate_metrics(self):
        """Test calculation of mean, median, variance."""
        runs = [
            {"diffusion_rate": 1.0},
            {"diffusion_rate": 2.0},
            {"diffusion_rate": 3.0}
        ]
        
        metrics = aggregate_metrics(runs)
        assert metrics["diffusion_rate"]["count"] == 3
        assert metrics["diffusion_rate"]["mean"] == 2.0
        assert metrics["diffusion_rate"]["median"] == 2.0
        # Variance of [1, 2, 3] is 2/3 * 1^2? No, population variance is 2/3 * 1 = 0.666...
        # Numpy var is population variance by default
        assert abs(metrics["diffusion_rate"]["variance"] - 0.6666666666666666) < 1e-6

    def test_aggregate_metrics_empty(self):
        """Test aggregation on empty list."""
        metrics = aggregate_metrics([])
        assert metrics["diffusion_rate"]["count"] == 0
        assert metrics["diffusion_rate"]["mean"] == 0.0

    def test_load_sensitivity_correlation_missing(self, temp_data_dir):
        """Test that missing sensitivity correlation file raises clear error."""
        file_path = temp_data_dir / "sensitivity_correlation.json"
        # File does not exist
        with pytest.raises(FileNotFoundError) as exc_info:
            load_sensitivity_correlation(file_path)
        
        assert "T035c" in str(exc_info.value) or "sensitivity" in str(exc_info.value).lower()

    def test_load_sensitivity_correlation_empty(self, temp_data_dir):
        """Test that empty sensitivity correlation file raises error."""
        file_path = temp_data_dir / "sensitivity_correlation.json"
        with open(file_path, 'w') as f:
            json.dump({}, f) # Empty dict
        
        with pytest.raises(ValueError) as exc_info:
            load_sensitivity_correlation(file_path)
        
        assert "empty" in str(exc_info.value).lower() or "no valid results" in str(exc_info.value).lower()
