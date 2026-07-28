"""
Train a Geometry-Only Baseline model.

This script trains a lightweight model (Logistic Regression via PyTorch) 
using ONLY the `initial_object_bounds` feature to predict stability.

Output: data/processed/baseline_model.pt
"""
import os
import sys
import random
import gc
import signal
import time
import math
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np

# Ensure imports work from code/ directory context
# We assume this file is run as `python code/train_baseline.py`
# or installed in an environment where `code` is on PYTHONPATH.
# To be safe for local execution, we add parent to path if needed.
if __name__ == "__main__":
    # Add current directory to path to allow imports of sibling modules
    # if run as script, but rely on environment for standard imports.
    pass

# --- Configuration & Constants ---
RANDOM_SEED = 42
TRAIN_PATH = "data/processed/train.parquet"
TEST_PATH = "data/processed/test.parquet"
OUTPUT_MODEL_PATH = "data/processed/baseline_model.pt"
DEVICE = torch.device("cpu") # Enforce CPU only per project constraints
BATCH_SIZE = 128
EPOCHS = 20
LEARNING_RATE = 0.01

# --- Timeout Handling (Consistent with train_model.py) ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timed out")

def set_timeout(seconds):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

# --- Dataset Class ---
class GeometryOnlyDataset(Dataset):
    """
    Dataset that loads ONLY initial_object_bounds as features.
    
    The raw data contains columns like:
    - initial_object_bounds: A list/array of 6 floats (min_x, min_y, min_z, max_x, max_y, max_z)
    - stability: The target label (0 or 1)
    """
    def __init__(self, parquet_path):
        self.df = pd.read_parquet(parquet_path)
        
        # Extract features: initial_object_bounds
        # Assuming the column contains lists or arrays of 6 floats.
        # We flatten them to shape (N, 6).
        if 'initial_object_bounds' not in self.df.columns:
            raise ValueError(f"Column 'initial_object_bounds' not found in {parquet_path}")
        
        # Convert list of lists to numpy array
        # Handle potential nested list structure
        bounds_list = self.df['initial_object_bounds'].tolist()
        self.features = np.array(bounds_list, dtype=np.float32)
        
        if self.features.shape[1] != 6:
            raise ValueError(f"Expected 6 bounds values, got {self.features.shape[1]}")

        # Extract target
        if 'stability' not in self.df.columns:
            raise ValueError(f"Column 'stability' not found in {parquet_path}")
        self.targets = self.df['stability'].values.astype(np.float32)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        return torch.tensor(self.features[idx]), torch.tensor(self.targets[idx])

# --- Model Definition ---
class GeometryBaselineModel(nn.Module):
    """
    A simple MLP for geometry-only baseline.
    Input: 6 values (min/max x,y,z)
    Output: 1 value (logit for stability)
    """
    def __init__(self, input_dim=6, hidden_dim=32):
        super(GeometryBaselineModel, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x):
        return self.net(x)

# --- Training Utilities ---
def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

def collate_fn(batch):
    """Custom collate to stack features and targets."""
    features, targets = zip(*batch)
    return torch.stack(features), torch.stack(targets)

def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    for batch_features, batch_targets in dataloader:
        batch_features = batch_features.to(device)
        batch_targets = batch_targets.to(device)

        optimizer.zero_grad()
        outputs = model(batch_features)
        # Flatten outputs if needed (B, 1) -> (B,)
        outputs = outputs.squeeze(1)
        loss = criterion(outputs, batch_targets)
        
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch_features, batch_targets in dataloader:
            batch_features = batch_features.to(device)
            batch_targets = batch_targets.to(device)
            
            outputs = model(batch_features).squeeze(1)
            loss = criterion(outputs, batch_targets)
            total_loss += loss.item()
            
            # Calculate accuracy
            predicted = (torch.sigmoid(outputs) > 0.5).float()
            total += batch_targets.size(0)
            correct += (predicted == batch_targets).sum().item()
    
    avg_loss = total_loss / len(dataloader)
    accuracy = correct / total
    return avg_loss, accuracy

def main():
    print(f"Starting Geometry-Only Baseline Training...")
    print(f"Device: {DEVICE}")
    
    # Set timeout for safety (e.g., 2 hours)
    set_timeout(7200)

    try:
        # 1. Load Data
        if not os.path.exists(TRAIN_PATH):
            raise FileNotFoundError(f"Training data not found at {TRAIN_PATH}. Run T016c first.")
        
        print(f"Loading training data from {TRAIN_PATH}...")
        train_dataset = GeometryOnlyDataset(TRAIN_PATH)
        
        # Optional: Load test data for validation
        if os.path.exists(TEST_PATH):
            print(f"Loading test data from {TEST_PATH}...")
            test_dataset = GeometryOnlyDataset(TEST_PATH)
        else:
            test_dataset = None
            print("Warning: Test data not found. Skipping validation metrics.")

        # 2. Create DataLoaders
        train_loader = DataLoader(
            train_dataset, 
            batch_size=BATCH_SIZE, 
            shuffle=True, 
            collate_fn=collate_fn,
            num_workers=0 # Keep it simple for CPU
        )
        
        test_loader = None
        if test_dataset:
            test_loader = DataLoader(
                test_dataset,
                batch_size=BATCH_SIZE,
                shuffle=False,
                collate_fn=collate_fn,
                num_workers=0
            )

        # 3. Initialize Model
        model = GeometryBaselineModel(input_dim=6, hidden_dim=32).to(DEVICE)
        total_params = sum(p.numel() for p in model.parameters())
        print(f"Model Parameters: {total_params:,}")

        # 4. Loss and Optimizer
        criterion = nn.BCEWithLogitsLoss()
        optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

        # 5. Training Loop
        print(f"Training for {EPOCHS} epochs...")
        best_test_acc = 0.0
        
        for epoch in range(EPOCHS):
            train_loss = train_epoch(model, train_loader, criterion, optimizer, DEVICE)
            
            if test_loader:
                test_loss, test_acc = evaluate(model, test_loader, criterion, DEVICE)
                print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {train_loss:.4f} | Test Loss: {test_loss:.4f} | Test Acc: {test_acc:.4f}")
                if test_acc > best_test_acc:
                    best_test_acc = test_acc
            else:
                print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {train_loss:.4f}")

        # 6. Save Model
        os.makedirs(os.path.dirname(OUTPUT_MODEL_PATH), exist_ok=True)
        torch.save({
            'model_state_dict': model.state_dict(),
            'total_params': total_params,
            'input_dim': 6,
            'best_test_acc': best_test_acc if test_loader else None
        }, OUTPUT_MODEL_PATH)
        
        print(f"Model saved to {OUTPUT_MODEL_PATH}")
        print(f"Best Test Accuracy: {best_test_acc:.4f}" if test_loader else "No test accuracy recorded.")

    except TimeoutError:
        print("ERROR: Training timed out.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Training failed with exception: {e}")
        raise
    finally:
        reset_timeout()
        gc.collect()

if __name__ == "__main__":
    set_seed(RANDOM_SEED)
    main()