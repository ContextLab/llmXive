import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from model_training.train import load_training_data, train_epoch, evaluate_model, run_training
from config import Config, set_config, reset_config
from model_training.mlp_model import create_model

class TestTrainLoop:
    """
    Tests for the training loop implementation (T023).
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary directories and mock config for each test."""
        self.tmp_path = tmp_path
        self.data_dir = tmp_path / "data" / "raw"
        self.model_dir = tmp_path / "data" / "models"
        self.metric_dir = tmp_path / "data" / "metrics"
        
        self.data_dir.mkdir(parents=True)
        self.model_dir.mkdir(parents=True)
        self.metric_dir.mkdir(parents=True)
        
        # Create a mock config
        self.config = Config(
            CPU_ONLY=True,
            EPSILON_FLOOR=1e-6,
            RANDOM_SEED=42,
            NUM_MATRICES=100,
            SIMULATION_STEPS=10,
            NUM_RUNS=30,
            LEARNING_RATE=0.001,
            NUM_EPOCHS=5
        )
        set_config(self.config)
        
        # Create a small mock dataset
        self._create_mock_dataset()

    def _create_mock_dataset(self):
        """Generates a small CSV dataset for testing."""
        n_samples = 50
        np.random.seed(42)
        data = {
            'mean': np.random.uniform(0.1, 0.5, n_samples).astype(np.float32),
            'variance': np.random.uniform(0.01, 0.1, n_samples).astype(np.float32),
            'scaling_factor': np.random.uniform(0.8, 1.2, n_samples).astype(np.float32)
        }
        df = pd.DataFrame(data)
        df.to_csv(self.data_dir / "synthetic_attention_matrices.csv", index=False)

    def test_load_training_data(self):
        """Test that load_training_data correctly reads the CSV and returns tensors."""
        X, y = load_training_data(self.config)
        
        assert isinstance(X, np.ndarray), "X should be a numpy array"
        assert isinstance(y, np.ndarray), "y should be a numpy array"
        assert X.shape[1] == 2, "X should have 2 features (mean, variance)"
        assert len(X) == len(y), "X and y should have same length"
        assert X.shape[0] == 50, "Should load 50 samples"

    def test_train_epoch(self):
        """Test that one epoch of training reduces loss."""
        # Prepare data
        X, y = load_training_data(self.config)
        train_dataset = TensorDataset(
            torch.tensor(X[:40], dtype=torch.float32),
            torch.tensor(y[:40], dtype=torch.float32)
        )
        loader = DataLoader(train_dataset, batch_size=10, shuffle=True)
        
        model = create_model(input_dim=2)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        loss_fn = torch.nn.MSELoss()
        device = torch.device("cpu")
        
        # Initial loss
        initial_loss = evaluate_model(model, loader, loss_fn, device)
        
        # Train one epoch
        final_loss = train_epoch(model, loader, optimizer, loss_fn, device)
        
        assert final_loss < initial_loss, f"Loss should decrease: {final_loss} vs {initial_loss}"

    def test_run_training_creates_artifacts(self):
        """Test that run_training creates the required output files."""
        # Patch paths in config to use temp dirs (simulating project root)
        # We rely on get_project_root() logic, so we need to ensure the mock data is at the expected relative path
        # For this test, we'll just verify the function logic by mocking get_project_root if needed,
        # but here we assume the fixture setup matches the expected relative structure if we ran from tmp_path.
        # To be safe, we'll manually override the config paths or mock the function.
        
        # Simpler approach: Just run the function and check for file creation in the expected relative locations
        # relative to the current working directory if we were in a project.
        # Since we are in a test, we will mock the project root logic or just check the files.
        
        # Let's assume the test runs in a context where tmp_path acts as root.
        # We need to ensure load_training_data finds the file.
        # The function uses get_project_root() which usually looks for a marker or CWD.
        # We will patch the config or the function to use our tmp_path.
        
        import model_training.train as train_module
        from unittest.mock import patch
        
        def mock_get_project_root():
            return self.tmp_path
        
        with patch.object(train_module, 'get_project_root', mock_get_project_root):
            results = run_training(self.config)
        
        assert "model_path" in results
        assert "log_path" in results
        
        model_path = Path(results["model_path"])
        log_path = Path(results["log_path"])
        
        assert model_path.exists(), f"Model file not created at {model_path}"
        assert log_path.exists(), f"Log file not created at {log_path}"
        
        # Verify model can be loaded
        model = create_model(input_dim=2)
        model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
        model.eval()
        
        # Verify log content
        log_df = pd.read_csv(log_path)
        assert len(log_df) == self.config.NUM_EPOCHS, "Log should have one row per epoch"
        assert "epoch" in log_df.columns
        assert "train_loss" in log_df.columns
        assert "val_loss" in log_df.columns

    def test_training_log_has_hyperparams(self):
        """Test that training hyperparameters are logged (T043)."""
        import model_training.train as train_module
        from unittest.mock import patch
        
        def mock_get_project_root():
            return self.tmp_path
        
        with patch.object(train_module, 'get_project_root', mock_get_project_root):
            run_training(self.config)
        
        hp_path = self.tmp_path / "data" / "metrics" / "training_hyperparams.json"
        assert hp_path.exists(), "Hyperparameters file not created"
        
        with open(hp_path, 'r') as f:
            hp = json.load(f)
        
        assert hp["learning_rate"] == self.config.LEARNING_RATE
        assert hp["batch_size"] == 64
        assert hp["num_epochs"] == self.config.NUM_EPOCHS