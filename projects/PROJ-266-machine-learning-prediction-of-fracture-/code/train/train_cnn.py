import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
import numpy as np

# Import project modules using the provided API surface
from code.models.cnn import CNN
from code.utils.seeds import get_seeds, set_global_seed
from code.utils.logger import get_logger
from code.utils.config import get_config_dict, get_split_seed, get_training_seed

# Ensure paths are set correctly relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class ImageDataset(Dataset):
    """Dataset for loading processed images and their K_IC values."""
    def __init__(self, split_dir: Path, metadata_path: Path):
        self.split_dir = split_dir
        self.metadata_path = metadata_path
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])

        # Load metadata
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
        import pandas as pd
        self.df = pd.read_csv(metadata_path)
        
        # Filter for the specific split (train/val/test) based on directory name
        split_name = split_dir.name
        self.df = self.df[self.df['split'] == split_name].reset_index(drop=True)
        
        if len(self.df) == 0:
            raise ValueError(f"No data found for split: {split_name}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        image_path = self.split_dir / row['image_path']
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image using PIL
        from PIL import Image
        img = Image.open(image_path).convert('L')
        img_tensor = self.transform(img)
        
        # Get target (K_IC)
        target = float(row['k_ic'])
        
        return img_tensor, target

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: optim.Optimizer, criterion: nn.Module, device: torch.device):
    model.train()
    running_loss = 0.0
    total_mae = 0.0
    num_samples = 0

    for batch_idx, (images, targets) in enumerate(dataloader):
        images, targets = images.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        total_mae += torch.abs(outputs - targets).sum().item()
        num_samples += targets.size(0)

    avg_loss = running_loss / len(dataloader)
    avg_mae = total_mae / num_samples
    return avg_loss, avg_mae

def validate(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, device: torch.device):
    model.eval()
    running_loss = 0.0
    total_mae = 0.0
    num_samples = 0

    with torch.no_grad():
        for images, targets in dataloader:
            images, targets = images.to(device), targets.to(device)
            outputs = model(images)
            loss = criterion(outputs, targets)

            running_loss += loss.item()
            total_mae += torch.abs(outputs - targets).sum().item()
            num_samples += targets.size(0)

    avg_loss = running_loss / len(dataloader)
    avg_mae = total_mae / num_samples
    return avg_loss, avg_mae

def train_model(seed: int, config: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Train the CNN model with a specific seed."""
    set_global_seed(seed)
    logger.info(f"Starting training with seed: {seed}")

    # Setup device (CPU only as per spec)
    device = torch.device('cpu')
    torch.set_num_threads(4)

    # Paths
    processed_dir = PROJECT_ROOT / "data" / "processed"
    train_dir = processed_dir / "train"
    val_dir = processed_dir / "val"
    metadata_path = processed_dir / "split_metadata.csv"

    # Hyperparameters
    batch_size = config.get('batch_size', 32)
    epochs = config.get('epochs', 50)
    lr = config.get('lr', 1e-3)
    weight_decay = config.get('weight_decay', 1e-4)

    # Create datasets and loaders
    train_dataset = ImageDataset(train_dir, metadata_path)
    val_dataset = ImageDataset(val_dir, metadata_path)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # Initialize model
    model = CNN(input_size=128, num_classes=1).to(device)
    
    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True)

    best_val_loss = float('inf')
    best_model_state = None
    patience_counter = 0
    early_stop_patience = 10

    logger.info(f"Training for {epochs} epochs...")

    for epoch in range(1, epochs + 1):
        train_loss, train_mae = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_mae = validate(model, val_loader, criterion, device)

        scheduler.step(val_loss)

        logger.info(f"Epoch [{epoch}/{epochs}] - Train Loss: {train_loss:.4f}, Train MAE: {train_mae:.4f}, Val Loss: {val_loss:.4f}, Val MAE: {val_mae:.4f}")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            patience_counter = 0
        else:
            patience_counter += 1

        # Early stopping
        if patience_counter >= early_stop_patience:
            logger.info(f"Early stopping triggered at epoch {epoch}")
            break

    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    # Save model
    model_dir = PROJECT_ROOT / "models" / "cnn"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / f"model_seed_{seed}.pt"
    torch.save({
        'model_state_dict': model.state_dict(),
        'seed': seed,
        'best_val_loss': best_val_loss,
        'config': config
    }, model_path)
    logger.info(f"Model saved to {model_path}")

    return {
        'seed': seed,
        'best_val_loss': best_val_loss,
        'final_train_loss': train_loss,
        'final_train_mae': train_mae,
        'final_val_loss': val_loss,
        'final_val_mae': val_mae,
        'model_path': str(model_path)
    }

def main():
    parser = argparse.ArgumentParser(description="Train CNN model with multiple seeds")
    parser.add_argument('--seeds', type=int, default=5, help="Number of independent seeds to run")
    parser.add_argument('--config', type=str, default=None, help="Path to config file (optional)")
    args = parser.parse_args()

    # Setup logging
    logger = get_logger("TRAIN")
    logger.info(f"Starting CNN training for {args.seeds} seeds")

    # Load config
    config = get_config_dict()
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            custom_config = json.load(f)
            config.update(custom_config)

    # Ensure output directory exists
    model_dir = PROJECT_ROOT / "models" / "cnn"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Get seeds
    seeds = get_seeds(args.seeds)
    logger.info(f"Using seeds: {seeds}")

    # Train for each seed
    results = []
    for seed in seeds:
        try:
            result = train_model(seed, config, logger)
            results.append(result)
        except Exception as e:
            logger.error(f"Training failed for seed {seed}: {e}")
            results.append({'seed': seed, 'error': str(e)})

    # Save results
    results_path = model_dir / "training_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Training results saved to {results_path}")

    logger.info("All training runs completed.")

if __name__ == "__main__":
    main()