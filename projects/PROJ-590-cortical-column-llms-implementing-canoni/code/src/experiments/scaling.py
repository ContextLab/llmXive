import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column
from src.models.hybrid_network import HybridNetwork, create_hybrid_network
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.training.homeostasis import HomeostasisConfig, HomeostaticScaler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for a specific scaling variant (1x, 2x, 4x)."""
    variant_name: str
    scale_factor: float
    hidden_dim: int
    neurons_per_layer: int
    num_columns: int
    num_layers: int
    seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ScalingResult:
    """Results from training a specific scaling variant."""
    variant_name: str
    scale_factor: float
    num_parameters: int
    train_mae: float
    test_mae: float
    training_time_seconds: float
    config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def create_scaling_configs(base_hidden_dim: int = 64, base_neurons: int = 128) -> List[ScalingConfig]:
    """
    Generate deterministic scaling configurations for 1x, 2x, and 4x variants.
    
    Base 1x: hidden_dim=64, neurons_per_layer=128
    2x: hidden_dim=128, neurons_per_layer=256
    4x: hidden_dim=256, neurons_per_layer=512
    """
    variants = []
    scales = [1.0, 2.0, 4.0]
    names = ["1x", "2x", "4x"]
    
    for i, scale in enumerate(scales):
        variants.append(
            ScalingConfig(
                variant_name=names[i],
                scale_factor=scale,
                hidden_dim=int(base_hidden_dim * scale),
                neurons_per_layer=int(base_neurons * scale),
                num_columns=4,  # Fixed number of columns for this study
                num_layers=3,   # Fixed depth
                seed=42
            )
        )
    
    return variants

def create_model_from_config(config: ScalingConfig) -> HybridNetwork:
    """Create a HybridNetwork model based on scaling configuration."""
    logger.info(f"Creating model for {config.variant_name}: "
               f"hidden={config.hidden_dim}, neurons={config.neurons_per_layer}, "
               f"columns={config.num_columns}")
    
    # Create the microcircuit column with scaled parameters
    column = create_microcircuit_column(
        input_dim=config.hidden_dim,
        hidden_dim=config.hidden_dim,
        neurons_per_layer=config.neurons_per_layer,
        num_layers=config.num_layers
    )
    
    # Wrap in hybrid network
    model = create_hybrid_network(
        input_dim=config.hidden_dim,
        output_dim=config.hidden_dim,  # Auto-regressive prediction
        microcircuit_column=column,
        num_columns=config.num_columns
    )
    
    return model

def train_scaling_variant(
    config: ScalingConfig,
    train_epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
    use_homeostasis: bool = True
) -> ScalingResult:
    """
    Train a single scaling variant and return results.
    
    This function:
    1. Generates synthetic training/test data (Lorenz/Polynomials)
    2. Creates the scaled model
    3. Trains for a fixed number of epochs
    4. Measures MAE on train and test sets
    5. Returns structured results
    """
    logger.info(f"Starting training for {config.variant_name}")
    
    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    
    # Generate data
    logger.info("Generating training data (Lorenz attractor)...")
    train_X, train_y = generate_training_data(
        num_samples=5000,
        seed=config.seed,
        noise_level=0.01
    )
    
    logger.info("Generating test data (Polynomial surfaces)...")
    test_X, test_y = generate_test_data(
        num_samples=1000,
        seed=config.seed + 1000,
        noise_level=0.01
    )
    
    # Convert to tensors and datasets
    train_dataset = TensorDataset(train_X, train_y)
    test_dataset = TensorDataset(test_X, test_y)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Create model
    model = create_model_from_config(config)
    num_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Model has {num_params:,} parameters")
    
    # Setup training
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Homeostasis scaler if enabled
    homeostasis_config = HomeostasisConfig(
        target_ei_ratio=4.0,
        decay_rate=0.01,
        log_interval=1
    ) if use_homeostasis else None
    
    scaler = HomeostaticScaler(model, homeostasis_config) if homeostasis_config else None
    
    # Training loop
    start_time = time.time()
    
    for epoch in range(train_epochs):
        model.train()
        epoch_loss = 0.0
        
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            # Apply homeostatic scaling if enabled
            if scaler:
                scaler.step(optimizer)
            
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / len(train_loader)
        
        # Evaluate every 2 epochs
        if (epoch + 1) % 2 == 0 or epoch == train_epochs - 1:
            model.eval()
            with torch.no_grad():
                test_outputs = model(test_X)
                test_mae = calculate_mae(test_outputs, test_y)
            
            logger.info(f"Epoch {epoch+1}/{train_epochs} - Loss: {avg_loss:.4f}, "
                       f"Test MAE: {test_mae:.4f}")
    
    training_time = time.time() - start_time
    
    # Final evaluation
    model.eval()
    with torch.no_grad():
        train_outputs = model(train_X)
        train_mae = calculate_mae(train_outputs, train_y)
        
        test_outputs = model(test_X)
        final_test_mae = calculate_mae(test_outputs, test_y)
    
    logger.info(f"Training complete for {config.variant_name}. "
               f"Train MAE: {train_mae:.4f}, Test MAE: {final_test_mae:.4f}, "
               f"Time: {training_time:.2f}s")
    
    return ScalingResult(
        variant_name=config.variant_name,
        scale_factor=config.scale_factor,
        num_parameters=num_params,
        train_mae=train_mae,
        test_mae=final_test_mae,
        training_time_seconds=training_time,
        config=config.to_dict()
    )

def run_scaling_study(
    output_path: str = "data/results/scaling_results.json",
    base_hidden_dim: int = 64,
    base_neurons: int = 128,
    train_epochs: int = 10,
    batch_size: int = 32,
    learning_rate: float = 1e-3
) -> List[ScalingResult]:
    """
    Run the full scaling study across 1x, 2x, and 4x variants.
    
    Args:
        output_path: Path to save results JSON
        base_hidden_dim: Base hidden dimension (1x)
        base_neurons: Base neurons per layer (1x)
        train_epochs: Number of training epochs per variant
        batch_size: Batch size for training
        learning_rate: Learning rate for optimizer
    
    Returns:
        List of ScalingResult objects for each variant
    """
    logger.info("Starting scaling study")
    
    # Generate configurations
    configs = create_scaling_configs(base_hidden_dim, base_neurons)
    
    results = []
    for config in configs:
        try:
            result = train_scaling_variant(
                config=config,
                train_epochs=train_epochs,
                batch_size=batch_size,
                learning_rate=learning_rate
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to train {config.variant_name}: {e}")
            raise
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_dict = [r.to_dict() for r in results]
    
    with open(output_path, 'w') as f:
        json.dump(results_dict, f, indent=2)
    
    logger.info(f"Scaling study complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for running the scaling study."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run scaling study for cortical column LLMs")
    parser.add_argument("--output", type=str, default="data/results/scaling_results.json",
                      help="Output path for results JSON")
    parser.add_argument("--epochs", type=int, default=10,
                      help="Number of training epochs per variant")
    parser.add_argument("--batch-size", type=int, default=32,
                      help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-3,
                      help="Learning rate")
    parser.add_argument("--base-hidden", type=int, default=64,
                      help="Base hidden dimension (1x)")
    parser.add_argument("--base-neurons", type=int, default=128,
                      help="Base neurons per layer (1x)")
    
    args = parser.parse_args()
    
    results = run_scaling_study(
        output_path=args.output,
        base_hidden_dim=args.base_hidden,
        base_neurons=args.base_neurons,
        train_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )
    
    # Print summary
    print("\n=== Scaling Study Summary ===")
    for r in results:
        print(f"{r.variant_name}: "
             f"params={r.num_parameters:,}, "
             f"train_mae={r.train_mae:.4f}, "
             f"test_mae={r.test_mae:.4f}, "
             f"time={r.training_time_seconds:.2f}s")

if __name__ == "__main__":
    main()
