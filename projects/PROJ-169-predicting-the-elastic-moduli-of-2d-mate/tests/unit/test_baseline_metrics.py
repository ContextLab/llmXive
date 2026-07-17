import pytest
import os
import json
import tempfile
import numpy as np
from pathlib import Path

# Mock the necessary imports for unit testing without full pipeline
from unittest.mock import patch, MagicMock
from model.baseline_metrics import BaselineResult, BaselineReport, run_intra_family_baseline
from model.splitter import load_graphs_from_parquet

def create_mock_graph(family_id, n_nodes=5):
    """Create a minimal mock graph dict for testing."""
    return {
        "family_id": family_id,
        "node_features": np.random.rand(n_nodes, 12).tolist(),
        "edge_index": [[0, 1], [1, 2]].tolist(),
        "target_moduli": [1.0, 2.0, 3.0], # Young, Shear, Poisson
        "edge_features": [[1.0]].tolist()
    }

def test_baseline_result_dataclass():
    result = BaselineResult(mape=0.1, rmse=0.05, r2=0.9, family="test", sample_size=10)
    assert result.mape == 0.1
    assert result.family == "test"

def test_baseline_report_dataclass():
    result = BaselineResult(mape=0.1, rmse=0.05, r2=0.9, family="test", sample_size=10)
    report = BaselineReport(
        intra_family_metrics=[{"mape": 0.1}],
        aggregated_metrics={"mape": 0.1},
        description="Test"
    )
    assert len(report.intra_family_metrics) == 1
    assert report.description == "Test"

@patch('model.baseline_metrics.graph_to_pyg')
@patch('model.baseline_metrics.PyGDataLoader')
@patch('model.baseline_metrics.create_model')
def test_run_intra_family_baseline_skips_small_families(mock_model, mock_loader, mock_to_pyg):
    """Test that families with < 20 samples are skipped."""
    # Create a list of graphs where one family has 5 items, another has 50
    small_family = [create_mock_graph("fam_small") for _ in range(5)]
    large_family = [create_mock_graph("fam_large") for _ in range(50)]
    graphs = small_family + large_family

    # Mock the model and loader to avoid actual training
    mock_model_instance = MagicMock()
    mock_model.return_value = mock_model_instance
    mock_loader.return_value.__iter__ = MagicMock(return_value=iter([]))
    mock_to_pyg.side_effect = lambda x: x # Just return the dict for mock

    # Run
    results = run_intra_family_baseline(graphs, None, torch.device("cpu"), batch_size=32)

    # Verify
    # fam_small should be skipped
    assert len(results) == 1
    assert results[0]["family_id"] == "fam_large"
    assert results[0]["sample_size"] > 0

@patch('model.baseline_metrics.graph_to_pyg')
@patch('model.baseline_metrics.PyGDataLoader')
@patch('model.baseline_metrics.create_model')
@patch('model.baseline_metrics.train_epoch')
@patch('model.baseline_metrics.evaluate')
def test_run_intra_family_baseline_computes_metrics(mock_eval, mock_train, mock_model, mock_loader, mock_to_pyg):
    """Test that metrics are computed for valid families."""
    # Create a family with enough data
    large_family = [create_mock_graph("fam_valid") for _ in range(30)]
    
    # Mock training/eval to return dummy values
    mock_train.return_value = 0.5
    mock_eval.return_value = (np.array([1.0, 1.0]), np.array([1.1, 0.9])) # preds, targets
    
    mock_model_instance = MagicMock()
    mock_model.return_value = mock_model_instance
    mock_loader.return_value.__iter__ = MagicMock(return_value=iter([]))
    mock_to_pyg.side_effect = lambda x: x

    results = run_intra_family_baseline(large_family, None, torch.device("cpu"), batch_size=32)

    assert len(results) == 1
    assert "mape" in results[0]
    assert "rmse" in results[0]
    assert "r2" in results[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
