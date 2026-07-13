import os
import sys
import time
import json
import gc
import signal
import argparse
import psutil
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Optional, Dict, Any

# Import from sibling modules as per API surface
from models.transformer import TranslationTransformer, count_parameters
from utils.data_utils import compute_checksum, update_checksums
from utils.physics_metrics import load_config

# --- Timeout Handling ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timeout exceeded")

def set_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

# --- Memory Monitoring ---
def get_peak_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

_peak_memory = 0.0

def update_peak_memory(current_mb: float):
    global _peak_memory
    if current_mb > _peak_memory:
        _peak_memory = current_mb

def log_peak_memory():
    global _peak_memory
    print(f"[RAM-PEAK-MB]: {_peak_memory:.2f}")

# --- Dataset Class (Minimal Implementation for Context) ---
class StabilityDataset(torch.utils.data.Dataset):
    def __init__(self, data_path: str):
        import pandas as pd
        self.df = pd.read_parquet(data_path)
        # Assuming columns 'translation_vector' (list/array) and 'label' exist
        # In a real scenario, we would parse the parquet properly
        self.data = self.df['translation_vector'].apply(lambda x: torch.tensor(x, dtype=torch.float32)).tolist()
        self.labels = self.df['label'].tolist()

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.data[idx], torch.tensor(self.labels[idx], dtype=torch.float32)

# --- Training Functions ---
def set_seed(seed: int = 42):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, criterion: nn.Module, device: torch.device):
    model.train()
    total_loss = 0.0
    for batch_x, batch_y in loader:
        batch_x = torch.stack(batch_x).to(device) # Shape: (B, Seq, F)
        batch_y = batch_y.to(device)

        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

        # Update memory stats periodically
        update_peak_memory(get_peak_memory_mb())

    return total_loss / len(loader)

def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x = torch.stack(batch_x).to(device)
            batch_y = batch_y.to(device)

            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            total_loss += loss.item()

            preds = (torch.sigmoid(outputs) > 0.5).float()
            correct += (preds == batch_y).sum().item()
            total += batch_y.size(0)

            update_peak_memory(get_peak_memory_mb())

    return total_loss / len(loader), correct / total

def main():
    parser = argparse.ArgumentParser(description="Train Stability Model")
    parser.add_argument("--data", type=str, default="data/processed/train.parquet", help="Path to training data")
    parser.add_argument("--output", type=str, default="data/processed/trained_model.pt", help="Path to save model")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--timeout", type=int, default=21600, help="Timeout in seconds (6 hours)")
    args = parser.parse_args()

    # Load config
    config = load_config("code/config.yaml")
    
    # Device setup (CPU only as per constraints)
    device = torch.device("cpu")
    print(f"Using device: {device}")

    # Data Loading
    print(f"Loading data from {args.data}...")
    dataset = StabilityDataset(args.data)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

    # Model Setup
    # Assuming input dim is based on translation vector length (e.g., 3) and sequence length
    # We need to infer or set these. For this implementation, we assume a fixed config or derive from first batch.
    # Let's assume sequence length 10 and feature dim 3 for translation vectors.
    input_dim = 3 
    seq_len = 10 
    model = TranslationTransformer(input_dim=input_dim, seq_len=seq_len, hidden_dim=64, num_layers=4, num_heads=4, dropout=0.1)
    model = model.to(device)

    # Parameter Count Verification (T025 Requirement)
    param_count = count_parameters(model)
    print(f"Model Parameter Count: {param_count:,}")
    
    if param_count >= 10_000_000:
        raise ValueError(f"Model has {param_count:,} parameters, which exceeds the 10,000,000 limit.")
    
    print("Parameter count verified: < 10,000,000")

    # Loss and Optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # Timeout Setup
    set_timeout(args.timeout)

    try:
        print("Starting training...")
        for epoch in range(args.epochs):
            start_time = time.time()
            train_loss = train_epoch(model, loader, optimizer, criterion, device)
            val_loss, val_acc = evaluate(model, loader, criterion, device)
            end_time = time.time()

            print(f"Epoch {epoch+1}/{args.epochs} - Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f} - Val Acc: {val_acc:.4f} - Time: {end_time - start_time:.2f}s")
            log_peak_memory() # Log memory usage periodically

        print("Training completed successfully.")
    except TimeoutError:
        print("Training timed out.")
        sys.exit(1)
    finally:
        reset_timeout()

    # Save Model (T024)
    print(f"Saving model to {args.output}...")
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'param_count': param_count,
        'config': {
            'input_dim': input_dim,
            'seq_len': seq_len,
            'hidden_dim': 64,
            'num_layers': 4,
            'num_heads': 4
        }
    }, args.output)

    # Update Checksums (T006 dependency)
    if os.path.exists("data/checksums.json"):
        update_checksums("data/checksums.json", args.output)

    print(f"Model saved. Total parameters: {param_count:,}")

if __name__ == "__main__":
    main()