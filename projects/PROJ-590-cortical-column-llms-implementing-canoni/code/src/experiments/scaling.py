import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import torch
import numpy as np
import pandas as pd

from src.models.hybrid_network import create_hybrid_network, count_parameters
from src.models.microcircuit import MicrocircuitColumnConfig
from src.training.trainer import run_training, TrainingConfig
from src.data.benchmarks import generate_training_data
from src.training.homeostasis import log_gradient_norms

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScalingConfig:
    """Configuration for a single scaling variant."""
    multiplier: int  # 1x, 2x, 4x
    num_columns: int
    hidden_dim: int = 256
    num_heads: int = 4
    num_layers: int = 4
    dropout: float = 0.1
    lr: float = 1e-4
    epochs: int = 10
    batch_size: int = 32
    seed: int = 42

@dataclass
class ScalingResult:
    """Result from training a single scaling variant."""
    multiplier: int
    num_columns: int
    parameter_count: int
    validation_mae: float
    training_time_sec: float
    config: Dict[str, Any] = field(default_factory=dict)

def create_scaling_configs(base_columns: int = 4, multipliers: List[int] = [1, 2, 4]) -> List[ScalingConfig]:
    """Generate configurations for the scaling study."""
    configs = []
    for m in multipliers:
        configs.append(ScalingConfig(
            multiplier=m,
            num_columns=base_columns * m,
            hidden_dim=256,
            num_heads=4,
            num_layers=4,
            dropout=0.1,
            lr=1e-4,
            epochs=10,
            batch_size=32,
            seed=42
        ))
    return configs

def train_scaling_variant(config: ScalingConfig, train_data: np.ndarray, test_data: np.ndarray) -> ScalingResult:
    """Train a single scaling variant and record metrics."""
    logger.info(f"Training variant: {config.multiplier}x ({config.num_columns} columns)")
    
    # Set seed for reproducibility
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    # Create model
    model = create_hybrid_network(
        num_columns=config.num_columns,
        hidden_dim=config.hidden_dim,
        num_heads=config.num_heads,
        num_layers=config.num_layers,
        dropout=config.dropout
    )
    
    param_count = count_parameters(model)
    logger.info(f"Parameter count: {param_count}")

    # Prepare training config
    train_config = TrainingConfig(
        lr=config.lr,
        epochs=config.epochs,
        batch_size=config.batch_size,
        weight_decay=1e-4,
        gradient_clip=1.0,
        log_dir="data/logs",
        checkpoint_dir="data/checkpoints"
    )

    # Ensure directories exist
    os.makedirs(train_config.log_dir, exist_ok=True)
    os.makedirs(train_config.checkpoint_dir, exist_ok=True)

    # Start timing
    start_time = time.time()
    
    # Run training
    metrics = run_training(
        model=model,
        train_data=train_data,
        test_data=test_data,
        config=train_config
    )
    
    end_time = time.time()
    training_time = end_time - start_time

    # Log gradient norms for SC-002
    log_gradient_norms(model, step=config.epochs)

    # Extract final validation MAE
    final_mae = metrics.get('final_test_mae', float('nan'))
    
    logger.info(f"Variant {config.multiplier}x completed. MAE: {final_mae:.4f}, Time: {training_time:.2f}s")

    return ScalingResult(
        multiplier=config.multiplier,
        num_columns=config.num_columns,
        parameter_count=param_count,
        validation_mae=final_mae,
        training_time_sec=training_time,
        config=asdict(config)
    )

def save_scaling_results(results: List[ScalingResult], output_path: str) -> None:
    """Save scaling results to CSV."""
    if not results:
        raise ValueError("No results to save")

    data = []
    for r in results:
        data.append({
            'columns': r.num_columns,
            'params': r.parameter_count,
            'mae': r.validation_mae,
            'time_sec': r.training_time_sec
        })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved scaling results to {output_path}")

def verify_scaling_output(output_path: str) -> bool:
    """Verify that the scaling output file exists and is valid."""
    if not os.path.exists(output_path):
        logger.error(f"Output file not found: {output_path}")
        return False

    try:
        df = pd.read_csv(output_path)
        required_cols = ['columns', 'params', 'mae', 'time_sec']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns in {output_path}")
            return False
        
        if len(df) == 0:
            logger.error(f"Empty data in {output_path}")
            return False

        # Verify we have the expected number of rows (1x, 2x, 4x)
        if len(df) != 3:
            logger.warning(f"Expected 3 rows, got {len(df)} in {output_path}")

        logger.info(f"Verification passed for {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to verify {output_path}: {e}")
        return False

def run_scaling_study(
    base_columns: int = 4,
    multipliers: List[int] = [1, 2, 4],
    output_path: str = "data/results/scaling_law.csv",
    train_size: int = 5000,
    test_size: int = 1000
) -> List[ScalingResult]:
    """Run the full scaling study."""
    logger.info("Starting scaling study")
    
    # Generate synthetic training and test data
    # Using Lorenz attractor for training (as per T008a)
    train_data = generate_training_data(n_samples=train_size, seed=42)
    
    # Using polynomial surfaces for test (as per T008c)
    test_data = generate_training_data(n_samples=test_size, seed=123)  # Distinct seed for independence

    # Create configs
    configs = create_scaling_configs(base_columns, multipliers)
    
    results = []
    for config in configs:
        result = train_scaling_variant(config, train_data, test_data)
        results.append(result)

    # Save results
    save_scaling_results(results, output_path)

    # Verify output
    if not verify_scaling_output(output_path):
        raise RuntimeError(f"Scaling output verification failed for {output_path}")

    logger.info("Scaling study completed successfully")
    return results

def main():
    """Entry point for scaling study."""
    logger.info("Running scaling study via main()")
    results = run_scaling_study(
        base_columns=4,
        multipliers=[1, 2, 4],
        output_path="data/results/scaling_law.csv",
        train_size=5000,
        test_size=1000
    )
    
    print(f"\nScaling Study Results:")
    for r in results:
        print(f"  {r.multiplier}x ({r.num_columns} cols): {r.parameter_count:,} params, MAE={r.validation_mae:.4f}, Time={r.training_time_sec:.1f}s")

if __name__ == "__main__":
    main()
