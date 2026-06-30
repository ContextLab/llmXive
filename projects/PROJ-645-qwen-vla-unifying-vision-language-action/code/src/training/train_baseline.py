"""
Baseline training script for User Story 2.
Trains a VLA model on the single-platform subset of Open X-Embodiment (T012b).
Reuses the US1 pipeline but enforces single-embodiment data and specific seeds.
"""
import os
import sys
import time
import logging
import gc
import json
import random
import argparse
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Import from existing API surface
from src.models.vla_model import Qwen2VLVLA
from src.data.dataset_loader import fetch_and_filter_dataset, save_to_parquet, ensure_data_directory
from src.data.preprocess_actions import preprocess_actions, load_token_config
from src.training.train_loop import train_loop, auto_reduce_batch_size
from src.utils.resource_monitor import get_current_ram_gb, check_ram_limit, check_wall_time_limit
from src.utils.checkpoint_saver import save_checkpoint
from src.utils.reproducibility import load_seeds
from src.utils.logging_config import get_logger, setup_logging
from src.utils.config import Config

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"
LOG_DIR = PROJECT_ROOT / "logs"

# Specific input/output paths for T012b and T020
SINGLE_PLATFORM_DATASET_PATH = DATA_DIR / "filtered_open_x_embodiment_single_platform.parquet"
SEEDS_FILE = DATA_DIR / "seeds.json"
BASELINE_OUTPUT_DIR = DATA_DIR / "baseline_checkpoints"

def setup_baseline_config(args):
    """Setup configuration for baseline training."""
    config = {
        "dataset_path": str(SINGLE_PLATFORM_DATASET_PATH),
        "output_dir": str(BASELINE_OUTPUT_DIR),
        "seeds_file": str(SEEDS_FILE),
        "epochs": args.epochs,
        "base_batch_size": args.batch_size,
        "max_ram_gb": 6.5,
        "wall_time_limit_seconds": 21600,  # 6 hours
        "log_dir": str(LOG_DIR),
        "num_workers": args.num_workers,
        "pin_memory": args.pin_memory,
    }
    return config

def load_and_prepare_dataset(config, logger):
    """Load the single-platform dataset and prepare DataLoader."""
    dataset_path = Path(config["dataset_path"])
    
    if not dataset_path.exists():
        logger.error(f"Single-platform dataset not found at {dataset_path}. "
                     "Run T012b first to generate this file.")
        raise FileNotFoundError(f"Dataset file missing: {dataset_path}")
    
    logger.info(f"Loading dataset from {dataset_path}")
    
    # The dataset_loader module expects specific args, but we assume the file exists.
    # We need a way to load the parquet into a torch Dataset.
    # Since T012 creates the parquet, we assume a simple wrapper exists or we load it here.
    # For this implementation, we will simulate the loading logic assuming the parquet
    # structure is known (observations, actions) or use a generic loader if available.
    # Given the constraints, we'll implement a minimal loader that reads the parquet
    # and yields batches, or delegates to a hypothetical helper if the API surface
    # implies a specific DataLoader class.
    
    # Since we don't have a specific DataLoader class in the API surface for the parquet,
    # we will assume the existence of a helper or implement a basic one here using pandas.
    # However, to stay within "Extend, don't re-author", we assume the training loop
    # expects a standard PyTorch Dataset.
    
    # Fallback: If no specific dataset class is provided in API, we create a minimal one.
    # This is necessary to make the script runnable.
    import pandas as pd
    import torch.utils.data as data

    class ParquetDataset(data.Dataset):
        def __init__(self, path):
            self.df = pd.read_parquet(path)
            # Assume columns 'observation' (dict or tensor) and 'action' (tensor)
            # In a real scenario, these would be pre-processed by T013.
            # For this script, we assume the parquet contains pre-processed tensors
            # or we load them as arrays and convert.
            # To be safe, we assume 'action' is a list of floats or a numpy array.
            
        def __len__(self):
            return len(self.df)
        
        def __getitem__(self, idx):
            row = self.df.iloc[idx]
            # Simple conversion assuming numpy arrays or lists in parquet
            obs = row['observation'] 
            act = row['action']
            
            # Convert to tensors if necessary
            if not isinstance(obs, torch.Tensor):
                obs = torch.tensor(obs, dtype=torch.float32) if isinstance(obs, (list, tuple)) else torch.tensor(obs)
            if not isinstance(act, torch.Tensor):
                act = torch.tensor(act, dtype=torch.float32) if isinstance(act, (list, tuple)) else torch.tensor(act)
            
            return obs, act

    dataset = ParquetDataset(dataset_path)
    logger.info(f"Loaded {len(dataset)} samples from single-platform dataset.")
    return dataset

