import os
import sys
import json
import logging
import random
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
import yaml

from model import MPNN, RidgeBaseline, build_gnn_model, build_baseline_model, prepare_gnn_data
from utils import get_device, get_logger, setup_logging
from hash_artifacts import compute_file_hash, update_state_file

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-379-predicting-molecular-excitation-waveleng"
STATE_DIR = PROJECT_ROOT / "state"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_OUTPUT_PATH = PROCESSED_DIR / "model.pt"
STATE_FILE = STATE_DIR / f"{PROJECT_NAME}.yaml"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def load_data_splits() -> Dict[str, pd.DataFrame]:
    """Load train, val, and test splits from processed CSV."""
    split_file = PROCESSED_DIR / "train_val_test.csv"
    if not split_file.exists():
        raise FileNotFoundError(f"Split file not found: {split_file}")
    
    df = pd.read_csv(split_file)
    # Assuming the file has columns: smi, lambda_max, scaffold_id, split
    # We need to separate them based on the 'split' column if it exists,
    # or load specific split files if the previous step created them.
    # Based on T010.5, we expect a single file with split indicators or separate files.
    # Let's assume standard convention: separate files or a 'split' column.
    # Given T010 output is split_indices.json, T010.5 creates the combined CSV.
    # Let's assume the combined CSV has a 'split' column ('train', 'val', 'test').
    
    if 'split' in df.columns:
        train_df = df[df['split'] == 'train']
        val_df = df[df['split'] == 'val']
        test_df = df[df['split'] == 'test']
    else:
        # Fallback if columns are named differently or files are separate
        # This logic depends on exact T010.5 output format. 
        # Assuming T010.5 creates a file with a 'split' column for robustness.
        raise ValueError("Expected 'split' column in train_val_test.csv")

    return {
        'train': train_df.reset_index(drop=True),
        'val': val_df.reset_index(drop=True),
        'test': test_df.reset_index(drop=True)
    }

def preprocess_df(df: pd.DataFrame, device: torch.device) -> tuple:
    """
    Convert DataFrame to PyTorch Geometric Data objects.
    Returns a DataLoader.
    """
    from model import build_gnn_model, prepare_gnn_data
    
    # This function relies on `prepare_gnn_data` from model.py which should handle
    # the conversion of SMILES to Graph Data objects.
    # Since the API surface for model.py shows `prepare_gnn_data`, we use it.
    # However, `prepare_gnn_data` likely expects a list of SMILES or a DataFrame.
    # Let's assume it returns a list of Data objects or a PyG Dataset.
    
    # We need to extract features and targets
    smiles_list = df['smi'].tolist()
    targets = torch.tensor(df['lambda_max'].values, dtype=torch.float32)
    
    # Prepare graph data
    # Note: prepare_gnn_data is expected to handle the RDKit conversion and graph building
    # based on the API surface provided.
    graph_data_list = prepare_gnn_data(smiles_list)
    
    if not graph_data_list:
        raise ValueError("No graph data generated from input SMILES.")

    # Create dataset and loader
    dataset = torch_geometric.data.InMemoryDataset() # Placeholder for actual dataset class if needed
    # Actually, let's just create a simple list of Data objects and use a custom loader or standard one
    # Since we don't have a specific Dataset class in the API, we'll create a TensorDataset-like structure
    # or just iterate. But for training loop, DataLoader is best.
    
    # Let's assume we stack features if possible, or use a custom collate function.
    # For simplicity in this context, we'll use a list and a custom collate if needed,
    # but standard practice with PyG is to use a DataLoader with a list of Data objects.
    from torch_geometric.loader import DataLoader as PyGDataLoader
    
    loader = PyGDataLoader(graph_data_list, batch_size=32, shuffle=True)
    return loader, targets # targets might need to be aligned with the dataset if not stored in Data

def train_model(model: nn.Module, train_loader: DataLoader, val_loader: DataLoader, device: torch.device, epochs: int = 100, patience: int = 10) -> Dict[str, Any]:
    """
    Train the model with early stopping.
    """
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)

    best_val_loss = float('inf')
    patience_counter = 0
    history = {'train_loss': [], 'val_loss': []}

    logger.info(f"Starting training for {epochs} epochs on {device}")

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            # Assuming batch.x, batch.edge_index, batch.edge_attr, batch.y exist
            # We need to ensure the targets are passed correctly.
            # If `prepare_gnn_data` didn't attach y, we need to handle that.
            # Let's assume the Data objects have 'y' attribute set during preparation.
            if hasattr(batch, 'y'):
                out = model(batch)
                loss = criterion(out, batch.y)
            else:
                # Fallback if y is not in batch (unlikely if prepare_gnn_data is correct)
                raise ValueError("Batch does not contain target 'y'. Check prepare_gnn_data.")
            
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch.num_graphs

        avg_train_loss = train_loss / len(train_loader.dataset) if len(train_loader.dataset) > 0 else 0
        history['train_loss'].append(avg_train_loss)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                if hasattr(batch, 'y'):
                    out = model(batch)
                    loss = criterion(out, batch.y)
                    val_loss += loss.item() * batch.num_graphs
        
        avg_val_loss = val_loss / len(val_loader.dataset) if len(val_loader.dataset) > 0 else 0
        history['val_loss'].append(avg_val_loss)
        scheduler.step(avg_val_loss)

        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}")

        # Early Stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model state temporarily
            torch.save(model.state_dict(), str(PROCESSED_DIR / "best_model_temp.pt"))
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

    # Load best model
    model.load_state_dict(torch.load(str(PROCESSED_DIR / "best_model_temp.pt")))
    return history

def main():
    """
    Main entry point for training.
    Includes versioning step: generate hash for model.pt and update state YAML.
    """
    setup_logging()
    logger.info("Starting Training Pipeline")

    # 1. Setup
    device = get_device()
    set_seed(42)

    # 2. Load Data
    try:
        splits = load_data_splits()
        train_loader, _ = preprocess_df(splits['train'], device)
        val_loader, _ = preprocess_df(splits['val'], device)
        test_loader, _ = preprocess_df(splits['test'], device)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # 3. Build Model
    # Using MPNN as per T014
    model = build_gnn_model()
    model = model.to(device)
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters())}")

    # 4. Train
    history = train_model(model, train_loader, val_loader, device, epochs=100, patience=10)

    # 5. Save Model
    torch.save(model.state_dict(), str(MODEL_OUTPUT_PATH))
    logger.info(f"Model saved to {MODEL_OUTPUT_PATH}")

    # 6. Versioning Step (T020 Requirement)
    # Generate hash for model.pt
    model_hash = compute_file_hash(MODEL_OUTPUT_PATH)
    logger.info(f"Model hash: {model_hash}")

    # Update state YAML
    state_entry = {
        "model_hash": model_hash,
        "model_path": str(MODEL_OUTPUT_PATH),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "epochs_trained": len(history['train_loss']),
        "best_val_loss": min(history['val_loss'])
    }

    update_state_file(
        state_file_path=STATE_FILE,
        artifact_name="model.pt",
        new_hash=model_hash,
        metadata=state_entry
    )
    logger.info(f"State file updated at {STATE_FILE}")

    logger.info("Training completed successfully.")

if __name__ == "__main__":
    main()