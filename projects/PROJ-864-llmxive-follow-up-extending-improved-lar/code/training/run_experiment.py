"""
Experiment orchestration for running multiple training seeds and architectures.
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch
import json

from utils.logging import get_logger, info, error, warning
from utils.config import get_config, get_num_epochs, get_device
from training.helpers import ensure_training_dirs
from training.train_loop import train_loop, prepare_dataloaders
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model

logger = get_logger(__name__)

def run_single_model_training(
    model_type: str,
    seed_id: int,
    data_dir: Path,
    num_epochs: int,
    device: torch.device
) -> Dict[str, Any]:
    """
    Run training for a single model and seed.
    
    Args:
        model_type: 'autoregressive' or 'diffusion'
        seed_id: Seed identifier
        data_dir: Path to data directory
        num_epochs: Number of epochs to train
        device: Torch device
        
    Returns:
        Training results dictionary
    """
    info(f"Starting training for {model_type} model with seed {seed_id}")
    
    # Set random seeds for reproducibility
    torch.manual_seed(seed_id)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(seed_id)
    
    # Create model
    if model_type == 'autoregressive':
        model = create_autoregressive_model()
    elif model_type == 'diffusion':
        model = create_diffusion_model()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model = model.to(device)
    
    # Prepare data
    train_loader, val_loader = prepare_dataloaders(data_dir)
    
    # Run training
    results = train_loop(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=num_epochs,
        seed_id=seed_id,
        device=device,
    )
    
    results["model_type"] = model_type
    return results

def save_logs_to_csv(all_results: List[Dict[str, Any]], output_path: Path):
    """
    Save all training results to a single CSV file.
    
    Args:
        all_results: List of training result dictionaries
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'timestamp', 'seed_id', 'model_type', 'epoch', 'train_loss', 
        'val_loss', 'gap', 'status', 'epochs_completed'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in all_results:
            for history in result.get('history', []):
                row = {
                    'timestamp': datetime.now().isoformat(),
                    'seed_id': result['seed_id'],
                    'model_type': result['model_type'],
                    'epoch': history['epoch'],
                    'train_loss': history['train_loss'],
                    'val_loss': history['val_loss'],
                    'gap': history['gap'],
                    'status': result['status'],
                    'epochs_completed': result['epochs_completed']
                }
                writer.writerow(row)
    
    info(f"Saved training logs to {output_path}")

def main():
    """
    Main entry point for running the full experiment.
    """
    parser = argparse.ArgumentParser(description="Run training experiment")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4, 5],
                        help="List of seed IDs to run")
    parser.add_argument("--epochs", type=int, default=100,
                        help="Number of epochs per model")
    parser.add_argument("--architectures", type=str, nargs="+", 
                        default=["autoregressive", "diffusion"],
                        help="Model architectures to train")
    parser.add_argument("--data-dir", type=str, default="data/processed",
                        help="Path to processed data directory")
    args = parser.parse_args()
    
    info(f"Running experiment with seeds: {args.seeds}")
    info(f"Architectures: {args.architectures}")
    info(f"Epochs: {args.epochs}")
    
    device = get_device()
    data_dir = Path(args.data_dir)
    num_epochs = args.epochs
    
    if not data_dir.exists():
        error(f"Data directory not found: {data_dir}")
        sys.exit(1)
    
    all_results = []
    
    try:
        for model_type in args.architectures:
            for seed_id in args.seeds:
                result = run_single_model_training(
                    model_type=model_type,
                    seed_id=seed_id,
                    data_dir=data_dir,
                    num_epochs=num_epochs,
                    device=device
                )
                all_results.append(result)
                
                # Check if we should truncate (simplified timeout check)
                if len(all_results) >= 10:  # Max 10 total runs (5 seeds * 2 archs)
                    break
            if len(all_results) >= 10:
                break
    
    except Exception as e:
        error(f"Experiment failed: {str(e)}")
        # Mark all as truncated
        for result in all_results:
            result["status"] = "TRUNCATED"
        raise
    
    finally:
        # Save aggregated logs
        dirs = ensure_training_dirs()
        output_path = dirs["logs"] / "training_logs.csv"
        save_logs_to_csv(all_results, output_path)
        
        # Save individual results as JSON
        results_path = dirs["logs"] / "experiment_results.json"
        with open(results_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        info(f"Experiment completed. Results saved to {output_path}")

if __name__ == "__main__":
    main()
