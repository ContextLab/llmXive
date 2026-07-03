import os
import sys
import argparse
import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import pandas as pd

# Project imports
from models.baseline_transformer import create_baseline_model
from data.dataset_loader import get_wikitext_dataloader
from metrics.perplexity import compute_perplexity, log_perplexity_to_csv
from metrics.energy_logger import EnergyLogger, estimate_energy_from_time

class TrainingTerminationError(Exception):
    """Raised when training must stop due to specific conditions (e.g., zero spikes)."""
    pass

class EarlyStopping:
    """
    Early stopping to stop training early if validation loss does not improve.
    
    Args:
        patience (int): How many epochs to wait before stopping.
        delta (float): Minimum change in the monitored quantity to qualify as an improvement.
        min_delta (float): Minimum change in the monitored value to be considered an improvement.
    """
    def __init__(self, patience: int = 2, delta: float = 0.01, min_delta: float = 0.0):
        self.patience = patience
        self.delta = delta
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        """
        Check if training should stop.
        
        Args:
            val_loss: Current validation loss.
        
        Returns:
            bool: True if training should stop (early stop triggered).
        """
        if self.best_loss is None:
            self.best_loss = val_loss
            self.counter = 0
            return False

        # Check if improvement (lower loss)
        if val_loss < self.best_loss - self.delta:
            self.best_loss = val_loss
            self.counter = 0
            return False
        
        self.counter += 1
        if self.counter >= self.patience:
            self.early_stop = True
            return True
        
        return False

class MetricRecord:
    """Data container for a single training epoch's metrics."""
    def __init__(self, seed: int, epoch: int, perplexity: float, 
                 energy_per_token_kWh: float, wall_clock_time: float):
        self.seed = seed
        self.epoch = epoch
        self.perplexity = perplexity
        self.energy_per_token_kWh = energy_per_token_kWh
        self.wall_clock_time = wall_clock_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "epoch": self.epoch,
            "perplexity": self.perplexity,
            "energy_per_token_kWh": self.energy_per_token_kWh,
            "wall_clock_time": self.wall_clock_time
        }

class TrainingResult:
    """Container for the final results of a training run."""
    def __init__(self, metrics: List[MetricRecord], final_model_state: Optional[Dict] = None):
        self.metrics = metrics
        self.final_model_state = final_model_state

def setup_seed(seed: int):
    """Set random seeds for reproducibility."""
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    # Note: Project enforces CPU-only, but setting these is good practice
    # if the environment were to support GPU.
    
    # For numpy if needed
    import numpy as np
    np.random.seed(seed)

def train_step(model: nn.Module, dataloader: DataLoader, optimizer: optim.Optimizer, 
               criterion: nn.Module, device: torch.device) -> float:
    """
    Perform a single training step over the dataloader.
    
    Returns:
        float: Average loss for the epoch.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch in dataloader:
        # batch is expected to be a tuple (input_ids, labels) or similar
        # Adjust based on get_wikitext_dataloader output format
        if isinstance(batch, (tuple, list)):
            inputs, labels = batch[0].to(device), batch[1].to(device)
        else:
            # Handle case where batch is a dict or single tensor
            inputs = batch.to(device)
            labels = inputs  # Simple self-supervised setup

        optimizer.zero_grad()
        outputs = model(inputs)
        
        # Compute loss (assuming outputs are logits and labels are targets)
        # Flatten for cross_entropy
        if isinstance(outputs, tuple):
            logits = outputs[0]
        else:
            logits = outputs
        
        loss = criterion(logits.view(-1, logits.size(-1)), labels.view(-1))
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches if num_batches > 0 else 0.0

def validate_step(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, 
                  device: torch.device) -> float:
    """
    Perform a single validation step.
    
    Returns:
        float: Average loss for the epoch.
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for batch in dataloader:
            if isinstance(batch, (tuple, list)):
                inputs, labels = batch[0].to(device), batch[1].to(device)
            else:
                inputs = batch.to(device)
                labels = inputs

            outputs = model(inputs)
            if isinstance(outputs, tuple):
                logits = outputs[0]
            else:
                logits = outputs
            
            loss = criterion(logits.view(-1, logits.size(-1)), labels.view(-1))
            total_loss += loss.item()
            num_batches += 1

    return total_loss / num_batches if num_batches > 0 else 0.0

