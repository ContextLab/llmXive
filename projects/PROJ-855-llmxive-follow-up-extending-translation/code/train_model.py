import os
import sys
import time
import json
import gc
import signal
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import psutil

# Import from sibling modules as per API surface
from models.transformer import TranslationTransformer, count_parameters
from utils.data_utils import update_checksums
from utils.physics_metrics import load_config

# --- Timeout Handling (from T023) ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Training timed out")

def set_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def reset_timeout():
    signal.alarm(0)

# --- Memory Monitoring (from T023) ---
_peak_memory_mb = 0.0

def get_peak_memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

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
class StabilityDataset(Dataset):
    def __init__(self, data_path: str):
        import pandas as pd
        self.data = pd.read_parquet(data_path)
        
        # Identify columns
        # Assuming columns: 'translation_trajectory' (list/array), 'initial_object_bounds' (list/array), 'label'
        # We need to flatten or handle sequences. For simplicity in this implementation,
        # we assume the parquet stores lists that we convert to tensors.
        
        self.trajectories = self.data['translation_trajectory'].tolist()
        self.bounds = self.data['initial_object_bounds'].tolist()
        self.labels = self.data['label'].tolist()
        
        # Convert to tensors
        self.trajectories = [torch.tensor(t, dtype=torch.float32) for t in self.trajectories]
        self.bounds = [torch.tensor(b, dtype=torch.float32) for b in self.bounds]
        self.labels = torch.tensor(self.labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.trajectories[idx], self.bounds[idx], self.labels[idx]

def collate_fn(batch):
    # Unpack batch
    trajs, bounds, labels = zip(*batch)
    
    # Pad trajectories to max length in batch
    max_len = max(t.shape[0] for t in trajs)
    padded_trajs = []
    for t in trajs:
        if t.shape[0] < max_len:
            pad = torch.zeros(max_len - t.shape[0], t.shape[1])
            t = torch.cat([t, pad], dim=0)
        padded_trajs.append(t)
    
    trajs_tensor = torch.stack(padded_trajs)
    bounds_tensor = torch.stack(bounds)
    labels_tensor = torch.stack(labels)
    
    return trajs_tensor, bounds_tensor, labels_tensor

# --- Training Loop ---
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def train_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    for trajs, bounds, labels in loader:
        trajs, bounds, labels = trajs.to(device), bounds.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(trajs, bounds)
        loss = criterion(outputs, labels)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        update_peak_memory()
        
        # GC to prevent memory bloat
        if len(loader) % 100 == 0:
            gc.collect()
    
    return total_loss / len(loader)

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for trajs, bounds, labels in loader:
            trajs, bounds, labels = trajs.to(device), bounds.to(device), labels.to(device)
            outputs = model(trajs, bounds)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            preds = (outputs > 0.5).float()
            correct += (preds == labels).sum().item()
            total += labels.size(0)
            
            update_peak_memory()
    
    return total_loss / len(loader), correct / total

# --- Main Entry Point ---
def main():
    # Configuration
    config = load_config()
    data_path = "data/processed/train.parquet"
    model_save_path = "data/processed/trained_model.pt"
    timeout_seconds = 6 * 3600  # 6 hours
    
    # Hyperparameters
    batch_size = 32
    learning_rate = 1e-4
    epochs = 10
    device = torch.device("cpu") # Enforce CPU-only as per T022
    
    print(f"Starting training on {device}")
    print(f"Loading data from {data_path}...")
    
    # Set timeout
    set_timeout(timeout_seconds)
    
    try:
        dataset = StabilityDataset(data_path)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
        
        # Model
        # Assuming model expects specific hidden dims. 
        # We'll use defaults that keep it under 10M params as per T021
        model = TranslationTransformer(d_model=64, nhead=4, num_layers=4, dim_feedforward=128)
        
        total_params = count_parameters(model)
        print(f"Model parameter count: {total_params:,}")
        
        if total_params >= 10_000_000:
            raise ValueError(f"Model has {total_params} parameters, exceeds 10M limit.")
        
        model = model.to(device)
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        criterion = nn.BCEWithLogitsLoss()
        
        # Training Loop
        for epoch in range(epochs):
            train_loss = train_epoch(model, loader, optimizer, criterion, device)
            val_loss, val_acc = evaluate(model, loader, criterion, device)
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
            log_peak_memory()
        
        # Save Model
        print(f"Saving model to {model_save_path}...")
        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
        
        # Save state dict and config info
        save_dict = {
            'model_state_dict': model.state_dict(),
            'param_count': total_params,
            'config': {
                'd_model': 64,
                'nhead': 4,
                'num_layers': 4,
                'dim_feedforward': 128
            }
        }
        torch.save(save_dict, model_save_path)
        
        # Log parameter count explicitly as required by T024
        print(f"MODEL_SAVED: {model_save_path}")
        print(f"PARAMETER_COUNT: {total_params}")
        
        # Update checksums
        update_checksums(model_save_path)
        
    except TimeoutError:
        print("ERROR: Training timed out.")
        reset_timeout()
        sys.exit(1)
    except Exception as e:
        print(f"ERROR during training: {e}")
        reset_timeout()
        sys.exit(1)
    finally:
        reset_timeout()
        log_peak_memory()

if __name__ == "__main__":
    main()