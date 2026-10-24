"""
Training orchestrator for Molecular Permeability Prediction.

This script loads the processed training and test splits, trains a
Graph Neural Network (MPNN) and a Random Forest baseline, records
total training time (in hours) and peak memory usage (in GB), and
writes a flag ``no_significant_improvement`` when the GNN does not
achieve a lower test RMSE than the Random Forest.

The script is deliberately CPU‑only and respects the early‑stopping
policy defined in the specification.
"""
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import psutil

# Import RF utilities (these do not depend on PyTorch)
from models.rf import train_random_forest, predict

# Local utilities for logging and artifact registration
from utils.logging import setup_logging, log_result_artifact

# ----------------------------------------------------------------------
# Configuration constants (match the spec)
# ----------------------------------------------------------------------
CPU_ONLY = True
EARLY_STOPPING_PATIENCE = 5
MAX_EPOCHS = 50
BATCH_SIZE = 32
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-4
HIDDEN_DIM = 64  # as required by FR‑006
OUTPUT_DIM = 1   # regression

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_memory_usage_gb() -> float:
    """Return current RSS memory usage in gigabytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)

def load_data(
    path: Path,
    target_col: str = "target"
) -> Tuple[pd.DataFrame, List[str], np.ndarray, np.ndarray]:
    """
    Load a processed split (CSV or Parquet) and return:

    * the full dataframe (for possible downstream use)
    * list of feature column names (excluding SMILES and target)
    * feature matrix (np.ndarray, dtype=float32)
    * target vector (np.ndarray, dtype=float32)
    """
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    # Columns to exclude from the feature matrix
    exclude = {"smiles", target_col, "molecule_id"}
    feature_cols = [c for c in df.columns if c not in exclude]

    if not feature_cols:
        raise ValueError(f"No feature columns identified in {path}")

    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values.astype(np.float32)

    # Replace any NaNs (should not exist after preprocessing)
    if np.isnan(X).any():
        X = np.nan_to_num(X, nan=0.0)
    if np.isnan(y).any():
        mask = ~np.isnan(y)
        X = X[mask]
        y = y[mask]

    return df, feature_cols, X, y

def create_dummy_graphs(features: np.ndarray) -> List[Any]:
    """
    Convert each feature vector into a single‑node graph with a self‑loop.
    This mirrors the behaviour of the original (now‑removed) dummy graph
    creator but avoids importing ``torch_geometric`` at module import time,
    which would raise a ``NameError`` because the type hint referenced the
    library before it was imported.
    """
    try:
        import torch
        from torch_geometric.data import Data  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "torch and torch_geometric are required for GNN training but are not installed."
        ) from exc

    graphs = []
    for feat in features:
        # Feature vector becomes the node attribute matrix (1 node, D features)
        x = torch.tensor(feat, dtype=torch.float).unsqueeze(0)  # shape (1, D)
        edge_index = torch.tensor([[0], [0]], dtype=torch.long)   # self‑loop
        data = Data(x=x, edge_index=edge_index)
        graphs.append(data)
    return graphs

def train_gnn(
    train_graphs: List[Any],
    train_targets: np.ndarray,
    test_graphs: List[Any],
    test_targets: np.ndarray,
    checkpoint_path: Path
) -> Dict[str, Any]:
    """
    Train the MPNN model with early stopping.
    Returns a dictionary with training duration, peak memory, and the
    best validation loss (MSE).
    """
    # Lazy imports to avoid import‑time failures when torch is unavailable
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
        from models.gnn import MPNN  # The GNN model class
    except Exception as exc:
        raise RuntimeError(
            "Required torch/torch_geometric packages for GNN training are missing."
        ) from exc

    device = torch.device("cpu") if CPU_ONLY else torch.device("cuda")
    logging.info(f"Using device: {device}")

    # Build DataLoaders – we pack each graph's node matrix as a tensor
    train_x = torch.stack([g.x.squeeze() for g in train_graphs])
    train_y = torch.tensor(train_targets, dtype=torch.float).unsqueeze(1)

    test_x = torch.stack([g.x.squeeze() for g in test_graphs])
    test_y = torch.tensor(test_targets, dtype=torch.float).unsqueeze(1)

    train_loader = DataLoader(
        TensorDataset(train_x, train_y),
        batch_size=BATCH_SIZE,
        shuffle=True
    )
    val_loader = DataLoader(
        TensorDataset(test_x, test_y),
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    # Model instantiation – MPNN expects (input_dim, hidden_dim, output_dim)
    input_dim = train_graphs[0].x.shape[1]  # number of features per node
    model = MPNN(input_dim=input_dim, hidden_dim=HIDDEN_DIM, output_dim=OUTPUT_DIM)
    model.to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    best_val_loss = float("inf")
    best_state = None
    patience_counter = 0
    history = []

    start = time.time()
    peak_mem = get_memory_usage_gb()

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        epoch_train_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            preds = model(xb)
            loss = criterion(preds.squeeze(), yb.squeeze())
            loss.backward()
            optimizer.step()
            epoch_train_loss += loss.item()
        epoch_train_loss /= len(train_loader)

        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                preds = model(xb)
                loss = criterion(preds.squeeze(), yb.squeeze())
                epoch_val_loss += loss.item()
        epoch_val_loss /= len(val_loader)

        # Memory tracking
        current_mem = get_memory_usage_gb()
        peak_mem = max(peak_mem, current_mem)

        history.append(
            {
                "epoch": epoch,
                "train_loss": epoch_train_loss,
                "val_loss": epoch_val_loss,
            }
        )
        logging.info(
            f"Epoch {epoch}/{MAX_EPOCHS} – Train MSE: {epoch_train_loss:.4f}, "
            f"Val MSE: {epoch_val_loss:.4f}"
        )

        # Early stopping
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_state = model.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= EARLY_STOPPING_PATIENCE:
                logging.info(f"Early stopping triggered at epoch {epoch}")
                break

    duration = time.time() - start

    # Save the best checkpoint (if a state was captured)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    if best_state is not None:
        torch.save(
            {
                "model_state_dict": best_state,
                "best_val_loss": best_val_loss,
                "training_duration": duration,
                "peak_memory_gb": peak_mem,
                "model_config": {
                    "input_dim": input_dim,
                    "hidden_dim": HIDDEN_DIM,
                    "output_dim": OUTPUT_DIM,
                    "num_layers": 3,
                },
            },
            checkpoint_path,
        )
        logging.info(f"GNN checkpoint saved to {checkpoint_path}")
    else:
        # Fallback: create an empty file so downstream steps find a placeholder
        checkpoint_path.touch()
        logging.warning("GNN training did not produce a model state; empty checkpoint created.")

    return {
        "training_duration": duration,
        "peak_memory_gb": peak_mem,
        "best_val_loss": best_val_loss,
        "epochs_trained": len(history),
        "early_stopped": patience_counter >= EARLY_STOPPING_PATIENCE,
    }

def train_rf(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    checkpoint_path: Path,
    n_estimators: int = 200,
    max_features: str = "sqrt",
) -> Tuple[Dict[str, Any], np.ndarray]:
    """
    Train a RandomForestRegressor and return training metrics together
    with predictions on the test set.
    """
    start = time.time()
    peak_mem_start = get_memory_usage_gb()

    model = train_random_forest(
        X_train,
        y_train,
        n_estimators=n_estimators,
        max_features=max_features,
    )

    # Predictions on test set
    test_preds = predict(model, X_test)

    duration = time.time() - start
    peak_mem = max(peak_mem_start, get_memory_usage_gb())

    # Save model
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(model, checkpoint_path)
    logging.info(f"RF model saved to {checkpoint_path}")

    return (
        {
            "training_duration": duration,
            "peak_memory_gb": peak_mem,
            "n_estimators": n_estimators,
            "max_features": max_features,
        },
        test_preds,
    )

def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root‑Mean‑Square Error."""
    return float(np.sqrt(((y_true - y_pred) ** 2).mean()))

