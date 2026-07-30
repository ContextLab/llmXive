"""
Scaling experiments for Cortical Column LLMs.

This module implements the scaling study to vary column count and neuron counts
to analyze the scaling laws of the microcircuit-based architecture.

Outputs:
    data/results/scaling_results.json: Results of scaling variants
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
import numpy as np

# Import from project modules
from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.models.microcircuit import MicrocircuitColumnConfig, LayerConfig
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.data.benchmarks import generate_training_data, generate_test_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ScalingConfig:
    """Configuration for a scaling variant."""
    name: str
    columns: int
    neurons_per_layer: int
    hidden_dim: int = 64
    num_layers: int = 4
    dropout: float = 0.1
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    seed: int = 42
    
@dataclass
class ScalingResult:
    """Result from training a scaling variant."""
    variant_name: str
    columns: int
    neurons_per_layer: int
    total_params: int
    train_mae: float
    test_mae: float
    training_time: float
    peak_memory_mb: float
    

def create_scaling_configs(base_config: Optional[Dict[str, Any]] = None) -> List[ScalingConfig]:
    """
    Generate scaling configurations by varying column count and neuron density.
    
    Args:
        base_config: Optional base configuration to override defaults.
    
    Returns:
        List of ScalingConfig objects for 1x, 2x, 4x variants.
    """
    defaults = {
        'hidden_dim': 64,
        'neurons_per_layer': 128,
        'num_layers': 4,
        'epochs': 10,
        'learning_rate': 0.001,
        'batch_size': 32,
        'seed': 42
    }
    
    if base_config:
        defaults.update(base_config)
    
    configs = []
    
    # 1x variant (baseline)
    configs.append(ScalingConfig(
        name='1x_baseline',
        columns=1,
        neurons_per_layer=defaults['neurons_per_layer'],
        hidden_dim=defaults['hidden_dim'],
        num_layers=defaults['num_layers'],
        epochs=defaults['epochs'],
        learning_rate=defaults['learning_rate'],
        batch_size=defaults['batch_size'],
        seed=defaults['seed']
    ))
    
    # 2x variant (double neurons)
    configs.append(ScalingConfig(
        name='2x_neurons',
        columns=2,
        neurons_per_layer=defaults['neurons_per_layer'] * 2,
        hidden_dim=defaults['hidden_dim'],
        num_layers=defaults['num_layers'],
        epochs=defaults['epochs'],
        learning_rate=defaults['learning_rate'],
        batch_size=defaults['batch_size'],
        seed=defaults['seed']
    ))
    
    # 4x variant (quadruple neurons)
    configs.append(ScalingConfig(
        name='4x_neurons',
        columns=4,
        neurons_per_layer=defaults['neurons_per_layer'] * 4,
        hidden_dim=defaults['hidden_dim'],
        num_layers=defaults['num_layers'],
        epochs=defaults['epochs'],
        learning_rate=defaults['learning_rate'],
        batch_size=defaults['batch_size'],
        seed=defaults['seed']
    ))
    
    return configs


def create_model_from_config(config: ScalingConfig) -> HybridNetwork:
    """
    Create a HybridNetwork model from a ScalingConfig.
    
    Args:
        config: Scaling configuration.
    
    Returns:
        Initialized HybridNetwork model.
    """
    logger.info(f"Creating model for variant: {config.name}")
    logger.info(f"  Columns: {config.columns}, Neurons/layer: {config.neurons_per_layer}")
    
    # Create microcircuit column config
    column_config = MicrocircuitColumnConfig(
        num_columns=config.columns,
        neurons_per_layer=config.neurons_per_layer,
        hidden_dim=config.hidden_dim,
        dropout=config.dropout
    )
    
    # Create the hybrid network
    model = create_hybrid_network(
        num_columns=config.columns,
        neurons_per_layer=config.neurons_per_layer,
        hidden_dim=config.hidden_dim,
        num_layers=config.num_layers,
        dropout=config.dropout
    )
    
    return model


def count_parameters(model: nn.Module) -> int:
    """Count total trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_scaling_variant(config: ScalingConfig) -> ScalingResult:
    """
    Train a single scaling variant and return results.
    
    Args:
        config: Scaling configuration.
    
    Returns:
        ScalingResult with metrics and timing.
    """
    logger.info(f"Starting training for variant: {config.name}")
    
    # Set random seed for reproducibility
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    
    # Generate data
    logger.info("Generating training and test data...")
    train_data = generate_training_data(seed=config.seed)
    test_data = generate_test_data(seed=config.seed + 1000)  # Different seed for independence
    
    # Create model
    model = create_model_from_config(config)
    total_params = count_parameters(model)
    logger.info(f"Model created with {total_params:,} parameters")
    
    # Configure training
    training_config = TrainingConfig(
        epochs=config.epochs,
        batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        gradient_clip=1.0,
        seed=config.seed,
        log_gradients=True,
        homeostasis_enabled=True
    )
    
    # Train
    start_time = time.time()
    logger.info(f"Starting training for {config.epochs} epochs...")
    
    try:
        metrics = run_training(
            model=model,
            train_data=train_data,
            test_data=test_data,
            config=training_config,
            variant_name=config.name
        )
    except Exception as e:
        logger.error(f"Training failed for {config.name}: {e}")
        raise
    
    training_time = time.time() - start_time
    
    # Calculate final metrics
    train_mae = metrics.get('train_mae', 0.0)
    test_mae = metrics.get('test_mae', 0.0)
    peak_memory = metrics.get('peak_memory_mb', 0.0)
    
    logger.info(f"Training completed for {config.name}")
    logger.info(f"  Train MAE: {train_mae:.4f}")
    logger.info(f"  Test MAE: {test_mae:.4f}")
    logger.info(f"  Training time: {training_time:.2f}s")
    
    return ScalingResult(
        variant_name=config.name,
        columns=config.columns,
        neurons_per_layer=config.neurons_per_layer,
        total_params=total_params,
        train_mae=round(train_mae, 4),
        test_mae=round(test_mae, 4),
        training_time=round(training_time, 2),
        peak_memory_mb=round(peak_memory, 2)
    )


