"""
Main training and evaluation orchestration for Neuromorphic Transformer Networks.

This module coordinates the training of both baseline and spiking transformer models,
handles seed management, and logs metrics to CSV files.
"""

import os
import sys
import argparse
import time
import json
import hashlib
import torch
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from utils.logging_config import setup_logging

# Import local modules
from data.dataset_loader import get_wikitext_dataloader
from models.baseline_transformer import create_baseline_model
from models.spiking_transformer import create_spiking_model, verify_surrogate_gradients
from metrics.perplexity import compute_perplexity, log_perplexity_to_csv
from metrics.energy_logger import EnergyLogger, estimate_energy_from_time
from metrics.temporal_coding import collect_and_log_temporal_metrics

# Initialize logger
logger = setup_logging("main", log_file="data/logs/main.log")


@dataclass
class MetricRecord:
    """Data class to hold a single metric record."""
    seed: int
    epoch: int
    perplexity: float
    energy_per_token_kWh: float
    wall_clock_time: float
    temporal_coding_metrics: Optional[str] = None  # JSON string


class TrainingTerminationError(Exception):
    """Custom exception for training termination conditions (e.g., zero spikes)."""
    pass


@dataclass
class TrainingConfig:
    """Configuration for training runs."""
    num_layers: int = 2
    num_heads: int = 4
    d_model: int = 128
    d_ff: int = 256
    batch_size: int = 32
    learning_rate: float = 1e-3
    max_epochs: int = 10
    patience: int = 3  # For early stopping
    seed: int = 42
    is_spiking: bool = False


