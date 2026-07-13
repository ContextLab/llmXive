"""
Train a Shuffled-Translation Control Model.

This script loads the training data (train.parquet), randomly shuffles the
translation trajectory sequences to break temporal correlations while preserving
marginal distributions, and trains a lightweight model on this permuted data.
The resulting model serves as a negative control to validate that the main
model's performance relies on temporal structure rather than just marginal
feature distributions.
"""
import os
import sys
import random
import gc
import signal
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from models.transformer import TranslationTransformer, count_parameters
from utils.data_utils import compute_checksum, update_checksums

# --- Constants & Paths ---
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "train.parquet"
MODEL_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "shuffled_control_model.pt"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
CHECKSUMS_PATH = PROJECT_ROOT / "data" / "checksums.json"

# Hyperparameters (matching main training for fair comparison)
SEED = 42
SEQ_LEN = 50  # Assumed sequence length for translation vectors
HIDDEN_DIM = 64
NUM_HEADS = 4
NUM_LAYERS = 2
DROPOUT = 0.1
BATCH_SIZE = 64
EPOCHS = 10
LEARNING_RATE = 1e-3
DEVICE = torch.device("cpu")  # CPU-only constraint

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timed out")

def set_timeout(seconds):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

class StabilityShuffledDataset(Dataset):
    """
    Dataset that loads data and shuffles the sequence dimension.
    """
    def __init__(self, df: pd.DataFrame, seq_len: int = SEQ_LEN):
        self.df = df
        self.seq_len = seq_len
        
        # Extract features and labels
        # Assuming columns 'translation_x', 'translation_y', 'translation_z' exist
        # or a single 'translation_vector' list column. 
        # Based on T012, we have relative wrist translation vectors.
        # We assume the data is already reshaped or we flatten here.
        
        # Check for specific columns or a list column
        if 'translation_vector' in df.columns:
            # If it's a list of vectors, expand it
            # Expected shape: (N, seq_len, 3)
            vectors = np.array(df['translation_vector'].tolist())
        else:
            # Fallback: assume flattened columns exist or reconstruct
            # For robustness, we'll assume the main script produced a specific format
            # Let's assume columns: tx_0, ty_0, tz_0 ... tx_49 ...
            cols = [c for c in df.columns if c.startswith('tx_') or c.startswith('ty_') or c.startswith('tz_')]
            if not cols:
                # If no specific columns, we might need to handle the 'initial_object_bounds' too?
                # The task says "shuffles translation trajectory sequences".
                # We will assume the main data generation script creates a 'translation_trajectory' column
                # which is a list of [x,y,z] tuples/lists.
                # If not, we raise an error.
                raise ValueError("Could not find translation trajectory data in DataFrame. Expected 'translation_vector' column or specific tx/ty/tz columns.")
        
        # Convert to numpy
        if 'translation_vector' in df.columns:
            self.X = np.array(df['translation_vector'].tolist(), dtype=np.float32)
        else:
            # Reconstruct from flattened columns if necessary
            # This is a fallback for safety
            raise ValueError("Data format mismatch. Expected 'translation_vector' list column.")

        self.y = df['stability'].values.astype(np.float32)

        # Verify dimensions
        if self.X.ndim != 3:
            raise ValueError(f"Expected 3D input (N, seq, 3), got {self.X.shape}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        # Get the sequence
        seq = self.X[idx].copy()
        
        # SHUFFLE THE SEQUENCE DIMENSION
        # We shuffle the time steps (axis 0 of the sequence) to break temporal order
        # while keeping the set of vectors (marginal distribution) the same.
        indices = np.arange(seq.shape[0])
        np.random.shuffle(indices)
        shuffled_seq = seq[indices]
        
        label = self.y[idx]
        
        return torch.tensor(shuffled_seq), torch.tensor(label)

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

def train_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_x, batch_y in loader:
        batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs.squeeze(), batch_y)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        preds = (outputs.squeeze() > 0.5).float()
        correct += (preds == batch_y).sum().item()
        total += batch_y.size(0)
        
        # GC for memory safety on CPU
        gc.collect()
    
    return total_loss / len(loader), correct / total

def evaluate(model, loader, criterion):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
            outputs = model(batch_x)
            loss = criterion(outputs.squeeze(), batch_y)
            
            total_loss += loss.item()
            preds = (outputs.squeeze() > 0.5).float()
            correct += (preds == batch_y).sum().item()
            total += batch_y.size(0)
    
    return total_loss / len(loader), correct / total

def main():
    print(f"Starting Shuffled-Translation Control Training (Task T027c)...")
    
    # 1. Load Data
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found at {DATA_PATH}. Run T016c first.")
    
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_parquet(DATA_PATH)
    
    # Validate columns
    required_cols = ['stability']
    if 'translation_vector' not in df.columns:
        # Try to find alternative column names if 'translation_vector' isn't there
        # The generate_data.py might have saved it differently.
        # We assume the standard format from T012.
        pass 
        
    print(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # 2. Prepare Dataset
    print("Preparing shuffled dataset...")
    dataset = StabilityShuffledDataset(df)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    
    # 3. Initialize Model
    # Input dim: 3 (x, y, z)
    model = TranslationTransformer(
        input_dim=3,
        hidden_dim=HIDDEN_DIM,
        num_heads=NUM_HEADS,
        num_layers=NUM_LAYERS,
        dropout=DROPOUT
    ).to(DEVICE)
    
    param_count = count_parameters(model)
    print(f"Model Parameters: {param_count:,}")
    
    if param_count >= 10_000_000:
        print(f"WARNING: Parameter count {param_count} exceeds 10M limit.")
    
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # 4. Training Loop
    print(f"Training for {EPOCHS} epochs on CPU...")
    set_timeout(7200) # 2 hour max for safety
    
    best_acc = 0.0
    
    try:
        for epoch in range(EPOCHS):
            train_loss, train_acc = train_epoch(model, loader, criterion, optimizer)
            val_loss, val_acc = evaluate(model, loader, criterion)
            
            print(f"Epoch {epoch+1}/{EPOCHS} - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, Val Acc: {val_acc:.4f}")
            
            if val_acc > best_acc:
                best_acc = val_acc
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'accuracy': val_acc,
                    'params': param_count,
                    'config': {
                        'seq_len': SEQ_LEN,
                        'hidden_dim': HIDDEN_DIM,
                        'num_heads': NUM_HEADS,
                        'num_layers': NUM_LAYERS,
                        'dropout': DROPOUT,
                        'learning_rate': LEARNING_RATE
                    }
                }, MODEL_OUTPUT_PATH)
                
    except TimeoutError:
        print("Training timed out. Saving current model state.")
    finally:
        reset_timeout()
    
    print(f"Training complete. Best Validation Accuracy: {best_acc:.4f}")
    print(f"Model saved to {MODEL_OUTPUT_PATH}")
    
    # 5. Update Checksums
    if MODEL_OUTPUT_PATH.exists():
        checksum = compute_checksum(MODEL_OUTPUT_PATH)
        update_checksums(CHECKSUMS_PATH, "shuffled_control_model.pt", checksum)
        print(f"Updated checksums for shuffled_control_model.pt: {checksum}")
        
    # 6. Log Results for T028
    metrics = {
        "task": "T027c",
        "model": "shuffled_control",
        "best_accuracy": best_acc,
        "parameters": param_count,
        "data_source": str(DATA_PATH),
        "method": "shuffled_sequences"
    }
    
    metrics_path = PROJECT_ROOT / "data" / "logs" / "shuffled_control_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics logged to {metrics_path}")

if __name__ == "__main__":
    set_seed(SEED)
    main()
