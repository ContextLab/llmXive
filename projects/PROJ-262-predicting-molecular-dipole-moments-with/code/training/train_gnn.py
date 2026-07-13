from __future__ import annotations

import argparse
import csv
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Project imports based on API surface
from models.schnet_gnn import SchNetGNN
from training.evaluate import rmse, mae
from training.save_checkpoints import save_gnn_checkpoint
from training.split_data import get_train_test_splits
from training.evaluate import mae, rmse
from utils.reproducibility import set_seed
from utils.pipeline_time_limit import time_limit
from utils.cpu_constraint import cpu_limit
from utils.memory_constraint import memory_limit

# Constants
RESULTS_DIR = Path("results")
CHECKPOINTS_DIR = Path("data/checkpoints")
PROCESSED_DATA_DIR = Path("data/processed")
NUM_SEEDS = 5
NUM_EPOCHS = 50
EARLY_STOPPING_PATIENCE = 10
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
HIDDEN_DIM = 64
NUM_LAYERS = 3
CHECKPOINT_DIR = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/checkpoints")
METRICS_OUTPUT = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/results/metrics.csv")
DATA_PATH_3D = Path("projects/PROJ-262-predicting-molecular-dipole-moments-with/data/processed/features_3d.parquet")


class DipoleDataset(Dataset):
    """Dataset wrapper for dipole moment prediction."""

    def __init__(self, features: np.ndarray, targets: np.ndarray):
        self.features = features
        self.targets = targets

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        x = torch.tensor(self.features[idx], dtype=torch.float32)
        y = torch.tensor(self.targets[idx], dtype=torch.float32)
        return {"x": x, "y": y}


def collate_fn(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """Collate function for DataLoader."""
    x_list = [item["x"] for item in batch]
    y_list = [item["y"] for item in batch]
    return {
        "x": torch.stack(x_list),
        "y": torch.stack(y_list)
    }

def load_processed_data(seed: int) -> Tuple[List[Dict], List[np.ndarray], List[float]]:
    """Load processed data for a specific seed."""
    # Load molecules
    molecules_path = PROCESSED_DATA_DIR / "molecules_10k.parquet"
    if not molecules_path.exists():
        raise FileNotFoundError(f"Processed molecules file not found: {molecules_path}")
    
    import pandas as pd
    df_molecules = pd.read_parquet(molecules_path)
    
    # Load 3D features
    features_path = PROCESSED_DATA_DIR / "features_3d.parquet"
    if not features_path.exists():
        raise FileNotFoundError(f"3D features file not found: {features_path}")
    
    df_features = pd.read_parquet(features_path)
    
    # Get dipole values
    dipole_values = df_molecules['dipole'].tolist()
    
    # Get 3D features as numpy arrays
    features_3d = [np.array(f) for f in df_features['features_3d'].tolist()]
    
    # Convert molecules to list of dicts
    molecules = df_molecules.to_dict('records')
    
    return molecules, features_3d, dipole_values

def train_one_seed(seed: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """Train the GNN model for a single seed with early stopping."""
    set_seed(seed)

    # Load data
    if not DATA_PATH_3D.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH_3D}. Run preprocessing first.")
    
    import pandas as pd
    df = pd.read_parquet(DATA_PATH_3D)
    
    # Prepare features and targets
    # Assuming columns: 'features_3d' (list) and 'dipole' (float)
    # We need to flatten features_3d if it's stored as a list in parquet
    features_list = []
    targets_list = []
    
    for _, row in df.iterrows():
        feat = row['features_3d']
        if isinstance(feat, list):
            features_list.append(feat)
        else:
            # Handle potential string representation or other formats
            try:
                features_list.append(list(feat))
            except:
                continue
        targets_list.append(row['dipole'])

    X = np.array(features_list)
    y = np.array(targets_list)

    # Split data
    train_idx, test_idx = get_train_test_splits(len(X), seed=seed)
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    # Create datasets and loaders
    train_dataset = DipoleDataset(X_train, y_train)
    test_dataset = DipoleDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=config["batch_size"], shuffle=False, collate_fn=collate_fn)

    # Initialize model
    device = torch.device("cpu")
    model = SchNetGNN(
        input_dim=X_train.shape[1],
        hidden_dim=config["hidden_dim"],
        num_layers=config["num_layers"],
        output_dim=1
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])
    criterion = nn.MSELoss()

    # Training loop with early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    train_losses = []
    val_losses = []

    for epoch in range(config["epochs"]):
        model.train()
        epoch_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            inputs = batch["x"].to(device)
            targets = batch["y"].to(device)
            
            outputs = model(inputs)
            loss = criterion(outputs.squeeze(), targets)
            
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        train_losses.append(epoch_loss / len(train_loader))

        # Validation
        model.eval()
        val_loss = 0.0
        all_preds = []
        all_targets = []
        with torch.no_grad():
            for batch in test_loader:
                inputs = batch["x"].to(device)
                targets = batch["y"].to(device)
                outputs = model(inputs)
                
                loss = criterion(outputs.squeeze(), targets)
                val_loss += loss.item()
                
                all_preds.extend(outputs.squeeze().cpu().numpy())
                all_targets.extend(targets.cpu().numpy())
        
        val_loss /= len(test_loader)
        val_losses.append(val_loss)

        # Calculate metrics
        current_rmse = rmse(all_targets, all_preds)
        current_mae = mae(all_targets, all_preds)

        print(f"Seed {seed}, Epoch {epoch+1}/{config['epochs']}, "
              f"Train Loss: {train_losses[-1]:.4f}, Val Loss: {val_loss:.4f}, "
              f"Val RMSE: {current_rmse:.4f}, Val MAE: {current_mae:.4f}")

        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= config["patience"]:
                print(f"Early stopping triggered at epoch {epoch+1}")
                break

    # Load best model for final evaluation
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    # Final evaluation on test set
    model.eval()
    final_preds = []
    final_targets = []
    with torch.no_grad():
        for batch in test_loader:
            inputs = batch["x"].to(device)
            targets = batch["y"].to(device)
            outputs = model(inputs)
            final_preds.extend(outputs.squeeze().cpu().numpy())
            final_targets.extend(targets.cpu().numpy())

    final_rmse = rmse(final_targets, final_preds)
    final_mae = mae(final_targets, final_preds)

    # Save checkpoint
    checkpoint_path = CHECKPOINT_DIR / f"model_seed_{seed}.pt"
    save_gnn_checkpoint(
        model=model,
        config=config,
        seed=seed,
        path=checkpoint_path,
        metrics={"rmse": final_rmse, "mae": final_mae}
    )

    return {
        "seed": seed,
        "rmse": final_rmse,
        "mae": final_mae,
        "best_val_loss": best_val_loss,
        "epochs_run": len(train_losses)
    }


