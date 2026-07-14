import os
import sys
import argparse
import time
import json
import hashlib
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Local imports based on API surface
from models.baseline_transformer import create_baseline_model, BaselineTransformer
from data.dataset_loader import get_wikitext_dataloader, load_wikitext_dataset
from metrics.perplexity import compute_perplexity, log_perplexity_to_csv
from metrics.energy_logger import EnergyLogger, EnergyRecord

# Custom exceptions
class TrainingTerminationError(Exception):
    """Raised when training should be terminated due to specific conditions (e.g., zero spikes)."""
    pass

@dataclass
class MetricRecord:
    """Dataclass to hold metrics for a single epoch or run."""
    seed: int
    epoch: int
    perplexity: float
    energy_per_token_kWh: float
    wall_clock_time: float
    val_loss: float = 0.0
    train_loss: float = 0.0

@dataclass
class EarlyStopping:
    """
    Early stopping logic to halt training when validation loss stops improving.
    
    Attributes:
        patience: Number of epochs with no improvement after which training stops.
        delta: Minimum change in the monitored quantity to qualify as an improvement.
        mode: 'min' for validation loss, 'max' for metrics like accuracy.
    """
    patience: int = 2
    delta: float = 0.01
    mode: str = 'min'
    best_score: Optional[float] = None
    counter: int = 0
    stop_training: bool = False

    def __call__(self, score: float) -> bool:
        """
        Update early stopping state and return True if training should stop.
        
        Args:
            score: The current validation metric score (e.g., loss).
        
        Returns:
            bool: True if training should stop, False otherwise.
        """
        if self.best_score is None:
            self.best_score = score
            self.counter = 0
            return False

        if self.mode == 'min':
            # For loss, we want it to decrease
            if score < self.best_score - self.delta:
                self.best_score = score
                self.counter = 0
                return False
            else:
                self.counter += 1
                if self.counter >= self.patience:
                    self.stop_training = True
                    return True
        else:
            # For accuracy, we want it to increase
            if score > self.best_score + self.delta:
                self.best_score = score
                self.counter = 0
                return False
            else:
                self.counter += 1
                if self.counter >= self.patience:
                    self.stop_training = True
                    return True
        
        return False

def setup_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    if hasattr(torch, 'use_deterministic_algorithms'):
        try:
            torch.use_deterministic_algorithms(True)
        except RuntimeError:
            pass  # Ignore if not supported in current environment

def train_step(model: nn.Module, dataloader: DataLoader, optimizer: optim.Optimizer, 
               criterion: nn.Module, device: torch.device) -> float:
    """
    Perform a single training step over one epoch.
    
    Returns:
        float: Average training loss for the epoch.
    """
    model.train()
    total_loss = 0.0
    num_batches = 0

    for batch_idx, (data, target) in enumerate(dataloader):
        data, target = data.to(device), target.to(device)
        
        optimizer.zero_grad()
        output = model(data)
        
        # Flatten for loss calculation if necessary
        if output.dim() > 2:
            output = output.view(-1, output.size(-1))
            target = target.view(-1)
        
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches if num_batches > 0 else 0.0

def validate_step(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, 
                  device: torch.device) -> Tuple[float, float]:
    """
    Perform validation over one epoch.
    
    Returns:
        Tuple[float, float]: (Average validation loss, Perplexity)
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0

    with torch.no_grad():
        for data, target in dataloader:
            data, target = data.to(device), target.to(device)
            
            output = model(data)
            
            if output.dim() > 2:
                output = output.view(-1, output.size(-1))
                target = target.view(-1)
            
            loss = criterion(output, target)
            total_loss += loss.item()
            num_batches += 1

    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    perplexity = compute_perplexity(avg_loss)
    
    return avg_loss, perplexity

def run_baseline_training(seed: int, output_path: str, 
                          patience: int = 2, delta: float = 0.01,
                          max_epochs: int = 10) -> List[MetricRecord]:
    """
    Train the baseline transformer model with early stopping.
    
    Args:
        seed: Random seed for reproducibility.
        output_path: Path to save the metrics CSV.
        patience: Early stopping patience.
        delta: Early stopping delta.
        max_epochs: Maximum number of epochs to run.
    
    Returns:
        List[MetricRecord]: List of metric records for each epoch.
    """
    setup_seed(seed)
    
    device = torch.device('cpu')
    print(f"Training baseline model with seed {seed} on {device}")
    
    # Load data
    train_loader, val_loader = get_wikitext_dataloader(batch_size=32, seed=seed)
    
    # Create model
    model = create_baseline_model()
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    
    # Initialize early stopping
    early_stopping = EarlyStopping(patience=patience, delta=delta, mode='min')
    
    # Initialize energy logger
    energy_logger = EnergyLogger()
    
    records: List[MetricRecord] = []
    
    for epoch in range(1, max_epochs + 1):
        start_time = time.time()
        
        # Train
        train_loss = train_step(model, train_loader, optimizer, criterion, device)
        
        # Validate
        val_loss, perplexity = validate_step(model, val_loader, criterion, device)
        
        end_time = time.time()
        wall_clock_time = end_time - start_time
        
        # Log energy (estimated based on wall clock for CPU)
        energy_logger.start_epoch()
        energy_record = energy_logger.end_epoch()
        energy_per_token = energy_record.energy_per_token_kWh
        
        # Create metric record
        record = MetricRecord(
            seed=seed,
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token_kWh=energy_per_token,
            wall_clock_time=wall_clock_time,
            val_loss=val_loss,
            train_loss=train_loss
        )
        records.append(record)
        
        # Log to CSV immediately
        log_perplexity_to_csv(
            output_path=output_path,
            seed=seed,
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token=energy_per_token,
            wall_clock_time=wall_clock_time
        )
        
        print(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, "
              f"PPL: {perplexity:.4f}, Energy: {energy_per_token:.6f} kWh/token, "
              f"Time: {wall_clock_time:.2f}s")
        
        # Check early stopping
        if early_stopping(val_loss):
            print(f"Early stopping triggered at epoch {epoch}. "
                  f"Best val loss: {early_stopping.best_score:.4f}")
            break
    
    print(f"Training completed for seed {seed}. Total epochs: {len(records)}")
    return records

def main():
    """Main entry point for baseline training."""
    parser = argparse.ArgumentParser(description="Train Baseline Transformer")
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3, 4, 5],
                        help='List of random seeds to run')
    parser.add_argument('--patience', type=int, default=2,
                        help='Early stopping patience')
    parser.add_argument('--delta', type=float, default=0.01,
                        help='Early stopping delta')
    parser.add_argument('--output', type=str, default='data/processed/baseline_metrics.csv',
                        help='Output path for metrics CSV')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    all_records: List[MetricRecord] = []
    
    for seed in args.seeds:
        records = run_baseline_training(
            seed=seed,
            output_path=args.output,
            patience=args.patience,
            delta=args.delta
        )
        all_records.extend(records)
    
    print(f"Training complete. Results saved to {args.output}")
    print(f"Total records: {len(all_records)}")

if __name__ == "__main__":
    main()