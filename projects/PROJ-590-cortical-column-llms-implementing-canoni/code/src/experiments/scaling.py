"""
Scaling experiments for cortical column LLMs.

Varies column count (1x, 2x, 4x) to measure scaling laws.
Base configuration: hidden_dim=64, neurons_per_layer=128.
"""

import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

import torch
import torch.nn as nn

from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.models.microcircuit import MicrocircuitColumn
from src.training.trainer import run_training, TrainingConfig
from src.data.benchmarks import generate_synthetic_dataset
from src.training.homeostasis import HomeostasisConfig, log_gradient_norms

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base configuration constants
BASE_HIDDEN_DIM = 64
BASE_NEURONS_PER_LAYER = 128
BASE_COLUMNS = 1

@dataclass
class ScalingConfig:
    """Configuration for a scaling variant."""
    multiplier: float
    column_count: int
    hidden_dim: int
    neurons_per_layer: int
    num_layers: int = 4
    dropout: float = 0.1
    learning_rate: float = 1e-4
    batch_size: int = 32
    num_epochs: int = 10
    seed: int = 42
    experiment_name: str = field(default="")
    
    def __post_init__(self):
        if not self.experiment_name:
            self.experiment_name = f"scaling_{self.multiplier}x"

@dataclass
class ScalingResult:
    """Result from a scaling experiment."""
    multiplier: float
    column_count: int
    total_parameters: int
    train_mae: float
    test_mae: float
    training_time_seconds: float
    peak_memory_mb: float
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def create_scaling_configs() -> List[ScalingConfig]:
    """
    Create scaling configurations for 1x, 2x, 4x column counts.
    
    Base: hidden_dim=64, neurons_per_layer=128, columns=1
    2x: hidden_dim=128, neurons_per_layer=256, columns=2
    4x: hidden_dim=256, neurons_per_layer=512, columns=4
    """
    configs = []
    
    # 1x configuration (base)
    config_1x = ScalingConfig(
        multiplier=1.0,
        column_count=1,
        hidden_dim=BASE_HIDDEN_DIM,
        neurons_per_layer=BASE_NEURONS_PER_LAYER
    )
    configs.append(config_1x)
    
    # 2x configuration
    config_2x = ScalingConfig(
        multiplier=2.0,
        column_count=2,
        hidden_dim=int(BASE_HIDDEN_DIM * 2),
        neurons_per_layer=int(BASE_NEURONS_PER_LAYER * 2)
    )
    configs.append(config_2x)
    
    # 4x configuration
    config_4x = ScalingConfig(
        multiplier=4.0,
        column_count=4,
        hidden_dim=int(BASE_HIDDEN_DIM * 4),
        neurons_per_layer=int(BASE_NEURONS_PER_LAYER * 4)
    )
    configs.append(config_4x)
    
    logger.info(f"Created {len(configs)} scaling configurations")
    for cfg in configs:
        logger.info(f"  {cfg.experiment_name}: columns={cfg.column_count}, "
                   f"hidden_dim={cfg.hidden_dim}, neurons={cfg.neurons_per_layer}")
    
    return configs

def save_configs(configs: List[ScalingConfig], output_path: str) -> None:
    """Save scaling configurations to JSON file."""
    data = [asdict(cfg) for cfg in configs]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(configs)} configs to {output_path}")

def create_model_from_config(config: ScalingConfig) -> HybridNetwork:
    """
    Create a HybridNetwork model based on scaling configuration.
    
    Uses MicrocircuitColumn modules with the specified dimensions.
    """
    # Create the model with scaled parameters
    model = create_hybrid_network(
        num_columns=config.column_count,
        hidden_dim=config.hidden_dim,
        neurons_per_layer=config.neurons_per_layer,
        num_layers=config.num_layers,
        dropout=config.dropout
    )
    
    logger.info(f"Created model with {sum(p.numel() for p in model.parameters()):,} parameters")
    return model

