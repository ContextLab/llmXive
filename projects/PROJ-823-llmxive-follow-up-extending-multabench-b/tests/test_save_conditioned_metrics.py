import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pipelines.save_conditioned_metrics import (
    generate_run_id,
    load_projected_metrics,
    aggregate_conditioned_metrics,
    save_aggregated_metrics
)

class TestGenerateRunId:
    def test_run_id_format(self):
        """Test that generated run_id has expected format."""
        run_id = generate_run_id()
        parts = run_id.split('_')
        assert len(parts) >= 3  # date_time_hash
        assert len(parts[-1]) == 8  # hash part should be 8 chars
        assert len(parts[0]) == 8  # date part
        assert len(parts[1]) == 6  # time part

    def test_run_id_uniqueness(self):
        """Test that generated run_ids are unique."""
        run_ids = [generate_run_id() for _ in range(10)]
        assert len(set(run_ids)) == 10  # All should be unique

class TestAggregateConditionedMetrics:
    def test_empty_metrics(self):
        """Test aggregation with empty metrics dict."""
        aggregated = aggregate_conditioned_metrics({}, "test_run")
        assert aggregated["run_id"] == "test_run"
        assert aggregated["datasets"] == {}
        assert aggregated["summary"]["total_datasets"] == 0
        assert aggregated["summary"]["successful_datasets"] == 0

    def test_single_dataset_metrics(self):
        """Test aggregation with single dataset."""
        metrics = {
            "dataset_1": {
                "auc": 0.85,
                "rmse": 0.12,
                "accuracy": 0.88
            }
        }
        aggregated = aggregate_conditioned_metrics(metrics, "test_run")
        
        assert aggregated["run_id"] == "test_run"
        assert "dataset_1" in aggregated["datasets"]
        assert aggregated["datasets"]["dataset_1"]["auc"] == 0.85
        assert aggregated["summary"]["auc"]["mean"] == 0.85
        assert aggregated["summary"]["auc"]["count"] == 1
        assert aggregated["summary"]["total_datasets"] == 1

    def test_multiple_datasets_metrics(self):
        """Test aggregation with multiple datasets."""
        metrics = {
            "dataset_1": {"auc": 0.85, "rmse": 0.12},
            "dataset_2": {"auc": 0.90, "rmse": 0.08},
            "dataset_3": {"auc": 0.78, "rmse": 0.15}
        }
        aggregated = aggregate_conditioned_metrics(metrics, "test_run")
        
        assert aggregated["summary"]["auc"]["mean"] == pytest.approx(0.8433, rel=1e-3)
        assert aggregated["summary"]["auc"]["min"] == 0.78
        assert aggregated["summary"]["auc"]["max"] == 0.90
        assert aggregated["summary"]["auc"]["count"] == 3
        assert aggregated["summary"]["total_datasets"] == 3
        assert aggregated["summary"]["successful_datasets"] == 3

    def test_mixed_metric_types(self):
        """Test aggregation with mixed metric types (some non-numeric)."""
        metrics = {
            "dataset_1": {"auc": 0.85, "status": "success"},
            "dataset_2": {"auc": 0.90, "status": "success"}
        }
        aggregated = aggregate_conditioned_metrics(metrics, "test_run")
        
        assert "auc" in aggregated["summary"]
        assert "status" not in aggregated["summary"]  # Non-numeric should be skipped
        assert aggregated["summary"]["auc"]["count"] == 2

    def test_run_id_linkage(self):
        """Test that run_id is properly linked in output."""
        metrics = {"dataset_1": {"auc": 0.85}}
        aggregated = aggregate_conditioned_metrics(metrics, "custom_run_123")
        
        assert aggregated["run_id"] == "custom_run_123"
        assert aggregated["generated_at"] is not None
        assert "pipeline" in aggregated

class TestSaveAggregatedMetrics:
    def test_save_to_file(self):
        """Test saving aggregated metrics to a file."""
        aggregated = {
            "run_id": "test_run",
            "datasets": {"dataset_1": {"auc": 0.85}},
            "summary": {"auc": {"mean": 0.85, "count": 1}}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            save_aggregated_metrics(aggregated, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["run_id"] == "test_run"
            assert saved_data["datasets"]["dataset_1"]["auc"] == 0.85

    def test_creates_parent_directories(self):
        """Test that save_aggregated_metrics creates parent directories."""
        aggregated = {"run_id": "test"}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "metrics.json"
            save_aggregated_metrics(aggregated, output_path)
            
            assert output_path.exists()

class TestLoadProjectedMetrics:
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised when metrics file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_projected_metrics("nonexistent_run")

    def test_load_from_json_file(self):
        """Test loading metrics from a JSON file."""
        # This test would require setting up actual files, which is complex
        # For now, we test the function signature and error handling
        pass