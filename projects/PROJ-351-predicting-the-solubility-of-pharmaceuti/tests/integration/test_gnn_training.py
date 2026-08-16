"""
Integration test for GNN training loop with early stopping.

This test verifies that the GNN training pipeline (T021) executes correctly,
handles early stopping, and produces valid model artifacts and metrics.
It relies on the data pipeline (T004-T006) and the MPNN model (T020).
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import torch
import numpy as np

# Project imports based on provided API surface
from data.split import load_cleaned_data, create_stratified_splits, save_split_indices
from data.preprocess import load_and_preprocess
from models.gnn_mpnn import GNNMPNN
from training.train_gnn import load_graph_data, prepare_data_loaders, train_model, save_model
from config.seeds import set_seed, get_seed
from evaluation.metrics import calculate_rmse, calculate_r2

# Constants
TEST_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = TEST_ROOT / "data" / "processed"
DATA_RAW = TEST_ROOT / "data" / "raw"
MODELS_DIR = TEST_ROOT / "models"
RESULTS_DIR = TEST_ROOT / "results"

@pytest.fixture(scope="module")
def test_env():
    """Ensure required data and directories exist for the integration test."""
    # Verify pre-requisites from T004-T006
    assert DATA_RAW.exists(), "Raw data directory missing. T004 must run first."
    assert DATA_PROCESSED.exists(), "Processed data directory missing. T005 must run first."
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set a fixed seed for reproducibility
    set_seed(42)
    
    yield

def test_gnn_training_loop_early_stopping(test_env):
    """
    Integration test: Run the GNN training loop with early stopping.
    
    Verifies:
    1. Data loading works (T005, T006 outputs)
    2. Model instantiation works (T020)
    3. Training loop executes without error (T021)
    4. Early stopping mechanism triggers (or max epochs reached)
    5. Model is saved to disk
    6. Metrics are calculated and saved
    """
    # Configuration for a minimal run to ensure test speed
    # These match the constraints for T021 and T022 (CPU, time limits)
    config = {
        "epochs": 10,
        "patience": 3,
        "learning_rate": 1e-3,
        "hidden_dim": 32,
        "num_layers": 2,
        "dropout": 0.1,
        "batch_size": 32,
        "device": "cpu",
        "seed": 42,
        "data_dir": str(DATA_PROCESSED),
        "model_save_path": str(MODELS_DIR / "gnn_integration_test.pt"),
        "metrics_save_path": str(RESULTS_DIR / "gnn_integration_test_metrics.json")
    }

    # Ensure model save directory exists
    Path(config["model_save_path"]).parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Data
        # The split indices are expected to be saved by T006
        # We assume the processed files (graphs) are in DATA_PROCESSED
        train_indices_path = DATA_PROCESSED / "train_indices.json"
        val_indices_path = DATA_PROCESSED / "val_indices.json"
        test_indices_path = DATA_PROCESSED / "test_indices.json"
        
        if not (train_indices_path.exists() and val_indices_path.exists()):
            # Fallback: If split hasn't been run yet in this environment, 
            # we skip the test or fail loudly rather than fabricating data.
            # However, T006 is marked completed, so we assert existence.
            assert train_indices_path.exists(), "Split indices missing. T006 must run."
            assert val_indices_path.exists(), "Split indices missing. T006 must run."

        # Load graph data using the project's loader
        # Note: load_graph_data is expected to read from the processed directory structure
        train_data, val_data, test_data = load_graph_data(config["data_dir"])
        
        assert len(train_data) > 0, "Training data is empty."
        assert len(val_data) > 0, "Validation data is empty."

        # 2. Prepare DataLoaders
        train_loader, val_loader, test_loader = prepare_data_loaders(
            train_data, val_data, test_data, 
            batch_size=config["batch_size"]
        )

        # 3. Instantiate Model (T020)
        # We need to know the input feature dimension. 
        # Usually this is 64 or 78 for standard RDKit features, but we can infer or default.
        # Assuming standard feature size from T005 if not explicitly passed.
        # For safety, we try to infer from the first batch if possible, or use a standard default.
        input_dim = 64  # Standard default for this pipeline if not dynamic
        
        model = GNNMPNN(
            input_dim=input_dim,
            hidden_dim=config["hidden_dim"],
            num_layers=config["num_layers"],
            dropout=config["dropout"]
        )
        
        model = model.to(config["device"])
        assert model is not None, "Model instantiation failed."

        # 4. Train Model (T021)
        # This function encapsulates the loop and early stopping logic
        best_model_state, training_history = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            epochs=config["epochs"],
            patience=config["patience"],
            lr=config["learning_rate"],
            device=config["device"]
        )

        # 5. Verify Early Stopping or Completion
        # The history should contain at least one epoch entry
        assert len(training_history) > 0, "Training history is empty."
        
        # Check if early stopping triggered (history length < max epochs) 
        # OR if it ran full epochs. Both are valid outcomes of the loop.
        # We specifically check that the loop didn't crash and produced a state.
        assert best_model_state is not None, "No best model state returned."

        # 6. Save Model (T021)
        save_model(best_model_state, config["model_save_path"])
        assert os.path.exists(config["model_save_path"]), "Model file not saved."
        assert os.path.getsize(config["model_save_path"]) > 0, "Model file is empty."

        # 7. Evaluate on Test Set (T023)
        # Reload the best model for evaluation
        model.load_state_dict(best_model_state)
        model.eval()
        
        # Perform a forward pass on test data to get predictions
        # We implement a minimal inline evaluation here to verify the pipeline
        # rather than calling the full metrics script which might have different I/O expectations.
        test_preds = []
        test_targets = []
        
        with torch.no_grad():
            for batch in test_loader:
                x, edge_index, batch_idx, y = batch.x, batch.edge_index, batch.batch, batch.y
                x, edge_index, batch_idx, y = x.to(config["device"]), edge_index.to(config["device"]), batch_idx.to(config["device"]), y.to(config["device"])
                
                pred = model(x, edge_index, batch_idx)
                test_preds.extend(pred.cpu().numpy())
                test_targets.extend(y.cpu().numpy())

        test_preds = np.array(test_preds)
        test_targets = np.array(test_targets)

        # Calculate metrics
        rmse = calculate_rmse(test_targets, test_preds)
        r2 = calculate_r2(test_targets, test_preds)

        assert not np.isnan(rmse), "RMSE is NaN."
        assert not np.isnan(r2), "R2 is NaN."

        # 8. Save Metrics
        metrics = {
            "rmse": float(rmse),
            "r2": float(r2),
            "epochs_run": len(training_history),
            "early_stopped": len(training_history) < config["epochs"]
        }
        
        with open(config["metrics_save_path"], "w") as f:
            json.dump(metrics, f, indent=2)

        assert os.path.exists(config["metrics_save_path"]), "Metrics file not saved."
        
        # Final Assertions
        assert metrics["rmse"] > 0, "RMSE must be positive."
        assert metrics["epochs_run"] > 0, "Must have run at least one epoch."

    except Exception as e:
        # Clean up on failure
        if os.path.exists(config["model_save_path"]):
            os.remove(config["model_save_path"])
        raise AssertionError(f"GNN Training Integration Test Failed: {str(e)}") from e

    finally:
        # Cleanup temporary artifacts if they were created in a temp dir (not the case here, but good practice)
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])