def train_scaling_variant(config: ScalingConfig) -> ScalingResult:
    """
    Train a single scaling variant and return results.
    
    Args:
        config: Scaling configuration for this variant
    
    Returns:
        ScalingResult with training metrics
    """
    logger.info(f"Starting training for {config.experiment_name}")
    
    # Set random seed
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(config.seed)
    
    # Generate synthetic datasets
    logger.info("Generating synthetic datasets...")
    train_data = generate_synthetic_dataset(
        task='lorenz',
        num_samples=1000,
        seed=config.seed,
        noise_level=0.1
    )
    test_data = generate_synthetic_dataset(
        task='lorenz',
        num_samples=500,
        seed=config.seed + 1,
        noise_level=0.1
    )
    
    # Create model
    model = create_model_from_config(config)
    
    # Configure training
    training_config = TrainingConfig(
        learning_rate=config.learning_rate,
        batch_size=config.batch_size,
        num_epochs=config.num_epochs,
        weight_decay=1e-4,
        gradient_clip=1.0,
        log_interval=10,
        save_dir='data/results'
    )
    
    # Homeostasis config (optional, can be disabled for ablation)
    homeostasis_config = HomeostasisConfig(
        target_ei_ratio=4.0,
        decay_rate=0.01,
        enabled=True
    )
    
    # Train the model
    logger.info(f"Training {config.experiment_name}...")
    result = run_training(
        model=model,
        train_data=train_data,
        test_data=test_data,
        config=training_config,
        homeostasis_config=homeostasis_config,
        device='cpu'
    )
    
    # Create result object
    scaling_result = ScalingResult(
        multiplier=config.multiplier,
        column_count=config.column_count,
        total_parameters=sum(p.numel() for p in model.parameters()),
        train_mae=result.train_mae,
        test_mae=result.test_mae,
        training_time_seconds=result.training_time_seconds,
        peak_memory_mb=result.peak_memory_mb,
        config=asdict(config)
    )
    
    logger.info(f"Completed {config.experiment_name}: "
               f"train_mae={result.train_mae:.4f}, "
               f"test_mae={result.test_mae:.4f}, "
               f"params={scaling_result.total_parameters:,}")
    
    return scaling_result

def run_scaling_study(output_dir: str = 'data/results') -> List[ScalingResult]:
    """
    Run the full scaling study across all variants.
    
    Args:
        output_dir: Directory to save results
    
    Returns:
        List of ScalingResult objects
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create configurations
    configs = create_scaling_configs()
    
    # Save configurations
    config_path = os.path.join(output_dir, 'scaling_configs.json')
    save_configs(configs, config_path)
    
    # Train each variant
    results = []
    for config in configs:
        try:
            result = train_scaling_variant(config)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {config.experiment_name}: {e}")
            raise
    
    # Save results
    results_path = os.path.join(output_dir, 'scaling_results.json')
    results_data = [r.to_dict() for r in results]
    with open(results_path, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    logger.info(f"Saved scaling results to {results_path}")
    return results

def main():
    """Main entry point for scaling experiments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run scaling experiments')
    parser.add_argument('--output-dir', type=str, default='data/results',
                      help='Output directory for results')
    parser.add_argument('--config-only', action='store_true',
                      help='Only generate configs, do not train')
    args = parser.parse_args()
    
    logger.info("Starting scaling experiments")
    
    if args.config_only:
        configs = create_scaling_configs()
        save_configs(configs, os.path.join(args.output_dir, 'scaling_configs.json'))
        logger.info("Generated configs only")
        return
    
    results = run_scaling_study(args.output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("SCALING STUDY RESULTS")
    print("="*60)
    print(f"{'Multiplier':<12} {'Columns':<10} {'Params':<15} {'Train MAE':<12} {'Test MAE':<12}")
    print("-"*60)
    for r in results:
        print(f"{r.multiplier:<12.1f}x {r.column_count:<10} {r.total_parameters:<15,} "
              f"{r.train_mae:<12.4f} {r.test_mae:<12.4f}")
    print("="*60)

if __name__ == '__main__':
    main()
