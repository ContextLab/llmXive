import os
import sys
import json
import tempfile
import torch
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.save_artifacts import save_best_model, save_metrics, load_best_training_result
from models.mpnn import MPNN, MPNNConfig

class TestSaveArtifacts:
    @pytest.fixture
    def temp_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = Path(tmpdir) / "models"
            metrics_dir = Path(tmpdir) / "metrics"
            results_dir = Path(tmpdir) / "results"
            model_dir.mkdir()
            metrics_dir.mkdir()
            results_dir.mkdir()
            yield model_dir, metrics_dir, results_dir

    def test_save_best_model_torch(self, temp_dirs):
        model_dir, _, _ = temp_dirs
        model = MPNN(input_dim=10, hidden_dim=32, output_dim=1, num_layers=2)
        path = save_best_model(model, model_dir, "test_model.pt")
        
        assert path.exists()
        # Verify it's a valid torch file
        state = torch.load(path, map_location='cpu')
        assert 'encoder.weight' in state or len(list(state.keys())) > 0

    def test_save_metrics(self, temp_dirs):
        _, metrics_dir, _ = temp_dirs
        metrics = {
            "r2": 0.85,
            "mae": 0.12,
            "test_r2": 0.82,
            "test_mae": 0.15
        }
        path = save_metrics(metrics, metrics_dir, "test_metrics.json")
        
        assert path.exists()
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded["r2"] == 0.85
        assert loaded["mae"] == 0.12

    def test_load_best_training_result_missing(self, temp_dirs):
        _, _, results_dir = temp_dirs
        with pytest.raises(FileNotFoundError):
            load_best_training_result(results_dir)

    def test_load_best_training_result_success(self, temp_dirs):
        _, _, results_dir = temp_dirs
        best_data = {
            "model_id": "test-1",
            "val_r2": 0.9,
            "val_mae": 0.05,
            "config": {
                "input_dim": 10,
                "hidden_dim": 32,
                "output_dim": 1,
                "num_layers": 2,
                "dropout": 0.1
            }
        }
        
        result_file = results_dir / "best_result.json"
        with open(result_file, 'w') as f:
            json.dump(best_data, f)
        
        loaded = load_best_training_result(results_dir)
        assert loaded["val_r2"] == 0.9
        assert loaded["config"]["hidden_dim"] == 32
