import os
import sys
import argparse
import time
import json
import hashlib

import torch
import torch.nn as nn
import pandas as pd
import numpy as np

# Local imports
from models.baseline_transformer import create_baseline_model
from models.spiking_transformer import create_spiking_model, verify_surrogate_gradients
from metrics.energy_logger import EnergyLogger, EnergyRecord, estimate_energy_from_time
from metrics.perplexity import compute_perplexity, log_perplexity_to_csv
from metrics.temporal_coding import analyze_spike_trains, log_temporal_metrics_to_csv
from data.dataset_loader import load_wikitext2, CharTokenizer, WikiTextDataset, get_dataloaders
from tests.test_training_loop import EarlyStopping, TrainingConfig, MetricRecord

class TrainingTerminationError(Exception):
    """Raised when training must stop due to specific conditions (e.g., zero spikes)."""
    pass

class TrainingResult:
    def __init__(self, metrics_list, final_state=None, logs=None):
        self.metrics_list = metrics_list
        self.final_state = final_state
        self.logs = logs or []

def setup_seed(seed: int):
    """Set random seeds for reproducibility."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def train_step(model, dataloader, optimizer, device, is_spiking=False):
    model.train()
    total_loss = 0.0
    total_tokens = 0
    all_spikes = [] if is_spiking else None

    for batch in dataloader:
        inputs = batch['input_ids'].to(device)
        targets = batch['labels'].to(device)

        optimizer.zero_grad()

        if is_spiking:
            # For spiking models, we need to handle the time dimension
            # Assuming model outputs a tuple (loss, spike_trains)
            outputs, spike_trains = model(inputs)
            loss = outputs
            all_spikes.append(spike_trains.detach().cpu())
        else:
            outputs = model(inputs)
            loss = nn.functional.cross_entropy(outputs.view(-1, outputs.size(-1)), targets.view(-1))

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * inputs.numel()
        total_tokens += inputs.numel()

    avg_loss = total_loss / total_tokens
    return avg_loss, all_spikes if is_spiking else None

def validate_step(model, dataloader, device, is_spiking=False):
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    all_spikes = [] if is_spiking else None

    with torch.no_grad():
        for batch in dataloader:
            inputs = batch['input_ids'].to(device)
            targets = batch['labels'].to(device)

            if is_spiking:
                outputs, spike_trains = model(inputs)
                loss = outputs
                all_spikes.append(spike_trains.detach().cpu())
            else:
                outputs = model(inputs)
                loss = nn.functional.cross_entropy(outputs.view(-1, outputs.size(-1)), targets.view(-1))

            total_loss += loss.item() * inputs.numel()
            total_tokens += inputs.numel()

    avg_loss = total_loss / total_tokens
    return avg_loss, all_spikes if is_spiking else None

def run_baseline_training(seed: int, config: TrainingConfig, device: torch.device):
    """Train baseline transformer and return metrics."""
    setup_seed(seed)
    tokenizer = CharTokenizer()
    train_loader, val_loader = get_dataloaders(tokenizer, config.batch_size)

    model = create_baseline_model(vocab_size=len(tokenizer), device=device)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    early_stopping = EarlyStopping(patience=config.patience, delta=config.delta)

    energy_logger = EnergyLogger()
    metrics = []

    for epoch in range(config.epochs):
        start_time = time.time()
        train_loss, _ = train_step(model, train_loader, optimizer, device, is_spiking=False)
        val_loss, _ = validate_step(model, val_loader, device, is_spiking=False)

        # Energy logging
        energy_record = energy_logger.log_epoch(epoch, train_loss, val_loss, config.batch_size)
        energy_per_token = energy_record.estimated_energy_kWh / (config.batch_size * len(train_loader.dataset))

        # Perplexity
        perplexity = compute_perplexity(val_loss)

        wall_clock = time.time() - start_time

        record = {
            'seed': seed,
            'epoch': epoch,
            'perplexity': perplexity,
            'energy_per_token_kWh': energy_per_token,
            'wall_clock_time': wall_clock,
            'estimated': energy_record.is_estimated
        }
        metrics.append(record)
        log_perplexity_to_csv(record, 'data/processed/baseline_metrics.csv')

        if early_stopping(val_loss, model):
            print(f"Early stopping at epoch {epoch}")
            break

    return metrics

def run_spiking_training(seed: int, config: TrainingConfig, device: torch.device):
    """Train spiking transformer and return metrics with explicit estimated flag."""
    setup_seed(seed)
    tokenizer = CharTokenizer()
    train_loader, val_loader = get_dataloaders(tokenizer, config.batch_size)

    model = create_spiking_model(vocab_size=len(tokenizer), device=device)
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    early_stopping = EarlyStopping(patience=config.patience, delta=config.delta)

    energy_logger = EnergyLogger()
    metrics = []
    zero_spike_epochs = 0

    for epoch in range(config.epochs):
        start_time = time.time()
        train_loss, train_spikes = train_step(model, train_loader, optimizer, device, is_spiking=True)
        val_loss, val_spikes = validate_step(model, val_loader, device, is_spiking=True)

        # Zero-spike detection (FR-006)
        if train_spikes:
            total_spikes = sum(s.sum().item() for s in train_spikes)
            total_neurons = model.num_neurons
            spike_rate = total_spikes / (total_neurons * config.batch_size * len(train_loader.dataset))
            if spike_rate < 0.01: # Threshold for "silent"
                zero_spike_epochs += 1
                print(f"WARNING: Zero-spike detection triggered at epoch {epoch}")
                if zero_spike_epochs >= 3:
                    raise TrainingTerminationError("Model has been silent for 3 epochs")
            else:
                zero_spike_epochs = 0

        # Energy logging with explicit "estimated" flag handling
        energy_record = energy_logger.log_epoch(epoch, train_loss, val_loss, config.batch_size)
        # The EnergyLogger already sets is_estimated if codecarbon fails
        energy_per_token = energy_record.estimated_energy_kWh / (config.batch_size * len(train_loader.dataset))

        # Temporal coding analysis
        temporal_metrics = analyze_spike_trains(val_spikes)
        
        # Perplexity
        perplexity = compute_perplexity(val_loss)

        wall_clock = time.time() - start_time

        record = {
            'seed': seed,
            'epoch': epoch,
            'perplexity': perplexity,
            'energy_per_token_kWh': energy_per_token,
            'wall_clock_time': wall_clock,
            'temporal_coding_metrics': json.dumps(temporal_metrics),
            'estimated': energy_record.is_estimated  # Explicit flag as per T020
        }
        metrics.append(record)
        log_perplexity_to_csv(record, 'data/processed/spiking_metrics.csv')
        log_temporal_metrics_to_csv(record, 'data/processed/spiking_metrics.csv')

        if early_stopping(val_loss, model):
            print(f"Early stopping at epoch {epoch}")
            break

    return metrics

def main():
    parser = argparse.ArgumentParser(description="Neuromorphic Transformer Training")
    parser.add_argument('--mode', type=str, default='baseline', choices=['baseline', 'spiking'])
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3, 4, 5])
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--patience', type=int, default=2)
    parser.add_argument('--delta', type=float, default=0.01)
    args = parser.parse_args()

    device = torch.device('cpu') # CPU-only enforcement
    config = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        patience=args.patience,
        delta=args.delta
    )

    all_metrics = []
    for seed in args.seeds:
        try:
            print(f"Training {args.mode} model with seed {seed}...")
            if args.mode == 'baseline':
                metrics = run_baseline_training(seed, config, device)
            else:
                metrics = run_spiking_training(seed, config, device)
            all_metrics.extend(metrics)
        except TrainingTerminationError as e:
            print(f"Training terminated for seed {seed}: {e}")
            # Log diagnostic report for zero-spike termination
            report = {
                'seed': seed,
                'error': str(e),
                'reason': 'zero_spike_detection'
            }
            os.makedirs('data/logs', exist_ok=True)
            with open('data/logs/zero_spike_report.json', 'a') as f:
                json.dump(report, f)
                f.write('\n')

    # Save all metrics to CSV
    if all_metrics:
        df = pd.DataFrame(all_metrics)
        output_path = f'data/processed/{args.mode}_metrics.csv'
        os.makedirs('data/processed', exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()