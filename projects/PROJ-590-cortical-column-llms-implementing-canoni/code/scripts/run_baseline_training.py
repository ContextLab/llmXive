"""
T014 Implementation: Run baseline training on Lorenz (train) and Polynomials (test).

This script orchestrates the baseline training pipeline using the BaselineRunner
from src.experiments.baseline_runner. It generates synthetic data for training
(Lorenz attractor) and testing (polynomial surfaces), trains the baseline model,
and outputs metrics to data/results/baseline_metrics.json.

Usage:
    python scripts/run_baseline_training.py --train-task lorenz --test-task polynomial
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig, ExperimentResult
from src.data.benchmarks import generate_lorenz_attractor, generate_polynomial_surface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'data' / 'logs' / 'baseline_training.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run baseline training pipeline')
    parser.add_argument('--train-task', type=str, default='lorenz',
                      choices=['lorenz', 'fourier', 'polynomial'],
                      help='Task for training data generation')
    parser.add_argument('--test-task', type=str, default='polynomial',
                      choices=['lorenz', 'fourier', 'polynomial'],
                      help='Task for test data generation')
    parser.add_argument('--epochs', type=int, default=10,
                      help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32,
                      help='Batch size for training')
    parser.add_argument('--lr', type=float, default=0.001,
                      help='Learning rate')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default=None,
                      help='Output path for metrics JSON')
    
    args = parser.parse_args()
    
    logger.info(f"Starting baseline training with seed={args.seed}")
    logger.info(f"Training task: {args.train_task}, Test task: {args.test_task}")
    
    # Set random seed
    import torch
    import numpy as np
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    
    # Generate synthetic datasets
    logger.info("Generating training dataset...")
    if args.train_task == 'lorenz':
        train_data = generate_lorenz_attractor(n_samples=1000, n_steps=50, noise_std=0.01)
    elif args.train_task == 'fourier':
        # Placeholder for Fourier implementation if needed
        raise NotImplementedError("Fourier series generation not yet implemented")
    else:  # polynomial
        train_data = generate_polynomial_surface(n_samples=1000, degree=3, noise_std=0.01)
    
    logger.info("Generating test dataset...")
    if args.test_task == 'lorenz':
        test_data = generate_lorenz_attractor(n_samples=500, n_steps=50, noise_std=0.01)
    elif args.test_task == 'fourier':
        raise NotImplementedError("Fourier series generation not yet implemented")
    else:  # polynomial
        test_data = generate_polynomial_surface(n_samples=500, degree=3, noise_std=0.01)
    
    logger.info(f"Training data shape: {train_data['X'].shape}")
    logger.info(f"Test data shape: {test_data['X'].shape}")
    
    # Configure experiment
    config = ExperimentConfig(
        model_type='baseline_transformer',
        hidden_dim=64,
        n_layers=2,
        n_heads=4,
        max_seq_len=50,
        learning_rate=args.lr,
        batch_size=args.batch_size,
        epochs=args.epochs,
        seed=args.seed,
        train_data=train_data,
        test_data=test_data
    )
    
    # Run training
    logger.info("Initializing BaselineRunner...")
    runner = BaselineRunner(config)
    
    logger.info("Starting training loop...")
    start_time = time.time()
    result = runner.train()
    elapsed_time = time.time() - start_time
    
    logger.info(f"Training completed in {elapsed_time:.2f} seconds")
    
    # Calculate degradation
    train_mae = result.train_metrics['mae']
    test_mae = result.test_metrics['mae']
    degradation_pct = ((test_mae - train_mae) / train_mae) * 100 if train_mae > 0 else 0.0
    
    logger.info(f"Train MAE: {train_mae:.6f}")
    logger.info(f"Test MAE: {test_mae:.6f}")
    logger.info(f"Degradation: {degradation_pct:.2f}%")
    
    # Prepare output metrics
    metrics = {
        'train_mae': float(train_mae),
        'test_mae': float(test_mae),
        'degradation_pct': float(degradation_pct),
        'train_time_seconds': float(elapsed_time),
        'epochs_completed': result.epochs_completed,
        'final_loss': float(result.final_loss),
        'config': {
            'model_type': config.model_type,
            'hidden_dim': config.hidden_dim,
            'n_layers': config.n_layers,
            'n_heads': config.n_heads,
            'learning_rate': config.learning_rate,
            'batch_size': config.batch_size,
            'epochs': config.epochs,
            'seed': config.seed,
            'train_task': args.train_task,
            'test_task': args.test_task
        }
    }
    
    # Determine output path
    output_path = Path(args.output) if args.output else PROJECT_ROOT / 'data' / 'results' / 'baseline_metrics.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write metrics to JSON
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to: {output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("BASELINE TRAINING SUMMARY")
    print("="*60)
    print(f"Train MAE: {train_mae:.6f}")
    print(f"Test MAE: {test_mae:.6f}")
    print(f"Degradation: {degradation_pct:.2f}%")
    print(f"Training Time: {elapsed_time:.2f} seconds")
    print(f"Output: {output_path}")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())