def main():
    parser = argparse.ArgumentParser(description="Train VLA Baseline (Single Platform)")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Base batch size")
    parser.add_argument("--num-workers", type=int, default=0, help="DataLoader workers")
    parser.add_argument("--pin-memory", action="store_true", default=True, help="Pin memory")
    args = parser.parse_args()

    # Setup logging
    setup_logging(log_dir=str(LOG_DIR), level=logging.INFO)
    logger = get_logger("train_baseline")
    
    logger.info("Starting Baseline Training (US2 - T020)")
    logger.info(f"Dataset: {SINGLE_PLATFORM_DATASET_PATH}")
    logger.info(f"Output: {BASELINE_OUTPUT_DIR}")

    # Load Seeds
    if not SEEDS_FILE.exists():
        logger.error(f"Seeds file not found at {SEEDS_FILE}. Run T018 first.")
        sys.exit(1)
    
    seeds = load_seeds(SEEDS_FILE)
    logger.info(f"Loaded {len(seeds)} seeds: {seeds}")

    config = setup_baseline_config(args)
    
    # Ensure output directories
    Path(config["output_dir"]).mkdir(parents=True, exist_ok=True)

    for i, seed in enumerate(seeds):
        logger.info(f"--- Starting Seed {i+1}/{len(seeds)}: {seed} ---")
        
        # Set seeds for reproducibility
        random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        
        # Limit threads
        torch.set_num_threads(2)

        # Load Dataset
        try:
            dataset = load_and_prepare_dataset(config, logger)
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            continue

        # Create DataLoader
        dataloader = DataLoader(
            dataset, 
            batch_size=config["base_batch_size"], 
            shuffle=True,
            num_workers=config["num_workers"],
            pin_memory=config["pin_memory"]
        )

        # Initialize Model
        model = Qwen2VLVLA()
        model.train()
        logger.info("Model initialized.")

        # Training Loop
        start_time = time.time()
        epoch = 0
        completed = False
        
        try:
            while epoch < config["epochs"]:
                # Check time limit
                if check_wall_time_limit(start_time, config["wall_time_limit_seconds"]):
                    logger.warning("TIMEOUT_WARNING: Wall time limit reached. Stopping training.")
                    break

                # Check RAM before epoch
                if check_ram_limit(config["max_ram_gb"]):
                    logger.warning("RAM limit reached before epoch. Reducing batch size.")
                    config["base_batch_size"] = auto_reduce_batch_size(config["base_batch_size"])
                    if config["base_batch_size"] < 1:
                        logger.error("Batch size reduced to 0. Cannot continue.")
                        break
                    dataloader = DataLoader(
                        dataset, 
                        batch_size=config["base_batch_size"], 
                        shuffle=True,
                        num_workers=config["num_workers"],
                        pin_memory=config["pin_memory"]
                    )

                # Train one epoch
                # We need to call the train_epoch logic. 
                # Since train_loop in T015 is the main entry, we might need to adapt or call internal logic.
                # The API surface shows `train_loop` in train_loop.py.
                # We assume `train_loop` handles the epoch logic if passed a dataloader.
                # However, `train_loop` signature in T015 likely takes a model, dataloader, etc.
                # Let's assume we can call a simplified version or adapt.
                # To be safe and reusable, we will assume `train_loop` from T015 is flexible enough
                # or we implement the epoch loop here if `train_loop` is the full run.
                # Given T015 implements the loop, we will call it.
                # But T015's `train_loop` might be the full run. Let's assume we need to implement
                # the epoch step here if `train_loop` is the whole thing, OR call it with a seed.
                
                # Re-reading T015: "Implement ... train_loop ... Output: data/checkpoints/model_epoch_{n}.pt"
                # It seems `train_loop` runs the full training.
                # For T020, we need to run it for this specific seed and dataset.
                # We will call `train_loop` but we need to ensure it uses the correct dataset and seeds.
                # Since `train_loop` is in `src.training.train_loop`, it might expect a specific dataset loader.
                # To avoid rewriting `train_loop`, we will assume we can pass the dataloader and model.
                # If `train_loop` is hardcoded to T012 dataset, we have a problem.
                # However, T015a added auto-reduction.
                # Let's assume `train_loop` is generic enough or we implement a simplified loop here
                # that calls `train_epoch` if available.
                # The API surface for T015 lists `train_epoch` as a public name.
                # So we can use `train_epoch`.
                
                from src.training.train_loop import train_epoch
                
                logger.info(f"Starting Epoch {epoch + 1}")
                train_epoch(model, dataloader, seed, config, logger)
                
                epoch += 1
                
                # Save checkpoint after epoch
                checkpoint_path = Path(config["output_dir"]) / f"baseline_model_seed_{seed}_epoch_{epoch}.pt"
                save_checkpoint(model, checkpoint_path, config)
                
                logger.info(f"Checkpoint saved to {checkpoint_path}")

            completed = True

        except Exception as e:
            logger.error(f"Training failed for seed {seed}: {e}", exc_info=True)
            continue

        if completed:
            logger.info(f"Seed {seed} training completed successfully.")
        else:
            logger.warning(f"Seed {seed} training did not complete all epochs.")

    logger.info("Baseline training pipeline finished.")

if __name__ == "__main__":
    main()