def run_baseline_training(seed: int, max_epochs: int = 10, patience: int = 2, 
                          delta: float = 0.01, batch_size: int = 32, 
                          lr: float = 1e-3, output_csv_path: str = "data/processed/baseline_metrics.csv") -> TrainingResult:
    """
    Run the baseline transformer training loop with early stopping.
    
    Args:
        seed: Random seed for reproducibility.
        max_epochs: Maximum number of epochs to train.
        patience: Patience for early stopping.
        delta: Delta for early stopping improvement threshold.
        batch_size: Batch size for dataloaders.
        lr: Learning rate.
        output_csv_path: Path to save metrics CSV.
    
    Returns:
        TrainingResult: Object containing metrics list and final model state.
    """
    setup_seed(seed)
    
    # Device setup (CPU enforced per project constraints)
    device = torch.device("cpu")
    
    # Load data
    train_loader, val_loader = get_wikitext_dataloader(batch_size=batch_size, seed=seed)
    
    # Create model
    model = create_baseline_model()
    model = model.to(device)
    
    # Optimizer and Criterion
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()
    
    # Early Stopping Instance
    early_stopper = EarlyStopping(patience=patience, delta=delta)
    
    # Energy Logger
    energy_logger = EnergyLogger()
    
    metrics_list: List[MetricRecord] = []
    
    print(f"Starting baseline training with seed {seed}...")
    
    for epoch in range(max_epochs):
        start_time = time.time()
        
        # Training
        train_loss = train_step(model, train_loader, optimizer, criterion, device)
        
        # Validation
        val_loss = validate_step(model, val_loader, criterion, device)
        
        # Calculate Perplexity
        perplexity = compute_perplexity(val_loss)
        
        # Estimate Energy (CPU proxy)
        epoch_time = time.time() - start_time
        # Estimate energy based on time for CPU proxy
        energy_kWh = estimate_energy_from_time(epoch_time, is_gpu=False)
        energy_per_token = energy_kWh / (len(train_loader.dataset) * epoch_time) if epoch_time > 0 else 0.0
        
        # Log metrics
        metric = MetricRecord(
            seed=seed,
            epoch=epoch + 1,
            perplexity=perplexity,
            energy_per_token_kWh=energy_per_token,
            wall_clock_time=epoch_time
        )
        metrics_list.append(metric)
        
        # Log to CSV
        log_perplexity_to_csv(metric, output_csv_path)
        
        print(f"Epoch {epoch+1}/{max_epochs} | Train Loss: {train_loss:.4f} | "
              f"Val Loss: {val_loss:.4f} | PPL: {perplexity:.2f} | "
              f"Energy: {energy_per_token:.6f} kWh/token | Time: {epoch_time:.2f}s")
        
        # Check Early Stopping
        if early_stopper(val_loss):
            print(f"Early stopping triggered at epoch {epoch+1}.")
            break
    
    # Save final model state if needed (optional, but good practice)
    final_state = model.state_dict() if model else None
    
    return TrainingResult(metrics=metrics_list, final_model_state=final_state)

def main():
    parser = argparse.ArgumentParser(description="Baseline Transformer Training")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5],
                        help="List of random seeds to run.")
    parser.add_argument("--patience", type=int, default=2, help="Early stopping patience.")
    parser.add_argument("--delta", type=float, default=0.01, help="Early stopping delta.")
    parser.add_argument("--max-epochs", type=int, default=10, help="Maximum epochs.")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--output", type=str, default="data/processed/baseline_metrics.csv",
                        help="Output CSV path.")
    
    args = parser.parse_args()
    
    all_metrics = []
    
    for seed in args.seeds:
        result = run_baseline_training(
            seed=seed,
            max_epochs=args.max_epochs,
            patience=args.patience,
            delta=args.delta,
            batch_size=args.batch_size,
            lr=args.lr,
            output_csv_path=args.output
        )
        all_metrics.extend(result.metrics)
        
    print(f"Training complete for seeds {args.seeds}. Results saved to {args.output}.")

if __name__ == "__main__":
    main()