@time_limit(3600)  # 1 hour limit
@cpu_limit(4)
@memory_limit(8 * 1024**3)  # 8 GB limit
def main():
    """Main entry point for GNN training across multiple seeds."""
    parser = argparse.ArgumentParser(description="Train GNN for dipole prediction")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(1, NUM_SEEDS + 1)),
                        help="List of seeds to run")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS)
    parser.add_argument("--patience", type=int, default=EARLY_STOPPING_PATIENCE)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--hidden_dim", type=int, default=HIDDEN_DIM)
    parser.add_argument("--num_layers", type=int, default=NUM_LAYERS)
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    config = {
        "epochs": args.epochs,
        "patience": args.patience,
        "lr": args.lr,
        "hidden_dim": args.hidden_dim,
        "num_layers": args.num_layers,
        "batch_size": args.batch_size
    }

    # Ensure output directory exists
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    results = []
    rmse_values = []

    print(f"Starting training with seeds: {args.seeds}")
    for seed in args.seeds:
        print(f"\n--- Training with seed {seed} ---")
        try:
            result = train_one_seed(seed, config)
            results.append(result)
            rmse_values.append(result["rmse"])
            
            # Append to metrics CSV immediately
            with open(METRICS_OUTPUT, mode='a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:  # Write header if file is empty
                    writer.writerow(["seed", "model", "mae", "rmse", "rmse_variance"])
                writer.writerow([
                    result["seed"],
                    "gnn",
                    f"{result['mae']:.6f}",
                    f"{result['rmse']:.6f}",
                    ""  # Variance calculated at the end
                ])
        except Exception as e:
            print(f"Error training with seed {seed}: {e}")
            continue

    if not results:
        print("No successful training runs.")
        return

    # Calculate RMSE variance across seeds
    rmse_array = np.array(rmse_values)
    rmse_variance = float(np.var(rmse_array))
    rmse_std = float(np.std(rmse_array))

    print(f"\n--- Summary ---")
    print(f"Completed seeds: {len(results)}")
    print(f"Mean RMSE: {np.mean(rmse_array):.4f}")
    print(f"RMSE Variance: {rmse_variance:.6f}")
    print(f"RMSE Std Dev: {rmse_std:.4f}")

    # Update metrics CSV with variance
    # Re-write the file with variance included
    with open(METRICS_OUTPUT, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "model", "mae", "rmse", "rmse_variance"])
        for r in results:
            writer.writerow([
                r["seed"],
                "gnn",
                f"{r['mae']:.6f}",
                f"{r['rmse']:.6f}",
                f"{rmse_variance:.6f}"
            ])

    print(f"Metrics saved to {METRICS_OUTPUT}")
    print(f"Variance of RMSE across seeds: {rmse_variance:.6f}")

def parse_args():
    parser = argparse.ArgumentParser(description="Train GNN model for dipole prediction")
    parser.add_argument("--num_seeds", type=int, default=NUM_SEEDS, help="Number of random seeds to use")
    parser.add_argument("--epochs", type=int, default=NUM_EPOCHS, help="Number of training epochs")
    parser.add_argument("--patience", type=int, default=EARLY_STOPPING_PATIENCE, help="Early stopping patience")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    NUM_SEEDS = args.num_seeds
    NUM_EPOCHS = args.epochs
    EARLY_STOPPING_PATIENCE = args.patience
    main()