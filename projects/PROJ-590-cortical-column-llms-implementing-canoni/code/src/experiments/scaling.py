"""
Scaling laws experiment: Train variants with different column counts (1x, 2x, 4x)
to measure the scaling exponent of performance vs. parameter count.
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
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.data.benchmarks import generate_training_data, generate_test_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for a single scaling variant."""
    name: str
    scale_factor: float
    hidden_dim: int
    neurons_per_layer: int
    num_columns: int
    num_layers: int = 3
    dropout: float = 0.1
    learning_rate: float = 0.001
    epochs: int = 10
    batch_size: int = 32
    seed: int = 42

@dataclass
class ScalingResult:
    """Results from training a scaling variant."""
    name: str
    scale_factor: float
    num_params: int
    train_mae: float
    test_mae: float
    training_time: float
    config: ScalingConfig = field(default=None, repr=False)

def create_scaling_configs(base_config: Optional[Dict[str, Any]] = None) -> List[ScalingConfig]:
    """
    Generate scaling configurations: 1x (base), 2x, and 4x variants.
    
    Base config (1x):
      - hidden_dim: 64
      - neurons_per_layer: 128
      - num_columns: 1
      
    Variants double neurons_per_layer and num_columns to maintain columnar structure.
    """
    if base_config is None:
        base_config = {
            "hidden_dim": 64,
            "neurons_per_layer": 128,
            "num_columns": 1,
            "num_layers": 3,
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 0.001,
            "dropout": 0.1,
            "seed": 42
        }
    
    scale_factors = [1.0, 2.0, 4.0]
    configs = []
    
    for scale in scale_factors:
        config = ScalingConfig(
            name=f"scale_{int(scale)}x" if scale > 1.0 else "scale_1x",
            scale_factor=scale,
            hidden_dim=int(base_config["hidden_dim"] * scale),
            neurons_per_layer=int(base_config["neurons_per_layer"] * scale),
            num_columns=int(base_config["num_columns"] * scale),
            num_layers=base_config["num_layers"],
            epochs=base_config["epochs"],
            batch_size=base_config["batch_size"],
            learning_rate=base_config["learning_rate"],
            dropout=base_config["dropout"],
            seed=base_config["seed"]
        )
        configs.append(config)
    
    return configs

def count_parameters(model: nn.Module) -> int:
    """Count total trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def create_model_from_config(config: ScalingConfig) -> HybridNetwork:
    """
    Create a HybridNetwork model from a ScalingConfig.
    
    The model is created with the specified hidden dimensions and column count.
    """
    model = create_hybrid_network(
        hidden_dim=config.hidden_dim,
        num_columns=config.num_columns,
        num_layers=config.num_layers,
        neurons_per_column=config.neurons_per_layer,
        dropout=config.dropout,
        seed=config.seed
    )
    return model

def train_scaling_variant(config: ScalingConfig, output_dir: str = "data/results") -> ScalingResult:
    """
    Train a single scaling variant and return results.
    
    This function:
    1. Creates the model from config
    2. Generates training and test data (deterministic)
    3. Trains the model
    4. Calculates MAE on train and test sets
    5. Returns ScalingResult with metrics and parameter count
    """
    logger.info(f"Starting training for {config.name} (scale={config.scale_factor}x)")
    start_time = time.time()
    
    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    
    # Create model
    model = create_model_from_config(config)
    num_params = count_parameters(model)
    logger.info(f"{config.name}: {num_params:,} parameters")
    
    # Generate data
    train_data = generate_training_data(
        num_samples=1000,
        sequence_length=50,
        seed=config.seed
    )
    test_data = generate_test_data(
        num_samples=200,
        sequence_length=50,
        seed=config.seed + 1000  # Different seed for test set
    )
    
    # Convert to tensors
    X_train = torch.FloatTensor(train_data['X'])
    y_train = torch.FloatTensor(train_data['y'])
    X_test = torch.FloatTensor(test_data['X'])
    y_test = torch.FloatTensor(test_data['y'])
    
    # Create training config
    train_config = TrainingConfig(
        epochs=config.epochs,
        batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        weight_decay=1e-4,
        gradient_clip=1.0,
        log_dir=os.path.join(output_dir, "logs"),
        device="cpu"
    )
    
    # Train model
    logger.info(f"Training {config.name} for {config.epochs} epochs...")
    metrics = run_training(
        model=model,
        train_loader=torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_train, y_train),
            batch_size=config.batch_size,
            shuffle=True
        ),
        test_loader=torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_test, y_test),
            batch_size=config.batch_size,
            shuffle=False
        ),
        config=train_config,
        optimizer=torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=1e-4)
    )
    
    # Calculate final MAE
    model.eval()
    with torch.no_grad():
        train_pred = model(X_train)
        test_pred = model(X_test)
        train_mae = calculate_mae(train_pred, y_train)
        test_mae = calculate_mae(test_pred, y_test)
    
    training_time = time.time() - start_time
    
    logger.info(f"{config.name} completed in {training_time:.2f}s")
    logger.info(f"  Train MAE: {train_mae:.4f}, Test MAE: {test_mae:.4f}")
    
    return ScalingResult(
        name=config.name,
        scale_factor=config.scale_factor,
        num_params=num_params,
        train_mae=train_mae,
        test_mae=test_mae,
        training_time=training_time,
        config=config
    )

def run_scaling_study(
    base_config: Optional[Dict[str, Any]] = None,
    output_path: str = "data/results/scaling_results.json"
) -> List[ScalingResult]:
    """
    Run the full scaling study across all variants.
    
    Args:
        base_config: Base configuration for 1x variant. If None, uses defaults.
        output_path: Path to save results JSON.
        
    Returns:
        List of ScalingResult objects for each variant.
    """
    logger.info("Starting scaling study")
    
    # Generate configs
    configs = create_scaling_configs(base_config)
    logger.info(f"Generated {len(configs)} scaling configurations")
    
    results = []
    for config in configs:
        try:
            result = train_scaling_variant(config, output_dir=os.path.dirname(output_path))
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {config.name}: {e}")
            raise
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_data = {
        "variants": [
            {
                "columns": r.name,
                "params": r.num_params,
                "mae": round(r.test_mae, 4),
                "time": round(r.training_time, 2)
            }
            for r in results
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return results

def main():
    """Entry point for scaling experiment script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run scaling study for cortical column LLMs")
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/scaling_results.json",
        help="Output path for results JSON"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=10,
        help="Number of training epochs per variant"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Create base config with custom epochs and seed
    base_config = {
        "hidden_dim": 64,
        "neurons_per_layer": 128,
        "num_columns": 1,
        "num_layers": 3,
        "epochs": args.epochs,
        "batch_size": 32,
        "learning_rate": 0.001,
        "dropout": 0.1,
        "seed": args.seed
    }
    
    results = run_scaling_study(base_config=base_config, output_path=args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("SCALING STUDY SUMMARY")
    print("="*60)
    for r in results:
        print(f"{r.name:12s} | Params: {r.num_params:8d} | MAE: {r.test_mae:.4f} | Time: {r.training_time:.2f}s")
    print("="*60)

if __name__ == "__main__":
    main()
