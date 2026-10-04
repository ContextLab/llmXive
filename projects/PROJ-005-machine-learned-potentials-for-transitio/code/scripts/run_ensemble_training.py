#!/usr/bin/env python3
"""
T023b Implementation: Runner script for a single ensemble member.
This script is invoked by train_ensemble.sh with a specific seed.
It initializes the seed, loads data, trains the SchNet model, and saves the checkpoint.
"""
import argparse
import logging
import os
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging import setup_logger, get_logger
from src.utils.config import load_config
from src.models.ensemble import GraphDataset, train_model, set_seed
from src.data.validate_splits import load_splits_file

def main():
    parser = argparse.ArgumentParser(description="Train a single SchNet model for the ensemble.")
    parser.add_argument("--seed", type=int, required=True, help="Random seed for this training run.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file.")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logger(name=f"train_seed_{args.seed}", level=logging.INFO)
    logger.info(f"Starting training for seed {args.seed}")

    # Set random seeds for reproducibility
    set_seed(args.seed)
    logger.info(f"Random seeds set to {args.seed}")

    # Load configuration
    config_path = PROJECT_ROOT / args.config
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        config = {}
    else:
        config = load_config(config_path)
    
    # Hyperparameters (defaults if not in config)
    num_epochs = config.get("training", {}).get("max_epochs", 30)
    batch_size = config.get("training", {}).get("batch_size", 32)
    learning_rate = config.get("training", {}).get("learning_rate", 1e-4)
    patience = config.get("training", {}).get("early_stopping_patience", 5)
    cutoff = config.get("data", {}).get("cutoff", 3.5)
    
    logger.info(f"Training config: epochs={num_epochs}, lr={learning_rate}, patience={patience}")

    # Paths
    data_path = PROJECT_ROOT / "data" / "processed" / "graphs.parquet"
    splits_path = PROJECT_ROOT / "data" / "processed" / "splits.json"
    model_dir = PROJECT_ROOT / "data" / "processed" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"seed_{args.seed}.pt"

    # Load splits
    if not splits_path.exists():
        logger.error(f"Splits file not found at {splits_path}. Run T011 first.")
        sys.exit(1)
    
    splits = load_splits_file(splits_path)
    # We assume the splits dict has 'train', 'val', 'test' keys with lists of sample IDs or indices
    # The GraphDataset class in ensemble.py is expected to handle loading based on these splits.
    
    # Initialize Dataset
    # Note: The GraphDataset class in ensemble.py is assumed to take the path to graphs.parquet
    # and the split indices to create train/val loaders.
    try:
        train_dataset = GraphDataset(
            data_path=str(data_path),
            split_indices=splits['train'],
            transform=None # Add transforms if needed
        )
        val_dataset = GraphDataset(
            data_path=str(data_path),
            split_indices=splits['val'],
            transform=None
        )
    except Exception as e:
        logger.error(f"Failed to initialize datasets: {e}")
        sys.exit(1)

    logger.info(f"Dataset loaded: Train={len(train_dataset)}, Val={len(val_dataset)}")

    # Train the model
    # train_model is expected to return the trained model and history
    try:
        model, history = train_model(
            train_dataset=train_dataset,
            val_dataset=val_dataset,
            num_epochs=num_epochs,
            batch_size=batch_size,
            learning_rate=learning_rate,
            patience=patience,
            seed=args.seed,
            logger=logger
        )
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

    # Save the model
    try:
        torch.save({
            'seed': args.seed,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': history.get('optimizer_state'),
            'history': history.get('history'),
            'config': {
                'cutoff': cutoff,
                'num_epochs': num_epochs,
                'batch_size': batch_size,
                'learning_rate': learning_rate
            }
        }, str(model_path))
        logger.info(f"Model saved to {model_path}")
    except Exception as e:
        logger.error(f"Failed to save model: {e}")
        sys.exit(1)

    logger.info(f"Training for seed {args.seed} completed successfully.")

if __name__ == "__main__":
    # Import torch here to avoid circular imports if any, though unlikely
    import torch
    main()
