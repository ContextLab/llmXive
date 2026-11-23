"""
Train a geometry-only baseline model.
Uses only 'initial_object_bounds' to predict stability.
Saves the model to data/processed/baseline_model.pt.
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
from typing import Tuple, List, Optional, Dict, Any

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

# --------------------------------------------------------------------------
# Configuration & Paths
# --------------------------------------------------------------------------

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# --------------------------------------------------------------------------
# Timeout Handling (matches train_model.py pattern)
# --------------------------------------------------------------------------

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timeout exceeded")

def set_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

# --------------------------------------------------------------------------
# Dataset
# --------------------------------------------------------------------------

class GeometryOnlyDataset(Dataset):
    """
    Dataset that loads only 'initial_object_bounds' and 'stability_label'.
    """
    def __init__(self, parquet_path: str):
        self.parquet_path = parquet_path
        # Load data
        self.df = pd.read_parquet(parquet_path)
        
        # Validate columns
        required_cols = ['initial_object_bounds', 'stability_label']
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Missing required columns in {parquet_path}: {missing}")

        # Flatten bounds: (x_min, y_min, z_min, x_max, y_max, z_max) -> 6 features
        # Assuming initial_object_bounds is a list/array of 6 floats per row
        self.X = []
        for _, row in self.df.iterrows():
            bounds = row['initial_object_bounds']
            if isinstance(bounds, (list, np.ndarray)):
                # Ensure it's a flat list of 6
                flat = list(bounds)
                if len(flat) != 6:
                    # If it's nested or different shape, flatten and take first 6 or pad
                    flat = [float(x) for x in bounds]
                    if len(flat) != 6:
                        raise ValueError(f"Expected 6 bounds, got {len(flat)}")
                self.X.append(flat)
            else:
                raise ValueError(f"Invalid bounds format: {type(bounds)}")
        
        self.X = np.array(self.X, dtype=np.float32)
        self.y = self.df['stability_label'].values.astype(np.int64)
        print(f"Loaded {len(self.y)} samples for geometry-only baseline.")

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        x = torch.tensor(self.X[idx], dtype=torch.float32)
        y = torch.tensor(self.y[idx], dtype=torch.float32)
        return x, y

def collate_fn(batch):
    """Standard collate function."""
    xs, ys = zip(*batch)
    return torch.stack(xs), torch.stack(ys)

# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

class GeometryBaselineModel(nn.Module):
    """
    Simple MLP for geometry-only prediction.
    Input: 6 floats (bounds)
    Output: 1 float (logit)
    """
    def __init__(self, input_dim: int = 6, hidden_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(self, x):
        return self.net(x)

# --------------------------------------------------------------------------
# Training Utilities
# --------------------------------------------------------------------------

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def train_epoch(model: nn.Module, loader: DataLoader, optimizer: optim.Optimizer, criterion: nn.Module, device: torch.device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        
        optimizer.zero_grad()
        logits = model(x).squeeze()
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        preds = (torch.sigmoid(logits) > 0.5).float()
        correct += (preds == y).sum().item()
        total += y.size(0)
    
    return total_loss / len(loader), correct / total

def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> Tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            logits = model(x).squeeze()
            loss = criterion(logits, y)
            
            total_loss += loss.item()
            preds = (torch.sigmoid(logits) > 0.5).float()
            correct += (preds == y).sum().item()
            total += y.size(0)
    
    return total_loss / len(loader), correct / total

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    # Configuration
    config = load_config()
    data_path = config.get('data', {}).get('processed_train', 'data/processed/train.parquet')
    output_path = config.get('data', {}).get('processed_baseline_model', 'data/processed/baseline_model.pt')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Loading data from: {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found at {data_path}. Run T016c first.")
    
    # Setup
    set_seed(42)
    device = torch.device("cpu")  # CPU-only constraint
    print(f"Using device: {device}")
    
    # Dataset & Loader
    dataset = GeometryOnlyDataset(data_path)
    loader = DataLoader(dataset, batch_size=64, shuffle=True, collate_fn=collate_fn)
    
    # Model
    model = GeometryBaselineModel(input_dim=6, hidden_dim=32).to(device)
    param_count = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {param_count}")
    
    # Training setup
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCEWithLogitsLoss()
    
    epochs = config.get('training', {}).get('epochs', 50)
    timeout_seconds = config.get('training', {}).get('timeout_seconds', 3600)
    
    print(f"Training for {epochs} epochs...")
    
    try:
        set_timeout(timeout_seconds)
        best_acc = 0.0
        for epoch in range(epochs):
            train_loss, train_acc = train_epoch(model, loader, optimizer, criterion, device)
            val_loss, val_acc = evaluate(model, loader, criterion, device)
            
            if val_acc > best_acc:
                best_acc = val_acc
                # Save best model
                torch.save({
                    'model_state_dict': model.state_dict(),
                    'param_count': param_count,
                    'epoch': epoch,
                    'accuracy': val_acc
                }, output_path)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}")
        
        reset_timeout()
        print(f"Training complete. Best validation accuracy: {best_acc:.4f}")
        print(f"Model saved to: {output_path}")
        
        # Verify file exists and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print("SUCCESS: Baseline model saved and verified.")
        else:
            raise RuntimeError("Model file was not saved correctly.")
            
    except TimeoutError as e:
        print(f"TRAINING TIMEOUT: {e}")
        reset_timeout()
        sys.exit(1)
    except Exception as e:
        print(f"TRAINING FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