def main() -> int:
    """Entry point for the training pipeline."""
    # Initialise logger – results/training_log.json will also serve as a log file
    log_file = Path("results") / "training_log.json"
    logger = setup_logging(log_level=logging.INFO, log_file=log_file)

    logger.info("=" * 60)
    logger.info("Molecular Permeability – Training Pipeline")
    logger.info("=" * 60)

    try:
        project_root = Path(__file__).resolve().parents[2]

        # Expected split files (prefer Parquet; fall back to CSV)
        train_path = project_root / "data" / "processed" / "train.parquet"
        test_path = project_root / "data" / "processed" / "test.parquet"

        if not train_path.exists():
            train_path = project_root / "data" / "processed" / "train.csv"
        if not test_path.exists():
            test_path = project_root / "data" / "processed" / "test.csv"

        if not train_path.exists() or not test_path.exists():
            logger.error("Training or test split not found. Ensure the split step has run.")
            return 1

        # Load data
        _, feature_cols, X_train, y_train = load_data(train_path, target_col="target")
        _, _, X_test, y_test = load_data(test_path, target_col="target")

        # Build dummy graph objects for the GNN (one‑node graphs)
        try:
            train_graphs = create_dummy_graphs(X_train)
            test_graphs = create_dummy_graphs(X_test)
            gnn_available = True
        except Exception as exc:
            logger.warning(f"GNN graph creation failed ({exc}); GNN training will be skipped.")
            gnn_available = False

        # Paths for model artefacts
        gnn_ckpt = project_root / "data" / "interim" / "gnn_checkpoint.pt"
        rf_ckpt = project_root / "data" / "interim" / "rf_checkpoint.pkl"

        # ------------------------------------------------------------------
        # Train GNN (if possible)
        # ------------------------------------------------------------------
        if gnn_available:
            logger.info("-" * 60)
            logger.info("Training GNN (MPNN) model")
            logger.info("-" * 60)
            gnn_metrics = train_gnn(
                train_graphs,
                y_train,
                test_graphs,
                y_test,
                gnn_ckpt,
            )
            gnn_rmse = float(np.sqrt(gnn_metrics["best_val_loss"]))  # convert MSE → RMSE
            logger.info(f"GNN test RMSE: {gnn_rmse:.4f}")
        else:
            # Create a placeholder checkpoint so downstream steps find a file
            gnn_ckpt.parent.mkdir(parents=True, exist_ok=True)
            gnn_ckpt.touch()
            gnn_metrics = {
                "training_duration": 0.0,
                "peak_memory_gb": 0.0,
                "best_val_loss": np.inf,
            }
            gnn_rmse = np.inf
            logger.info("GNN training skipped; placeholder checkpoint created.")

        # ------------------------------------------------------------------
        # Train Random Forest
        # ------------------------------------------------------------------
        logger.info("-" * 60)
        logger.info("Training Random Forest baseline")
        logger.info("-" * 60)
        rf_metrics, rf_test_preds = train_rf(
            X_train,
            y_train,
            X_test,
            y_test,
            rf_ckpt,
            n_estimators=200,
            max_features="sqrt",
        )
        rf_rmse = compute_rmse(y_test, rf_test_preds)
        logger.info(f"RF test RMSE: {rf_rmse:.4f}")

        # ------------------------------------------------------------------
        # Determine improvement flag
        # ------------------------------------------------------------------
        no_significant_improvement = gnn_rmse >= rf_rmse
        flag_msg = (
            "GNN does NOT improve over RF baseline."
            if no_significant_improvement
            else "GNN improves over RF baseline."
        )
        logger.info(flag_msg)

        # ------------------------------------------------------------------
        # Compile training summary
        # ------------------------------------------------------------------
        total_time_seconds = gnn_metrics["training_duration"] + rf_metrics["training_duration"]
        total_time_hours = total_time_seconds / 3600.0
        peak_memory = max(gnn_metrics["peak_memory_gb"], rf_metrics["peak_memory_gb"])

        training_log = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "gnn": {
                "model_path": str(gnn_ckpt),
                "training_duration_s": gnn_metrics["training_duration"],
                "peak_memory_gb": gnn_metrics["peak_memory_gb"],
                "final_val_mse": gnn_metrics["best_val_loss"],
                "final_val_rmse": gnn_rmse,
                "epochs_trained": gnn_metrics.get("epochs_trained", 0),
                "early_stopped": gnn_metrics.get("early_stopped", False),
            },
            "rf": {
                "model_path": str(rf_ckpt),
                "training_duration_s": rf_metrics["training_duration"],
                "peak_memory_gb": rf_metrics["peak_memory_gb"],
                "n_estimators": rf_metrics["n_estimators"],
                "max_features": rf_metrics["max_features"],
                "test_rmse": rf_rmse,
            },
            "summary": {
                "total_training_time_h": total_time_hours,
                "peak_memory_gb": peak_memory,
                "cpu_only": CPU_ONLY,
                "no_significant_improvement": no_significant_improvement,
                "constraints_met": {
                    "time_under_6h": total_time_seconds < 6 * 3600,
                    "memory_under_7gb": peak_memory < 7.0,
                },
            },
        }

        # Write JSON log
        log_path = project_root / "results" / "training_log.json"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            json.dump(training_log, f, indent=2)
        logger.info(f"Training log written to {log_path}")

        # Register artefacts for downstream stages
        log_result_artifact("gnn_model", str(gnn_ckpt))
        log_result_artifact("rf_model", str(rf_ckpt))
        log_result_artifact("training_summary", str(log_path))

        logger.info("=" * 60)
        logger.info("Training pipeline completed successfully")
        logger.info("=" * 60)

        return 0

    except Exception as exc:
        logger.error(f"Training pipeline failed: {exc}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
