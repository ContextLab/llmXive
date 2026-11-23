import os
import sys
import time
import json
import gc
import signal
import random
import math
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import Tuple, List, Dict, Optional
import psutil
import numpy as np
from pathlib import Path

from models.transformer import TranslationTransformer, count_parameters
from utils.data_utils import update_checksums

# --- Timeout Handling ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timed out")

def set_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

# --- Memory Tracking ---
_peak_memory_mb = 0.0

def get_peak_memory_mb() -> float:
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def update_peak_memory():
    global _peak_memory_mb
    current = get_peak_memory_mb()
    if current > _peak_memory_mb:
        _peak_memory_mb = current

def log_peak_memory():
    global _peak_memory_mb
    update_peak_memory()
    print(f"[RAM-PEAK-MB]: {_peak_memory_mb:.2f}")

# --- Dataset ---
class StabilityDataset(torch.utils.data.Dataset):
    def __init__(self, parquet_path: str):
        import pandas as pd
        self.df = pd.read_parquet(parquet_path)
        self.translation_keys = [col for col in self.df.columns if col.startswith('translation')]
        self.bounds_keys = [col for col in self.df.columns if col.startswith('initial_bounds')]
        
        # Convert to tensors
        self.X_trans = torch.tensor(self.df[self.translation_keys].values, dtype=torch.float32)
        self.X_bounds = torch.tensor(self.df[self.bounds_keys].values, dtype=torch.float32)
        self.y = torch.tensor(self.df['stability_label'].values, dtype=torch.float32)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        return self.X_trans[idx], self.X_bounds[idx], self.y[idx]

def collate_fn(batch):
    trans, bounds, labels = zip(*batch)
    return torch.stack(trans), torch.stack(bounds), torch.stack(labels)

# --- Training Utilities ---
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def train_epoch(model: nn.Module, loader: DataLoader, criterion: nn.Module, optimizer: optim.Optimizer, device: torch.device) -> float:
    model.train()
    total_loss = 0.0
    for trans, bounds, labels in loader:
        trans, bounds, labels = trans.to(device), bounds.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(trans, bounds)
        loss = criterion(outputs.squeeze(), labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        update_peak_memory()
    
    return total_loss / len(loader)

def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> Tuple[float, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for trans, bounds, labels in loader:
            trans, bounds, labels = trans.to(device), bounds.to(device), labels.to(device)
            outputs = model(trans, bounds)
            loss = criterion(outputs.squeeze(), labels)
            
            total_loss += loss.item()
            predicted = (torch.sigmoid(outputs.squeeze()) > 0.5).float()
            correct += (predicted == labels).sum().item()
            total += labels.size(0)
            
            update_peak_memory()
    
    return total_loss / len(loader), correct / total

def main():
    # Configuration
    device = torch.device("cpu") # CPU-only as per constraints
    epochs = 10
    batch_size = 64
    learning_rate = 1e-3
    timeout_seconds = 21600 # 6 hours
    data_path_train = "data/processed/train.parquet"
    data_path_test = "data/processed/test.parquet"
    output_model_path = "data/processed/trained_model.pt"
    output_log_path = "data/processed/training_log.json"

    print(f"Loading data from {data_path_train}...")
    train_dataset = StabilityDataset(data_path_train)
    test_dataset = StabilityDataset(data_path_test)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

    # Model Initialization
    input_dim_trans = train_dataset.X_trans.shape[1]
    input_dim_bounds = train_dataset.X_bounds.shape[1]
    
    print(f"Initializing TranslationTransformer with trans_dim={input_dim_trans}, bounds_dim={input_dim_bounds}...")
    model = TranslationTransformer(
        trans_input_dim=input_dim_trans,
        bounds_input_dim=input_dim_bounds,
        d_model=64,
        nhead=4,
        num_layers=4,
        dim_feedforward=128,
        dropout=0.1
    ).to(device)

    param_count = count_parameters(model)
    print(f"Model Parameter Count: {param_count:,}")
    
    if param_count >= 10_000_000:
        raise ValueError(f"Model parameter count ({param_count}) exceeds limit of 10,000,000.")

    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training Loop
    set_timeout(timeout_seconds)
    try:
        print(f"Starting training for {epochs} epochs on CPU...")
        start_time = time.time()
        
        history = {'train_loss': [], 'test_loss': [], 'test_acc': []}
        
        for epoch in range(1, epochs + 1):
            train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
            test_loss, test_acc = evaluate(model, test_loader, criterion, device)
            
            history['train_loss'].append(train_loss)
            history['test_loss'].append(test_loss)
            history['test_acc'].append(test_acc)
            
            update_peak_memory()
            print(f"Epoch {epoch}/{epochs} - Train Loss: {train_loss:.4f} - Test Loss: {test_loss:.4f} - Test Acc: {test_acc:.4f}")
        
        elapsed_time = time.time() - start_time
        print(f"Training completed in {elapsed_time:.2f} seconds.")
        
    except TimeoutError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        reset_timeout()

    # --- T024: Save Model and Log Parameter Count ---
    print(f"Saving trained model to {output_model_path}...")
    torch.save({
        'epoch': epochs,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'param_count': param_count,
        'input_trans_dim': input_dim_trans,
        'input_bounds_dim': input_dim_bounds,
        'history': history
    }, output_model_path)

    # Log parameter count explicitly
    log_entry = {
        "model_path": output_model_path,
        "total_parameters": param_count,
        "training_epochs": epochs,
        "final_test_accuracy": history['test_acc'][-1],
        "final_test_loss": history['test_loss'][-1],
        "peak_memory_mb": _peak_memory_mb
    }
    
    with open(output_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"Model saved successfully. Parameter count: {param_count:,}")
    print(f"Training log saved to {output_log_path}")

    # Update checksums for the new model file
    update_checksums(output_model_path)
    update_checksums(output_log_path)

    # Final Memory Log
    log_peak_memory()

if __name__ == "__main__":
    main()
