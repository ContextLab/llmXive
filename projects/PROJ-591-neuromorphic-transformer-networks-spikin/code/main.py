import os
import sys
import argparse
import time
import json
import hashlib
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from metrics.perplexity import compute_perplexity
from metrics.energy_logger import EnergyLogger, EnergyRecord
from metrics.temporal_coding import collect_and_log_temporal_metrics
from models.baseline_transformer import create_baseline_model
from models.spiking_transformer import create_spiking_model, verify_surrogate_gradients
from data.dataset_loader import load_wikitext_dataset, get_wikitext_dataloader
from metrics.temporal_coding import extract_spike_trains_from_model_outputs

@dataclass
class MetricRecord:
    epoch: int
    perplexity: float
    energy_per_token_kWh: float
    wall_clock_time: float
    temporal_coding_metrics: Optional[Dict[str, float]] = None
    spike_outputs: Optional[Any] = None

class TrainingTerminationError(Exception):
    """Raised when training should be terminated early due to specific conditions."""
    pass

@dataclass
class TrainingConfig:
    model_type: str
    num_epochs: int
    batch_size: int
    learning_rate: float
    num_heads: int
    num_layers: int
    hidden_dim: int
    vocab_size: int
    max_seq_len: int
    early_stopping_patience: int
    log_dir: str

class EarlyStopping:
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
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
    import numpy as np
    np.random.seed(seed)

