"""
Train a control model on shuffled translation trajectories.

This script implements the Shuffled-Translation Control (T027c) for US2.
It loads the geometry-disjoint training data, randomly shuffles the translation
trajectory sequences to break temporal correlation while preserving marginal
distributions, and trains a lightweight model on this data.
"""

import os
import sys
import random
import gc
import signal
import time
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

# Import shared utilities from sibling modules
from utils.data_utils import compute_checksum, update_checksums
from utils.physics_metrics import load_config

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "train.parquet"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "shuffled_control_model.pt"
LOG_PATH = PROJECT_ROOT / "data" / "processed" / "shuffled_control_log.json"
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"

# Hyperparameters (aligned with train_model.py for fair comparison)
SEED = 42
EPOCHS = 10
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
MAX_SEQ_LEN = 20
HIDDEN_DIM = 32
NUM_HEADS = 2
NUM_LAYERS = 2
DROPOUT = 0.1
TIMEOUT_SECONDS = 3600  # 1 hour timeout

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timed out")

def set_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class StabilityShuffledDataset(Dataset):
    """
    Dataset that loads translation trajectories and labels,
    then shuffles the time dimension of the trajectories to break temporal correlation.
    """

    def __init__(self, data_path: Path, max_seq_len: int = 20):
        if not data_path.exists():
            raise FileNotFoundError(f"Training data not found at {data_path}")

        self.df = pd.read_parquet(data_path)
        self.max_seq_len = max_seq_len

        # Validate required columns
        required_cols = ['translation_trajectory', 'label', 'geometry_id']
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns in data: {missing}")

        # Parse trajectories if stored as string/json
        if self.df['translation_trajectory'].dtype == 'object':
            # Assume list of lists or string representation of list
            def parse_traj(t):
                if isinstance(t, str):
                    try:
                        return json.loads(t)
                    except:
                        return []
                return t

            self.df['translation_trajectory'] = self.df['translation_trajectory'].apply(parse_traj)

        self.labels = self.df['label'].values
        self.geometries = self.df['geometry_id'].values
        self.trajectories = self.df['translation_trajectory'].values

    def __len__(self):
        return len(self.df)

    def _shuffle_trajectory(self, traj: List[List[float]]) -> List[List[float]]:
        """
        Shuffle the time steps of the trajectory.
        Preserves marginal distribution of values but breaks temporal order.
        """
        if not traj:
            return []

        # Convert to numpy for easy shuffling
        arr = np.array(traj)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)

        # Shuffle rows (time steps)
        np.random.shuffle(arr)
        return arr.tolist()

    def __getitem__(self, idx: int):
        traj = self.trajectories[idx]
        label = self.labels[idx]
        geometry_id = self.geometries[idx]

        # Pad or truncate to max_seq_len
        if len(traj) > self.max_seq_len:
            traj = traj[:self.max_seq_len]
        else:
            pad_len = self.max_seq_len - len(traj)
            traj = traj + [[0.0, 0.0, 0.0]] * pad_len  # Zero padding

        # SHUFFLE: Break temporal correlation
        shuffled_traj = self._shuffle_trajectory(traj)

        # Convert to tensor
        x = torch.tensor(shuffled_traj, dtype=torch.float32)
        y = torch.tensor(label, dtype=torch.float32)

        return x, y, geometry_id

def collate_fn(batch: List[Tuple[torch.Tensor, torch.Tensor, int]]):
    """Collate function for DataLoader."""
    xs, ys, geoms = zip(*batch)
    x_batch = torch.stack(xs)
    y_batch = torch.stack(ys)
    return x_batch, y_batch, list(geoms)

