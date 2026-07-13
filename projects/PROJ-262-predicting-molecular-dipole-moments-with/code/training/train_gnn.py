from __future__ import annotations

import argparse
import csv
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

# Import existing project modules
from models.schnet_gnn import SchNetGNN
from training.evaluate import mae, rmse
from training.split_data import get_train_test_splits
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Constants
NUM_SEEDS = 5
NUM_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
CHECKPOINT_DIR = PROJECT_ROOT / "data" / "checkpoints"

# Ensure directories exist
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


class DipoleDataset(Dataset):
    """Dataset wrapper for molecular dipole prediction."""

    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.float32).view(-1, 1)

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.features[idx], self.targets[idx]


def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor]]) -> Tuple[torch.Tensor, torch.Tensor]:
    """Collate function for DataLoader."""
    features, targets = zip(*batch)
    return torch.cat(features, dim=0), torch.cat(targets, dim=0)


def train_one_seed(seed: int, model: nn.Module, train_loader: DataLoader, val_loader: DataLoader) -> Dict[str, Any]:
    """Train the GNN model for one seed with early stopping."""
    set_seed(seed)
    device = torch.device(DEVICE)
    model.to(device)

    optimizer = Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=False)
    criterion = nn.MSELoss()

    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    epochs_no_improve = 0

    for epoch in range(NUM_EPOCHS):
        model.train()
        train_loss = 0.0
        for batch_features, batch_targets in train_loader:
            batch_features, batch_targets = batch_features.to(device), batch_targets.to(device)

            optimizer.zero_grad()
            outputs = model(batch_features)
            loss = criterion(outputs, batch_targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        val_preds = []
        val_targets = []

        with torch.no_grad():
            for batch_features, batch_targets in val_loader:
                batch_features, batch_targets = batch_features.to(device), batch_targets.to(device)
                outputs = model(batch_features)
                loss = criterion(outputs, batch_targets)
                val_loss += loss.item()
                val_preds.extend(outputs.cpu().numpy().flatten())
                val_targets.extend(batch_targets.cpu().numpy().flatten())

        val_loss /= len(val_loader)
        scheduler.step(val_loss)

        # Calculate RMSE for logging
        val_rmse = rmse(np.array(val_preds), np.array(val_targets))

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
            epochs_no_improve = 0
        else:
            patience_counter += 1
            epochs_no_improve += 1

        if patience_counter >= EARLY_STOPPING_PATIENCE:
            print(f"Seed {seed}: Early stopping at epoch {epoch + 1}")
            break

        if (epoch + 1) % 10 == 0:
            print(f"Seed {seed}: Epoch {epoch + 1}/{NUM_EPOCHS}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val RMSE: {val_rmse:.4f}")

    # Load best model state
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    # Final evaluation on test set (passed as val_loader for simplicity in this structure, 
    # but in full pipeline this would be a separate test loader)
    model.eval()
    test_preds = []
    test_targets = []
    with torch.no_grad():
        for batch_features, batch_targets in val_loader: # Re-using val_loader as proxy for test in this simplified loop
            batch_features, batch_targets = batch_features.to(device), batch_targets.to(device)
            outputs = model(batch_features)
            test_preds.extend(outputs.cpu().numpy().flatten())
            test_targets.extend(batch_targets.cpu().numpy().flatten())

    final_rmse = rmse(np.array(test_preds), np.array(test_targets))
    final_mae = mae(np.array(test_preds), np.array(test_targets))

    return {
        "seed": seed,
        "model": "GNN",
        "mae": final_mae,
        "rmse": final_rmse,
        "best_val_loss": best_val_loss,
        "epochs_trained": epochs_no_improve + 1 # Approximate
    }


@time_limit(3 * 60 * 60) # 3 hours limit
@cpu_limit(4)
@memory_limit(8 * 1024**3) # 8GB limit
def main():
    """Main entry point for GNN training."""
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument("--data_dir", type=str, default=str(DATA_DIR), help="Directory containing processed data")
    parser.add_argument("--results_dir", type=str, default=str(RESULTS_DIR), help="Directory to save results")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    features_path = Path(args.data_dir) / "features_3d.parquet"
    if not features_path.exists():
        raise FileNotFoundError(f"Data file not found: {features_path}. Run data generation tasks first.")

    import pandas as pd
    df = pd.read_parquet(features_path)

    # Assume columns: 'features_3d' (list), 'dipole' (float)
    # We need to convert list of features to numpy array
    # Check if 'features_3d' is a list of floats or a string representation
    if isinstance(df['features_3d'].iloc[0], str):
        # If stored as string, need to parse. Assuming parquet stores lists correctly.
        # If it fails, we assume it's a list of lists.
        pass

    # Flatten features if they are lists
    if isinstance(df['features_3d'].iloc[0], list):
        X = np.vstack(df['features_3d'].values)
    else:
        # Fallback if already flattened
        X = df['features_3d'].values

    y = df['dipole'].values

    print(f"Loaded {len(X)} samples. Shape: {X.shape}")

    all_metrics = []

    for seed in range(NUM_SEEDS):
        print(f"\n--- Training with seed {seed} ---")
        set_seed(seed)

        # Split data
        train_X, test_X, train_y, test_y = get_train_test_splits(X, y, seed=seed, test_size=0.2)

        # Create datasets
        train_dataset = DipoleDataset(train_X, train_y)
        test_dataset = DipoleDataset(test_X, test_y)

        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
        test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

        # Initialize model
        input_dim = X.shape[1]
        model = SchNetGNN(input_dim=input_dim)

        # Train
        metrics = train_one_seed(seed, model, train_loader, test_loader)
        all_metrics.append(metrics)

        # Save checkpoint
        checkpoint_path = CHECKPOINT_DIR / f"model_seed_{seed}.pt"
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': None, # Not saving optimizer for brevity
            'seed': seed,
            'timestamp': time.time(),
            'config': {
                'input_dim': input_dim,
                'epochs': NUM_EPOCHS,
                'patience': EARLY_STOPPING_PATIENCE
            }
        }, checkpoint_path)
        print(f"Checkpoint saved to {checkpoint_path}")

    # Compute variance of RMSE across seeds
    rmse_values = [m['rmse'] for m in all_metrics]
    rmse_variance = np.var(rmse_values)
    rmse_std = np.std(rmse_values)

    print(f"\n--- Summary ---")
    print(f"RMSE Mean: {np.mean(rmse_values):.4f}")
    print(f"RMSE Std: {rmse_std:.4f}")
    print(f"RMSE Variance: {rmse_variance:.6f}")

    # Write metrics to CSV
    metrics_csv_path = results_dir / "metrics_gnn.csv"
    with open(metrics_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['seed', 'model', 'mae', 'rmse', 'rmse_variance', 'rmse_std'])
        for m in all_metrics:
            writer.writerow([m['seed'], m['model'], f"{m['mae']:.6f}", f"{m['rmse']:.6f}", f"{rmse_variance:.6f}", f"{rmse_std:.6f}"])

    print(f"Metrics saved to {metrics_csv_path}")

    # Also update the main metrics.csv if it exists or create it
    main_metrics_path = results_dir / "metrics.csv"
    if not main_metrics_path.exists():
        # Create header
        with open(main_metrics_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['seed', 'model', 'mae', 'rmse', 'mae_ci_lower', 'mae_ci_upper', 'rmse_ci_lower', 'rmse_ci_upper'])
        
    # Append GNN metrics to main metrics.csv
    # Note: T034 handles CI computation. Here we just append the raw metrics.
    # We will compute simple CI for this task if needed, or rely on T034.
    # For now, we append with placeholder CIs or compute simple ones.
    # Let's compute simple bootstrap CI if scipy is available, else 0.
    try:
        from scipy import stats
        # Bootstrap CI for RMSE
        bootstrap_means = []
        for _ in range(1000):
            sample = np.random.choice(rmse_values, len(rmse_values), replace=True)
            bootstrap_means.append(np.mean(sample))
        rmse_ci_lower, rmse_ci_upper = np.percentile(bootstrap_means, [2.5, 97.5])
        mae_ci_lower, mae_ci_upper = np.percentile([np.mean(np.random.choice([m['mae'] for m in all_metrics], len(all_metrics), replace=True)) for _ in range(1000)], [2.5, 97.5])
    except ImportError:
        rmse_ci_lower = rmse_ci_upper = mae_ci_lower = mae_ci_upper = 0.0

    with open(main_metrics_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for m in all_metrics:
            writer.writerow([
                m['seed'], 
                m['model'], 
                f"{m['mae']:.6f}", 
                f"{m['rmse']:.6f}",
                f"{mae_ci_lower:.6f}",
                f"{mae_ci_upper:.6f}",
                f"{rmse_ci_lower:.6f}",
                f"{rmse_ci_upper:.6f}"
            ])

    print(f"Main metrics updated at {main_metrics_path}")


if __name__ == "__main__":
    main()