def run_scaling_study(
    configs: Optional[List[ScalingConfig]] = None,
    output_path: str = "data/results/scaling_results.json"
) -> List[ScalingResult]:
    """
    Run the full scaling study across all variants.
    
    Args:
        configs: List of scaling configurations (defaults to 1x, 2x, 4x).
        output_path: Path to save results JSON.
    
    Returns:
        List of ScalingResult objects.
    """
    if configs is None:
        configs = create_scaling_configs()
    
    logger.info(f"Running scaling study with {len(configs)} variants")
    
    results = []
    for config in configs:
        try:
            result = train_scaling_variant(config)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train variant {config.name}: {e}")
            # Continue with other variants
            continue
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results_dict = {
        "variants": [
            {
                "name": r.variant_name,
                "columns": r.columns,
                "neurons_per_layer": r.neurons_per_layer,
                "params": r.total_params,
                "train_mae": r.train_mae,
                "test_mae": r.test_mae,
                "time": r.training_time,
                "peak_memory_mb": r.peak_memory_mb
            }
            for r in results
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    logger.info(f"Scaling results saved to {output_path}")
    
    return results


def main():
    """Main entry point for scaling study."""
    logger.info("Starting scaling study...")
    
    # Run the study
    results = run_scaling_study()
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SCALING STUDY SUMMARY")
    logger.info("="*60)
    
    for r in results:
        logger.info(f"{r.variant_name}:")
        logger.info(f"  Columns: {r.columns}, Neurons/layer: {r.neurons_per_layer}")
        logger.info(f"  Parameters: {r.total_params:,}")
        logger.info(f"  Train MAE: {r.train_mae:.4f}")
        logger.info(f"  Test MAE: {r.test_mae:.4f}")
        logger.info(f"  Time: {r.training_time:.2f}s")
    
    logger.info("="*60)
    
    return results


if __name__ == "__main__":
    main()