class EarlyStopping:
    """Early stopping handler to prevent overfitting."""

    def __init__(self, patience: int = 3, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
            return False

        if val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        else:
            self.best_loss = val_loss
            self.counter = 0
        return False


def setup_seed(seed: int):
    """Set random seeds for reproducibility."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    logger.info(f"Seed set to {seed}")


def save_zero_spike_report(seed: int, epoch: int, spike_stats: Dict[str, Any], output_path: str):
    """Save diagnostic report when zero-spike condition is detected."""
    report = {
        "seed": seed,
        "epoch": epoch,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "spike_statistics": spike_stats,
        "reason": "Zero-spike detection triggered: >50% neurons silent for 3 epochs"
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.warning(f"Zero-spike report saved to {output_path}")


def check_zero_spike_condition(
    spike_trains: torch.Tensor,
    threshold: float = 0.5,
    window_epochs: int = 3
) -> bool:
    """
    Check if >50% of neurons are silent for a given window.

    Args:
        spike_trains: Tensor of shape (batch, seq_len, num_neurons)
        threshold: Fraction of silent neurons to trigger termination
        window_epochs: Number of epochs to consider (simplified to current for this implementation)

    Returns:
        True if zero-spike condition is met.
    """
    # Calculate fraction of silent neurons
    # spike_trains is binary (0 or 1)
    active_neurons = spike_trains.sum(dim=(0, 1))  # Sum over batch and seq_len
    total_neurons = spike_trains.shape[2]
    silent_fraction = 1.0 - (active_neurons / total_neurons).mean().item()

    return silent_fraction > threshold


def train_step(
    model: torch.nn.Module,
    data_loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: torch.nn.Module,
    is_spiking: bool = False,
    num_steps: int = 10
) -> Tuple[float, torch.Tensor]:
    """
    Perform a single training step.

    Returns:
        Tuple of (loss, spike_trains)
    """
    model.train()
    total_loss = 0.0
    all_spikes = []

    for i, (inputs, targets) in enumerate(data_loader):
        if i >= num_steps:
            break

        optimizer.zero_grad()

        if is_spiking:
            # Spiking model forward pass
            # inputs: (batch, seq_len) -> need embedding
            outputs, spike_trains = model(inputs)
            loss = criterion(outputs, targets)
            all_spikes.append(spike_trains.detach())
        else:
            # Baseline model
            outputs = model(inputs)
            loss = criterion(outputs, targets)

        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    avg_loss = total_loss / min(num_steps, len(data_loader))
    spike_tensor = torch.cat(all_spikes, dim=0) if all_spikes else torch.tensor([])
    return avg_loss, spike_tensor


def validate_step(
    model: torch.nn.Module,
    data_loader: torch.utils.data.DataLoader,
    criterion: torch.nn.Module,
    is_spiking: bool = False,
    num_steps: int = 10
) -> Tuple[float, Optional[torch.Tensor]]:
    """
    Perform a single validation step.

    Returns:
        Tuple of (loss, spike_trains)
    """
    model.eval()
    total_loss = 0.0
    all_spikes = []

    with torch.no_grad():
        for i, (inputs, targets) in enumerate(data_loader):
            if i >= num_steps:
                break

            if is_spiking:
                outputs, spike_trains = model(inputs)
                loss = criterion(outputs, targets)
                all_spikes.append(spike_trains)
            else:
                outputs = model(inputs)
                loss = criterion(outputs, targets)

            total_loss += loss.item()

    avg_loss = total_loss / min(num_steps, len(data_loader))
    spike_tensor = torch.cat(all_spikes, dim=0) if all_spikes else None
    return avg_loss, spike_tensor


def run_baseline_training(config: TrainingConfig, output_csv: str):
    """
    Train the baseline transformer model.

    Args:
        config: Training configuration.
        output_csv: Path to save metrics CSV.
    """
    setup_seed(config.seed)
    logger.info(f"Starting baseline training with seed {config.seed}")

    # Create model
    model = create_baseline_model(
        d_model=config.d_model,
        nhead=config.num_heads,
        num_layers=config.num_layers,
        d_ff=config.d_ff
    )
    model.to("cpu")  # Enforce CPU

    # Data loader
    train_loader, val_loader = get_wikitext_dataloader(config.batch_size, config.seed)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    early_stopping = EarlyStopping(patience=config.patience)

    metrics_list = []
    energy_logger = EnergyLogger()

    for epoch in range(config.max_epochs):
        start_time = time.time()
        train_loss, _ = train_step(model, train_loader, optimizer, criterion, is_spiking=False)
        val_loss, _ = validate_step(model, val_loader, criterion, is_spiking=False)

        wall_clock = time.time() - start_time
        energy_logger.update(wall_clock, len(train_loader.dataset))

        perplexity = np.exp(val_loss)
        energy_per_token = energy_logger.estimate_energy_per_token()

        record = MetricRecord(
            seed=config.seed,
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token_kWh=energy_per_token,
            wall_clock_time=wall_clock
        )
        metrics_list.append(record)
        log_perplexity_to_csv([record], output_csv)

        logger.info(f"Epoch {epoch}: Val Loss={val_loss:.4f}, PPL={perplexity:.2f}, Energy={energy_per_token:.6f} kWh/token")

        if early_stopping(val_loss):
            logger.info(f"Early stopping triggered at epoch {epoch}")
            break

    logger.info("Baseline training completed.")


def run_spiking_training(config: TrainingConfig, output_csv: str):
    """
    Train the spiking transformer model.

    Args:
        config: Training configuration.
        output_csv: Path to save metrics CSV.
    """
    setup_seed(config.seed)
    logger.info(f"Starting spiking training with seed {config.seed}")

    # Create model
    model = create_spiking_model(
        d_model=config.d_model,
        nhead=config.num_heads,
        num_layers=config.num_layers,
        d_ff=config.d_ff
    )
    model.to("cpu")  # Enforce CPU

    # Verify surrogate gradients
    verify_surrogate_gradients(model)

    # Data loader
    train_loader, val_loader = get_wikitext_dataloader(config.batch_size, config.seed)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    early_stopping = EarlyStopping(patience=config.patience)

    metrics_list = []
    energy_logger = EnergyLogger()
    zero_spike_counter = 0

    for epoch in range(config.max_epochs):
        start_time = time.time()
        train_loss, train_spikes = train_step(model, train_loader, optimizer, criterion, is_spiking=True)
        val_loss, val_spikes = validate_step(model, val_loader, criterion, is_spiking=True)

        wall_clock = time.time() - start_time
        energy_logger.update(wall_clock, len(train_loader.dataset))

        perplexity = np.exp(val_loss)
        energy_per_token = energy_logger.estimate_energy_per_token()

        # Check zero-spike condition
        if val_spikes is not None:
            if check_zero_spike_condition(val_spikes):
                zero_spike_counter += 1
                if zero_spike_counter >= 3:
                    save_zero_spike_report(config.seed, epoch, {"silent_fraction": 0.5}, "data/logs/zero_spike_report.json")
                    raise TrainingTerminationError("Zero-spike detection triggered")
            else:
                zero_spike_counter = 0

        # Temporal coding metrics
        temporal_metrics = None
        if val_spikes is not None:
            temporal_metrics = collect_and_log_temporal_metrics(val_spikes, epoch, config.seed)

        record = MetricRecord(
            seed=config.seed,
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token_kWh=energy_per_token,
            wall_clock_time=wall_clock,
            temporal_coding_metrics=json.dumps(temporal_metrics) if temporal_metrics else None
        )
        metrics_list.append(record)
        log_perplexity_to_csv([record], output_csv)

        logger.info(f"Epoch {epoch}: Val Loss={val_loss:.4f}, PPL={perplexity:.2f}, Energy={energy_per_token:.6f} kWh/token")

        if early_stopping(val_loss):
            logger.info(f"Early stopping triggered at epoch {epoch}")
            break

    logger.info("Spiking training completed.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Train Baseline or Spiking Transformer")
    parser.add_argument("--mode", choices=["baseline", "spiking"], required=True, help="Training mode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")

    args = parser.parse_args()

    config = TrainingConfig(seed=args.seed, is_spiking=(args.mode == "spiking"))

    if args.mode == "baseline":
        output_path = args.output or "data/processed/baseline_metrics.csv"
        run_baseline_training(config, output_path)
    else:
        output_path = args.output or "data/processed/spiking_metrics.csv"
        try:
            run_spiking_training(config, output_path)
        except TrainingTerminationError as e:
            logger.error(str(e))
            sys.exit(1)


if __name__ == "__main__":
    main()