def save_zero_spike_report(log_dir: str, seed: int, epoch: int, metrics: Dict[str, Any]):
    """Save a diagnostic report for zero-spike detection."""
    os.makedirs(log_dir, exist_ok=True)
    report_path = os.path.join(log_dir, f"zero_spike_report_seed_{seed}_epoch_{epoch}.json")
    with open(report_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def check_zero_spike_condition(spike_outputs: Any, threshold: float = 0.5, window: int = 3) -> bool:
    """
    Check if more than threshold% of neurons are silent.
    
    Args:
        spike_outputs: Spike train outputs from the model
        threshold: Fraction of silent neurons to trigger condition
        window: Number of epochs to check (simplified for this implementation)
        
    Returns:
        True if zero-spike condition is met
    """
    spike_trains = extract_spike_trains_from_model_outputs(spike_outputs)
    if not spike_trains:
        return False
    
    # Calculate sparsity
    total_spikes = sum(train.sum().item() for train in spike_trains)
    total_elements = sum(train.numel() for train in spike_trains)
    
    if total_elements == 0:
        return True
    
    sparsity = 1.0 - (total_spikes / total_elements)
    return sparsity > threshold

def train_step(
    model: nn.Module,
    batch: Dict[str, torch.Tensor],
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, Any]:
    """Perform a single training step."""
    model.train()
    optimizer.zero_grad()
    
    inputs = batch['input_ids'].to(device)
    targets = batch['labels'].to(device)
    
    outputs = model(inputs)
    
    # Handle both regular and spiking model outputs
    if isinstance(outputs, dict):
        logits = outputs['logits']
        spike_outputs = outputs.get('spikes', None)
    else:
        logits = outputs
        spike_outputs = None
    
    loss = criterion(logits.view(-1, logits.size(-1)), targets.view(-1))
    loss.backward()
    
    # Verify gradients for spiking models
    if hasattr(model, 'verify_surrogate_gradients'):
        model.verify_surrogate_gradients()
    
    optimizer.step()
    
    return loss.item(), spike_outputs

def validate_step(
    model: nn.Module,
    batch: Dict[str, torch.Tensor],
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, Any]:
    """Perform a single validation step."""
    model.eval()
    
    inputs = batch['input_ids'].to(device)
    targets = batch['labels'].to(device)
    
    with torch.no_grad():
        outputs = model(inputs)
        
        if isinstance(outputs, dict):
            logits = outputs['logits']
            spike_outputs = outputs.get('spikes', None)
        else:
            logits = outputs
            spike_outputs = None
        
        loss = criterion(logits.view(-1, logits.size(-1)), targets.view(-1))
    
    return loss.item(), spike_outputs

def run_baseline_training(config: TrainingConfig, seed: int) -> List[MetricRecord]:
    """Run baseline transformer training."""
    setup_seed(seed)
    
    device = torch.device('cpu')
    model = create_baseline_model(
        vocab_size=config.vocab_size,
        hidden_dim=config.hidden_dim,
        num_heads=config.num_heads,
        num_layers=config.num_layers,
        max_seq_len=config.max_seq_len
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.CrossEntropyLoss()
    dataloader = get_wikitext_dataloader(config.batch_size, config.max_seq_len, split='train')
    val_dataloader = get_wikitext_dataloader(config.batch_size, config.max_seq_len, split='validation')
    
    energy_logger = EnergyLogger()
    early_stopping = EarlyStopping(patience=config.early_stopping_patience)
    
    records = []
    
    for epoch in range(config.num_epochs):
        start_time = time.time()
        total_loss = 0.0
        num_batches = 0
        
        model.train()
        for batch in dataloader:
            loss, _ = train_step(model, batch, optimizer, criterion, device)
            total_loss += loss
            num_batches += 1
        
        avg_train_loss = total_loss / num_batches
        
        # Validation
        val_loss = 0.0
        val_batches = 0
        model.eval()
        with torch.no_grad():
            for batch in val_dataloader:
                loss, _ = validate_step(model, batch, criterion, device)
                val_loss += loss
                val_batches += 1
        
        avg_val_loss = val_loss / val_batches
        perplexity = compute_perplexity(avg_val_loss)
        
        # Energy measurement
        energy_record = energy_logger.log_epoch(epoch, num_batches, config.batch_size)
        
        wall_clock_time = time.time() - start_time
        
        record = MetricRecord(
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token_kWh=energy_record.energy_per_token_kWh,
            wall_clock_time=wall_clock_time,
            temporal_coding_metrics=None,
            spike_outputs=None
        )
        records.append(record)
        
        if early_stopping(avg_val_loss):
            print(f"Early stopping at epoch {epoch}")
            break
    
    return records

def run_spiking_training(config: TrainingConfig, seed: int) -> List[MetricRecord]:
    """Run spiking transformer training."""
    setup_seed(seed)
    
    device = torch.device('cpu')
    model = create_spiking_model(
        vocab_size=config.vocab_size,
        hidden_dim=config.hidden_dim,
        num_heads=config.num_heads,
        num_layers=config.num_layers,
        max_seq_len=config.max_seq_len
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    criterion = nn.CrossEntropyLoss()
    dataloader = get_wikitext_dataloader(config.batch_size, config.max_seq_len, split='train')
    val_dataloader = get_wikitext_dataloader(config.batch_size, config.max_seq_len, split='validation')
    
    energy_logger = EnergyLogger()
    early_stopping = EarlyStopping(patience=config.early_stopping_patience)
    
    records = []
    silent_epochs = 0
    
    for epoch in range(config.num_epochs):
        start_time = time.time()
        total_loss = 0.0
        num_batches = 0
        all_spike_outputs = []
        
        model.train()
        for batch in dataloader:
            loss, spike_outputs = train_step(model, batch, optimizer, criterion, device)
            total_loss += loss
            num_batches += 1
            if spike_outputs is not None:
                all_spike_outputs.append(spike_outputs)
        
        avg_train_loss = total_loss / num_batches
        
        # Validation
        val_loss = 0.0
        val_batches = 0
        val_spike_outputs = []
        model.eval()
        with torch.no_grad():
            for batch in val_dataloader:
                loss, spike_outputs = validate_step(model, batch, criterion, device)
                val_loss += loss
                val_batches += 1
                if spike_outputs is not None:
                    val_spike_outputs.append(spike_outputs)
        
        avg_val_loss = val_loss / val_batches
        perplexity = compute_perplexity(avg_val_loss)
        
        # Energy measurement
        energy_record = energy_logger.log_epoch(epoch, num_batches, config.batch_size)
        
        # Temporal coding metrics
        temporal_metrics = None
        spike_outputs_for_logging = None
        
        if val_spike_outputs:
            # Combine spike outputs for analysis
            combined_spikes = torch.cat(val_spike_outputs, dim=0) if isinstance(val_spike_outputs[0], torch.Tensor) else val_spike_outputs
            temporal_metrics = collect_and_log_temporal_metrics(
                combined_spikes,
                "data/processed/temporal_metrics.csv",
                seed,
                epoch
            )
            spike_outputs_for_logging = combined_spikes
            
            # Check zero-spike condition
            if check_zero_spike_condition(combined_spikes):
                silent_epochs += 1
                if silent_epochs >= 3:
                    print(f"WARNING: Zero-spike detection triggered at epoch {epoch}")
                    save_zero_spike_report(
                        config.log_dir,
                        seed,
                        epoch,
                        {
                            'perplexity': perplexity,
                            'val_loss': avg_val_loss,
                            'sparsity': 1.0 - (combined_spikes.sum().item() / combined_spikes.numel())
                        }
                    )
                    raise TrainingTerminationError("Zero-spike condition met for 3 consecutive epochs")
            else:
                silent_epochs = 0
        
        wall_clock_time = time.time() - start_time
        
        record = MetricRecord(
            epoch=epoch,
            perplexity=perplexity,
            energy_per_token_kWh=energy_record.energy_per_token_kWh,
            wall_clock_time=wall_clock_time,
            temporal_coding_metrics=temporal_metrics,
            spike_outputs=spike_outputs_for_logging
        )
        records.append(record)
        
        if early_stopping(avg_val_loss):
            print(f"Early stopping at epoch {epoch}")
            break
    
    return records

def main():
    parser = argparse.ArgumentParser(description="Train baseline or spiking transformer")
    parser.add_argument("--model-type", type=str, choices=["baseline", "spiking"], default="spiking")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--num-epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--num-heads", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--vocab-size", type=int, default=10000)
    parser.add_argument("--max-seq-len", type=int, default=256)
    parser.add_argument("--early-stopping-patience", type=int, default=3)
    parser.add_argument("--log-dir", type=str, default="data/logs")
    
    args = parser.parse_args()
    
    config = TrainingConfig(
        model_type=args.model_type,
        num_epochs=args.num_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        num_heads=args.num_heads,
        num_layers=args.num_layers,
        hidden_dim=args.hidden_dim,
        vocab_size=args.vocab_size,
        max_seq_len=args.max_seq_len,
        early_stopping_patience=args.early_stopping_patience,
        log_dir=args.log_dir
    )
    
    if args.model_type == "baseline":
        records = run_baseline_training(config, args.seed)
    else:
        records = run_spiking_training(config, args.seed)
    
    print(f"Training completed. Recorded {len(records)} epochs.")
    for record in records:
        print(f"Epoch {record.epoch}: Perplexity={record.perplexity:.2f}, Energy={record.energy_per_token_kWh:.6f} kWh")

if __name__ == "__main__":
    main()