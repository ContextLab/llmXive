"""
Train.py - Main training loop for the Molecular Excitation Wavelength prediction model.

This script implements the training pipeline for the GNN model, including:
- Data loading and preprocessing
- Model training with fixed seeds
- CPU-only execution
- Time budget enforcement (4-hour cap)
- Model versioning via artifact hashing

Dependencies:
- torch
- rdkit
- pandas
- pydantic
"""

import os
import sys
import json
import logging
import random
import time
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

# Project imports
from model import MPNN, build_gnn_model, prepare_gnn_data
from utils import get_device, parse_smiles, setup_logging, get_logger

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-379-predicting-molecular-excitation-waveleng.yaml"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Time budget (seconds)
TRAINING_TIME_LIMIT = 4 * 60 * 60  # 4 hours

# Setup logging
setup_logging()
logger = get_logger(__name__)

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(model_path: Path, model_hash: str) -> None:
    """Update the project state file with model artifact hash."""
    state_data = {
        "artifact_hashes": {},
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Load existing state if it exists
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                existing_state = yaml.safe_load(f) or {}
                state_data["artifact_hashes"] = existing_state.get("artifact_hashes", {})
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}")
    
    # Update with new model hash
    state_data["artifact_hashes"]["model.pt"] = model_hash
    state_data["artifact_hashes"]["model.pt.path"] = str(model_path)
    
    # Ensure state directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Write updated state
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger.info(f"Updated state file with model hash: {model_hash}")

def load_data_splits() -> Dict[str, pd.DataFrame]:
    """Load train, validation, and test splits from CSV."""
    splits = {}
    split_files = {
        "train": "train_val_test.csv",
        "val": "train_val_test.csv",
        "test": "train_val_test.csv"
    }
    
    for split_name, filename in split_files.items():
        file_path = PROCESSED_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Split file not found: {file_path}")
        
        df = pd.read_csv(file_path)
        if split_name == "train":
            splits[split_name] = df[df['split'] == 'train']
        elif split_name == "val":
            splits[split_name] = df[df['split'] == 'val']
        elif split_name == "test":
            splits[split_name] = df[df['split'] == 'test']
        
        logger.info(f"Loaded {split_name} split: {len(splits[split_name])} samples")
    
    return splits

def preprocess_df(df: pd.DataFrame) -> Dict[str, Any]:
    """Preprocess dataframe for GNN training."""
    data_list = []
    
    for idx, row in df.iterrows():
        smiles = row['smi']
        lambda_max = row['lambda_max']
        
        mol = parse_smiles(smiles)
        if mol is None:
            logger.warning(f"Invalid SMILES at index {idx}: {smiles}")
            continue
        
        # Generate ECFP fingerprint
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
        fp_array = list(fp)
        
        data_list.append({
            "smiles": smiles,
            "lambda_max": lambda_max,
            "fp": fp_array,
            "mol": mol
        })
    
    logger.info(f"Preprocessed {len(data_list)} molecules")
    return data_list

class MolecularDataset(Dataset):
    """PyTorch Dataset for molecular data."""
    
    def __init__(self, data_list: list):
        self.data_list = data_list
    
    def __len__(self):
        return len(self.data_list)
    
    def __getitem__(self, idx):
        item = self.data_list[idx]
        fp_tensor = torch.tensor(item['fp'], dtype=torch.float32)
        label = torch.tensor(item['lambda_max'], dtype=torch.float32)
        return fp_tensor, label

def collate_fn(batch):
    """Collate function for DataLoader."""
    fps, labels = zip(*batch)
    return torch.stack(fps), torch.stack(labels)

def train_epoch(model: nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    """Train model for one epoch."""
    model.train()
    total_loss = 0.0
    criterion = nn.MSELoss()
    
    for fps, labels in dataloader:
        fps = fps.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(fps)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def validate_epoch(model: nn.Module, dataloader: DataLoader, device: torch.device) -> float:
    """Validate model on one epoch."""
    model.eval()
    total_loss = 0.0
    criterion = nn.MSELoss()
    
    with torch.no_grad():
        for fps, labels in dataloader:
            fps = fps.to(device)
            labels = labels.to(device)
            
            outputs = model(fps)
            loss = criterion(outputs, labels)
            total_loss += loss.item()
    
    return total_loss / len(dataloader)

def train_model(model: nn.Module, train_data: list, val_data: list, epochs: int = 100, device: torch.device = None) -> nn.Module:
    """Train the model with early stopping and validation."""
    if device is None:
        device = get_device()
    
    train_dataset = MolecularDataset(train_data)
    val_dataset = MolecularDataset(val_data)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, collate_fn=collate_fn)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=10)
    
    best_val_loss = float('inf')
    patience_counter = 0
    max_patience = 20
    
    logger.info(f"Starting training on {device} for {epochs} epochs")
    start_time = time.time()
    
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss = validate_epoch(model, val_loader, device)
        
        scheduler.step(val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            # Save best model state
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
            if patience_counter >= max_patience:
                logger.info(f"Early stopping at epoch {epoch+1}")
                break
        
        # Check time budget
        elapsed = time.time() - start_time
        if elapsed > TRAINING_TIME_LIMIT:
            raise RuntimeError(f"Training exceeded {TRAINING_TIME_LIMIT}s limit per FR-003.")
    
    # Restore best model state
    model.load_state_dict(best_model_state)
    logger.info(f"Training completed in {time.time() - start_time:.2f}s")
    return model

def save_seeds(seed: int, output_path: Path) -> None:
    """Save random seeds to file for reproducibility."""
    with open(output_path, 'w') as f:
        json.dump({"seed": seed, "timestamp": datetime.utcnow().isoformat()}, f)
    logger.info(f"Saved seeds to {output_path}")

def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train molecular excitation wavelength model")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="model.pt", help="Output model path")
    args = parser.parse_args()
    
    # Set seed
    set_seed(args.seed)
    
    # Load data
    logger.info("Loading data splits...")
    try:
        splits = load_data_splits()
    except FileNotFoundError as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    train_data = preprocess_df(splits['train'])
    val_data = preprocess_df(splits['val'])
    
    if not train_data or not val_data:
        logger.error("No valid data found for training/validation")
        sys.exit(1)
    
    # Build model
    logger.info("Building GNN model...")
    model = build_gnn_model(input_dim=2048, hidden_dim=128, output_dim=1)
    device = get_device()
    model = model.to(device)
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")
    
    # Train model
    logger.info("Starting training...")
    try:
        trained_model = train_model(
            model, 
            train_data, 
            val_data, 
            epochs=args.epochs, 
            device=device
        )
    except RuntimeError as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)
    
    # Save model
    output_path = PROCESSED_DIR / args.output
    torch.save({
        "model_state_dict": trained_model.state_dict(),
        "seed": args.seed,
        "timestamp": datetime.utcnow().isoformat()
    }, output_path)
    
    logger.info(f"Model saved to {output_path}")
    
    # Versioning: Compute hash and update state
    model_hash = compute_file_hash(output_path)
    update_state_file(output_path, model_hash)
    
    # Save seeds
    save_seeds(args.seed, PROCESSED_DIR / "training_seeds.json")
    
    logger.info("Training pipeline completed successfully")

if __name__ == "__main__":
    main()