"""
Scaling study for Cortical Column LLMs.
Varies column count (1x, 2x, 4x) and trains on standard synthetic tasks.
"""
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Import from existing project modules
from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.models.microcircuit import create_microcircuit_column
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import run_training, TrainingConfig, calculate_mae
from src.training.homeostasis import apply_scaling_hook, HomeostasisConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for a single scaling variant."""
    name: str
    columns: int
    hidden_dim: int
    neurons_per_layer: int
    num_layers: int = 4
    seq_len: int = 100
    batch_size: int = 32
    epochs: int = 10
    learning_rate: float = 1e-3
    seed: int = 42

@dataclass
class ScalingResult:
    """Result of training a scaling variant."""
    variant: str
    columns: int
    params: int
    mae: float
    time: float

def create_scaling_configs() -> List[ScalingConfig]:
    """
    Generate configurations for 1x, 2x, and 4x scaling.
    Base: hidden_dim=64, neurons_per_layer=128
    """
    base_hidden_dim = 64
    base_neurons = 128
    base_layers = 4

    configs = [
        ScalingConfig(
            name="1x_baseline",
            columns=1,
            hidden_dim=base_hidden_dim,
            neurons_per_layer=base_neurons,
            num_layers=base_layers
        ),
        ScalingConfig(
            name="2x_scaled",
            columns=2,
            hidden_dim=base_hidden_dim,
            neurons_per_layer=base_neurons * 2,
            num_layers=base_layers
        ),
        ScalingConfig(
            name="4x_scaled",
            columns=4,
            hidden_dim=base_hidden_dim,
            neurons_per_layer=base_neurons * 4,
            num_layers=base_layers
        ),
    ]
    return configs

def create_model_from_config(config: ScalingConfig) -> HybridNetwork:
    """
    Instantiate a HybridNetwork with the specified scaling parameters.
    The 'columns' argument determines the number of microcircuit columns
    repeated in the network.
    """
    logger.info(f"Creating model for {config.name}: columns={config.columns}, neurons={config.neurons_per_layer}")

    # Create a microcircuit column with the specified neuron count
    # We assume the HybridNetwork accepts a 'num_columns' and 'neurons_per_layer'
    # The create_hybrid_network function needs to be adapted to accept these params
    # For now, we construct the model manually to ensure correct parameterization

    # We'll create a standard HybridNetwork but modify its internal structure
    # to reflect the scaling. Since create_hybrid_network is the public API,
    # we pass the scaled neurons_per_layer.
    # Note: The 'columns' parameter is handled by repeating the microcircuit
    # module 'columns' times in the network.

    # Construct the microcircuit column
    microcircuit = create_microcircuit_column(
        neurons_per_layer=config.neurons_per_layer,
        num_layers=config.num_layers
    )

    # Create the hybrid network with the scaled microcircuit
    # We assume HybridNetwork can accept a custom microcircuit module
    model = HybridNetwork(
        microcircuit=microcircuit,
        num_columns=config.columns,
        hidden_dim=config.hidden_dim
    )

    return model

def count_parameters(model: nn.Module) -> int:
    """Count total trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def train_scaling_variant(config: ScalingConfig) -> ScalingResult:
    """
    Train a single scaling variant and return the result.
    """
    logger.info(f"Starting training for {config.name}")
    start_time = time.time()

    # Set seed for reproducibility
    torch.manual_seed(config.seed)

    # Generate data
    train_data, train_labels = generate_training_data(
        n_samples=1000,
        seq_len=config.seq_len,
        seed=config.seed
    )
    test_data, test_labels = generate_test_data(
        n_samples=500,
        seq_len=config.seq_len,
        seed=config.seed + 1
    )

    # Convert to tensors
    train_dataset = TensorDataset(train_data, train_labels)
    test_dataset = TensorDataset(test_data, test_labels)

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=config.batch_size, shuffle=False)

    # Create model
    model = create_model_from_config(config)
    num_params = count_parameters(model)
    logger.info(f"Model {config.name} has {num_params} parameters")

    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)

    # Training config
    training_config = TrainingConfig(
        epochs=config.epochs,
        learning_rate=config.learning_rate,
        device="cpu",
        gradient_clip=1.0,
        log_interval=10
    )

    # Homeostasis config (optional, can be disabled if needed)
    homeostasis_config = HomeostasisConfig(
        enabled=True,
        target_ei_ratio=4.0,
        decay_rate=0.01
    )

    # Train
    # Note: run_training expects a model, optimizer, loaders, and config
    # We need to ensure it supports homeostasis
    try:
        metrics = run_training(
            model=model,
            optimizer=optimizer,
            train_loader=train_loader,
            test_loader=test_loader,
            config=training_config,
            homeostasis_config=homeostasis_config,
            apply_scaling_hook_fn=apply_scaling_hook
        )
    except Exception as e:
        logger.error(f"Training failed for {config.name}: {e}")
        raise

    elapsed_time = time.time() - start_time

    # Evaluate final MAE
    model.eval()
    all_preds = []
    all_targets = []
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            outputs = model(batch_x)
            all_preds.append(outputs.numpy() if hasattr(outputs, 'numpy') else outputs.cpu().numpy())
            all_targets.append(batch_y.numpy() if hasattr(batch_y, 'numpy') else batch_y.cpu().numpy())

    import numpy as np
    preds = np.concatenate(all_preds, axis=0)
    targets = np.concatenate(all_targets, axis=0)
    mae = calculate_mae(preds, targets)

    logger.info(f"Completed {config.name}: MAE={mae:.4f}, Time={elapsed_time:.2f}s")

    return ScalingResult(
        variant=config.name,
        columns=config.columns,
        params=num_params,
        mae=float(mae),
        time=float(elapsed_time)
    )

def run_scaling_study(output_path: str = "data/results/scaling_results.json") -> List[ScalingResult]:
    """
    Run the full scaling study (1x, 2x, 4x) and save results.
    """
    logger.info("Starting scaling study")

    configs = create_scaling_configs()
    results = []

    for config in configs:
        try:
            result = train_scaling_variant(config)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {config.name}: {e}")
            # Re-raise to ensure failure is caught
            raise

    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_data = {
        "variants": [asdict(r) for r in results]
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Scaling study complete. Results saved to {output_path}")
    return results

def main():
    """Entry point for the scaling study script."""
    output_path = "data/results/scaling_results.json"
    run_scaling_study(output_path)

if __name__ == "__main__":
    main()
