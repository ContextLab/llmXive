import os
import sys
import json
import logging
import random
import subprocess
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import torch
from rdkit import Chem
from rdkit.Chem import MolFingerprint, Descriptors
from rdkit import DataStructs

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger
from models.mpnn import MPNNConfig, create_mpnn_from_config

logger = get_logger(__name__)

class TrainingConfig:
    def __init__(self, epochs=10, lr=0.01, batch_size=32, max_configs=50):
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.max_configs = max_configs

def load_processed_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    df = pd.read_csv(file_path)
    return df

def prepare_features(df: pd.DataFrame):
    # In a real implementation, this would parse descriptor strings into numeric vectors.
    # For the scaffold split logic, we just need the SMILES column.
    if 'smiles' not in df.columns:
        raise ValueError("DataFrame must contain 'smiles' column for scaffold splitting.")
    return df

def get_scaffold(smiles: str) -> str:
    """
    Generates a unique scaffold identifier for a given SMILES string using RDKit.
    Uses the Morgan fingerprint (radius 2) to represent the scaffold.
    """
    try:
        mol = Chem.SmilesMol(smiles)
        if mol is None:
            return "INVALID"
        # Generate Morgan fingerprint (radius 2) which captures the local scaffold structure
        fp = MolFingerprint(mol, fpType='morgan', radius=2)
        # Convert to a hashable string representation
        return fp.ToBitString()
    except Exception as e:
        logger.warning(f"Failed to generate scaffold for {smiles}: {e}")
        return "ERROR"

def scaffold_split(df: pd.DataFrame, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, random_state=42):
    """
    Performs a scaffold split to ensure molecules with identical scaffolds
    do not appear in both training and test sets.
    """
    logger.info("Performing scaffold split...")
    
    # Generate scaffolds
    df['scaffold'] = df['smiles'].apply(get_scaffold)
    
    # Group by scaffold
    scaffold_groups = df.groupby('scaffold')
    
    # Get unique scaffolds
    scaffolds = list(scaffold_groups.groups.keys())
    
    # Shuffle scaffolds
    rng = random.Random(random_state)
    rng.shuffle(scaffolds)
    
    # Calculate split sizes
    total_scaffolds = len(scaffolds)
    train_count = int(total_scaffolds * train_ratio)
    val_count = int(total_scaffolds * val_ratio)
    # test_count is the remainder
    
    train_scaffolds = scaffolds[:train_count]
    val_scaffolds = scaffolds[train_count:train_count + val_count]
    test_scaffolds = scaffolds[train_count + val_count:]
    
    # Assign rows to splits
    train_mask = df['scaffold'].isin(train_scaffolds)
    val_mask = df['scaffold'].isin(val_scaffolds)
    test_mask = df['scaffold'].isin(test_scaffolds)
    
    train_df = df[train_mask]
    val_df = df[val_mask]
    test_df = df[test_mask]
    
    logger.info(f"Scaffold split completed: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    # Verify no leakage
    train_scaffolds_set = set(train_df['scaffold'].unique())
    test_scaffolds_set = set(test_df['scaffold'].unique())
    if train_scaffolds_set & test_scaffolds_set:
        raise RuntimeError("Data leakage detected: Scaffolds found in both train and test sets.")
    
    return train_df, val_df, test_df

def generate_random_config():
    return {
        'hidden_dim': random.choice([32, 64, 128]),
        'num_layers': random.choice([1, 2, 3, 4]),
        'dropout': random.choice([0.1, 0.2, 0.3])
    }

def evaluate_model(model, data):
    # Dummy evaluation for now
    return {'r2': 0.5, 'mae': 0.1}

def train_epoch(model, data, optimizer):
    pass

def train_model(model, data, config):
    for epoch in range(config.epochs):
        train_epoch(model, data, None)
    return model

def run_training_with_timeout(config, df, timeout_seconds=300):
    """
    Runs training in a subprocess with a timeout to prevent hanging.
    """
    # This is a placeholder for the actual subprocess logic.
    # In a real implementation, this would spawn a new process.
    logger.info(f"Running training with timeout {timeout_seconds}s")
    start = time.time()
    try:
        # Simulate training
        time.sleep(1) 
        return True
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return False

def run_random_search(df, num_iterations=5, max_configs=None):
    if max_configs is not None:
        num_iterations = min(num_iterations, max_configs)
        
    best_config = None
    best_score = -float('inf')
    results = []
    
    for i in range(num_iterations):
        cfg = generate_random_config()
        mpnn_cfg = MPNNConfig(input_dim=10, **cfg)
        model = create_mpnn_from_config(mpnn_cfg)
        score = evaluate_model(model, df)
        results.append({'config': cfg, 'score': score})
        
        if score['r2'] > best_score:
            best_score = score['r2']
            best_config = cfg

    return best_config, results

def save_results(results, output_path):
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Train MPNN model")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--search_iterations", type=int, default=3)
    parser.add_argument("--input", type=str, default="data/processed/train.csv")
    parser.add_argument("--output", type=str, default="artifacts/best_model.pt")
    parser.add_argument("--max-configs", type=int, default=None, help="Max configs for hyperparameter search")
    args = parser.parse_args()

    ensure_dirs()
    
    df = load_processed_data(args.input)
    
    # Perform scaffold split if not already split
    if 'scaffold' not in df.columns:
        train_df, val_df, test_df = scaffold_split(df, random_state=42)
        # For this script, we assume the input is already split or we use the train part
        # In a real pipeline, we would save these splits to disk
        df = train_df 
    
    best_config, _ = run_random_search(df, num_iterations=args.search_iterations, max_configs=args.max_configs)
    
    # Train final model with best config
    mpnn_cfg = MPNNConfig(input_dim=10, **best_config)
    model = create_mpnn_from_config(mpnn_cfg)
    
    # Save model
    torch.save(model.state_dict(), args.output)
    logger.info(f"Best model saved to {args.output}")

if __name__ == "__main__":
    main()