# Simple MLP model for the control experiment (lightweight, no temporal attention)
class ShuffledControlModel(nn.Module):
    """
    A simple MLP that treats shuffled time steps as independent features.
    This serves as the control to test if temporal structure is necessary.
    """

    def __init__(self, input_dim: int = 3, seq_len: int = 20, hidden_dim: int = 32):
        super().__init__()
        self.flatten_dim = input_dim * seq_len
        self.net = nn.Sequential(
            nn.Linear(self.flatten_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # x shape: (batch, seq_len, 3) -> flatten to (batch, seq_len * 3)
        batch_size = x.size(0)
        x = x.view(batch_size, -1)
        return self.net(x)

def train_epoch(model: nn.Module, loader: DataLoader, optimizer: optim.Optimizer,
                criterion: nn.Module, device: torch.device) -> float:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for x_batch, y_batch, _ in loader:
        x_batch, y_batch = x_batch.to(device), y_batch.to(device)

        optimizer.zero_grad()
        outputs = model(x_batch)
        loss = criterion(outputs.squeeze(), y_batch)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        predictions = (outputs.squeeze() > 0.5).float()
        correct += (predictions == y_batch).sum().item()
        total += y_batch.size(0)

    return total_loss / len(loader), correct / total

def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module,
             device: torch.device) -> Tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for x_batch, y_batch, _ in loader:
            x_batch, y_batch = x_batch.to(device), y_batch.to(device)
            outputs = model(x_batch)
            loss = criterion(outputs.squeeze(), y_batch)

            total_loss += loss.item()
            predictions = (outputs.squeeze() > 0.5).float()
            correct += (predictions == y_batch).sum().item()
            total += y_batch.size(0)

    return total_loss / len(loader), correct / total

def main():
    print(f"[INFO] Starting Shuffled-Translation Control Training (T027c)")
    print(f"[INFO] Loading config from {CONFIG_PATH}")

    # Load configuration
    try:
        config = load_config(CONFIG_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        sys.exit(1)

    # Set up timeout
    set_timeout(TIMEOUT_SECONDS)

    try:
        # Set seeds for reproducibility
        set_seed(SEED)

        # Device setup (CPU only as per project constraints)
        device = torch.device('cpu')
        print(f"[INFO] Using device: {device}")

        # Load dataset
        print(f"[INFO] Loading training data from {DATA_PATH}")
        if not DATA_PATH.exists():
            print(f"[ERROR] Training data not found at {DATA_PATH}. Please run data generation first.")
            sys.exit(1)

        dataset = StabilityShuffledDataset(DATA_PATH, max_seq_len=MAX_SEQ_LEN)
        print(f"[INFO] Loaded {len(dataset)} samples with shuffled trajectories")

        # Split into train/val (80/20)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        train_ds, val_ds = torch.utils.data.random_split(
            dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(SEED)
        )

        train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                                  collate_fn=collate_fn, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False,
                                collate_fn=collate_fn, num_workers=0)

        # Initialize model
        print(f"[INFO] Initializing ShuffledControlModel...")
        model = ShuffledControlModel(
            input_dim=3,
            seq_len=MAX_SEQ_LEN,
            hidden_dim=HIDDEN_DIM
        ).to(device)

        total_params = sum(p.numel() for p in model.parameters())
        print(f"[INFO] Model parameters: {total_params:,}")

        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)

        # Training loop
        print(f"[INFO] Starting training for {EPOCHS} epochs...")
        best_val_acc = 0.0

        for epoch in range(EPOCHS):
            train_loss, train_acc = train_epoch(model, train_loader, optimizer, criterion, device)
            val_loss, val_acc = evaluate(model, val_loader, criterion, device)
            scheduler.step()

            print(f"[Epoch {epoch+1}/{EPOCHS}] "
                  f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | "
                  f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_acc': val_acc,
                    'config': {
                        'seq_len': MAX_SEQ_LEN,
                        'hidden_dim': HIDDEN_DIM,
                        'lr': LEARNING_RATE,
                        'batch_size': BATCH_SIZE
                    }
                }, MODEL_OUTPUT_PATH)
                print(f"[INFO] Saved best model to {MODEL_OUTPUT_PATH}")

        print(f"[INFO] Training completed. Best validation accuracy: {best_val_acc:.4f}")

        # Final validation
        reset_timeout()
        print(f"[INFO] Final model saved to {MODEL_OUTPUT_PATH}")

        # Log results
        log_data = {
            'task_id': 'T027c',
            'model_type': 'ShuffledControlModel',
            'total_parameters': total_params,
            'epochs': EPOCHS,
            'best_val_accuracy': best_val_acc,
            'final_train_accuracy': train_acc,
            'final_val_accuracy': val_acc,
            'data_path': str(DATA_PATH),
            'model_path': str(MODEL_OUTPUT_PATH),
            'shuffled': True,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(LOG_PATH, 'w') as f:
            json.dump(log_data, f, indent=2)

        # Update checksums
        if MODEL_OUTPUT_PATH.exists():
            checksum = compute_checksum(MODEL_OUTPUT_PATH)
            update_checksums(MODEL_OUTPUT_PATH, checksum, "shuffled_control_model")
            print(f"[INFO] Updated checksums.json with model checksum: {checksum}")

        print(f"[SUCCESS] T027c completed successfully.")

    except TimeoutError:
        print("[ERROR] Training timed out!")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
