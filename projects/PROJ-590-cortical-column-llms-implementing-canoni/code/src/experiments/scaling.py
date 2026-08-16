import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

import torch
import torch.nn as nn
import numpy as np

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.training.homeostasis import log_gradient_norms, apply_scaling_hook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for a specific scaling variant."""
    name: str
    hidden_dim: int
    neurons_per_layer: int
    num_columns: int
    num_layers: int = 4  # L4, L2/3, L5, L6
    seed: int = 42
    epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 1e-3

@dataclass
class ScalingResult:
    """Result of training a specific scaling variant."""
    name: str
    columns: str
    params: int
    mae: float
    time: float
    seed: int

def create_scaling_configs() -> List[ScalingConfig]:
    """
    Generate configuration objects for scaling variants.
    Base config: hidden_dim=64, neurons_per_layer=128.
    Variants: 1x (base), 2x (double neurons), 4x (quadruple neurons).
    """
    base_hidden = 64
    base_neurons = 128
    
    configs = [
        ScalingConfig(
            name="1x",
            hidden_dim=base_hidden,
            neurons_per_layer=base_neurons,
            num_columns=1,
            seed=42,
            epochs=5,
            batch_size=32,
            learning_rate=1e-3
        ),
        ScalingConfig(
            name="2x",
            hidden_dim=base_hidden * 2,
            neurons_per_layer=base_neurons * 2,
            num_columns=2,
            seed=42,
            epochs=5,
            batch_size=32,
            learning_rate=1e-3
        ),
        ScalingConfig(
            name="4x",
            hidden_dim=base_hidden * 4,
            neurons_per_layer=base_neurons * 4,
            num_columns=4,
            seed=42,
            epochs=5,
            batch_size=32,
            learning_rate=1e-3
        )
    ]
    return configs

def count_parameters(model: nn.Module) -> int:
    """Count total trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def create_model_from_config(config: ScalingConfig) -> nn.Module:
    """
    Create a HybridNetwork model based on scaling configuration.
    Uses MicrocircuitColumn with specified neurons_per_layer and num_columns.
    """
    # Create a microcircuit column with the specified parameters
    # The HybridNetwork wraps microcircuit columns in a transformer-like structure
    model = create_hybrid_network(
        hidden_dim=config.hidden_dim,
        num_columns=config.num_columns,
        neurons_per_layer=config.neurons_per_layer,
        num_layers=config.num_layers,
        dropout=0.1
    )
    return model

def train_scaling_variant(config: ScalingConfig) -> ScalingResult:
    """
    Train a single scaling variant and return results.
    
    Args:
        config: ScalingConfig for this variant
        
    Returns:
        ScalingResult with MAE, parameters, and training time
    """
    logger.info(f"Training scaling variant: {config.name}")
    logger.info(f"  hidden_dim={config.hidden_dim}, neurons_per_layer={config.neurons_per_layer}, num_columns={config.num_columns}")
    
    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    
    # Generate training and test data
    logger.info("Generating training data (Lorenz attractor)...")
    train_X, train_y = generate_training_data(seed=config.seed)
    
    logger.info("Generating test data (Polynomials/Fourier)...")
    test_X, test_y = generate_test_data(seed=config.seed + 1)
    
    # Verify independence of distributions
    logger.info("Verifying data independence...")
    verify_independence(train_X, test_X)
    
    # Create model
    model = create_model_from_config(config)
    param_count = count_parameters(model)
    logger.info(f"Model parameters: {param_count}")
    
    # Configure training
    training_config = TrainingConfig(
        epochs=config.epochs,
        batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        seed=config.seed,
        gradient_clip=1.0,
        log_gradients=True,
        log_path="data/logs/gradient_norms_scaling.json"
    )
    
    # Train model
    start_time = time.time()
    logger.info(f"Starting training for {config.epochs} epochs...")
    
    try:
        metrics = run_training(
            model=model,
            train_data=(train_X, train_y),
            test_data=(test_X, test_y),
            config=training_config
        )
    except Exception as e:
        logger.error(f"Training failed for {config.name}: {e}")
        raise
    
    training_time = time.time() - start_time
    logger.info(f"Training completed in {training_time:.2f} seconds")
    
    # Calculate MAE on test set
    model.eval()
    with torch.no_grad():
        test_pred = model(test_X)
        test_mae = calculate_mae(test_pred, test_y)
    
    logger.info(f"Test MAE for {config.name}: {test_mae:.6f}")
    
    # Log gradient norms for SC-002 verification
    log_gradient_norms(model, step=0)
    
    return ScalingResult(
        name=config.name,
        columns=f"{config.num_columns}x",
        params=param_count,
        mae=round(test_mae, 4),
        time=round(training_time, 2),
        seed=config.seed
    )

def run_scaling_study() -> List[ScalingResult]:
    """
    Run scaling study across all variants and aggregate results.
    
    Returns:
        List of ScalingResult objects for all variants
    """
    logger.info("Starting scaling study...")
    
    # Generate configurations
    configs = create_scaling_configs()
    
    # Train each variant
    results = []
    for config in configs:
        try:
            result = train_scaling_variant(config)
            results.append(result)
            logger.info(f"Completed {config.name}: MAE={result.mae}, Params={result.params}, Time={result.time}s")
        except Exception as e:
            logger.error(f"Failed to train {config.name}: {e}")
            # Continue with other variants
            continue
    
    if not results:
        raise RuntimeError("No scaling variants completed successfully")
    
    return results

def save_scaling_results(results: List[ScalingResult], output_path: str = "data/results/scaling_results.json") -> None:
    """
    Save scaling results to JSON file.
    
    Args:
        results: List of ScalingResult objects
        output_path: Path to output JSON file
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert to dict format matching schema
    output = {
        "variants": [
            {
                "columns": r.columns,
                "params": r.params,
                "mae": r.mae,
                "time": r.time
            }
            for r in results
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved scaling results to {output_path}")

def main():
    """Main entry point for scaling study."""
    logger.info("=== Scaling Study Execution ===")
    
    # Run scaling study
    results = run_scaling_study()
    
    # Save results
    save_scaling_results(results)
    
    logger.info("=== Scaling Study Completed ===")
    
    # Print summary
    print("\nScaling Results Summary:")
    print("-" * 60)
    print(f"{'Variant':<10} {'Columns':<10} {'Params':<12} {'MAE':<10} {'Time (s)':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r.name:<10} {r.columns:<10} {r.params:<12} {r.mae:<10.4f} {r.time:<10.2f}")
    print("-" * 60)

if __name__ == "__main__":
    main()
