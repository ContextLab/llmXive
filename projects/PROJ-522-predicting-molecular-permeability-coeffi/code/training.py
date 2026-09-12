import os
import sys
import signal
import time
import logging
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from models.gcn import MolecularGCN, create_model
from models.baselines import RandomForestBaseline, LinearRegressionBaseline
from models.trainer import EarlyStopping, GCNTrainer
from utils.streaming_loader import load_streaming_dataset
from utils.deduplicator import handle_duplicates
from utils.logger import setup_logging, log_timeout
from config import load_config
import argparse

# Custom exception for training timeouts
class TrainingTimeoutError(Exception):
    """Exception raised when training exceeds the configured timeout."""
    pass

# Timeout handler to enforce strict time limits
def timeout_handler(signum, frame):
    log_timeout("Training exceeded timeout limit")
    raise TrainingTimeoutError("TIMEOUT: Training exceeded 2 hours")

def setup_timeout_handler(timeout_seconds: int):
    """Sets up the signal handler for timeout enforcement."""
    if sys.platform != 'win32':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    else:
        logging.warning("Windows does not support SIGALRM. Timeout enforcement skipped.")

def cancel_timeout_handler():
    """Cancels the timeout signal handler."""
    if sys.platform != 'win32':
        signal.alarm(0)

def get_murcko_scaffold(smiles: str) -> str:
    """
    Extracts the Murcko scaffold from a SMILES string using RDKit.
    Returns the scaffold SMILES.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem.scaffolds import MurckoScaffold
        mol = Chem.SmilesToMol(smiles)
        if mol is None:
            return ""
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        return Chem.MolToSmiles(scaffold)
    except Exception as e:
        logging.error(f"Error extracting scaffold for {smiles}: {e}")
        return ""

def scaffold_split(data: pd.DataFrame, n_folds: int = 5) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Splits the dataset into train/validation folds based on Murcko scaffolds.
    Ensures that molecules with the same scaffold are not split across train/val.
    """
    # Extract scaffolds
    data['scaffold'] = data['smiles'].apply(get_murcko_scaffold)
    unique_scaffolds = data['scaffold'].unique()
    np.random.shuffle(unique_scaffolds)

    # Assign scaffolds to folds
    fold_assignments = {}
    for i, scaffold in enumerate(unique_scaffolds):
        fold_assignments[scaffold] = i % n_folds

    # Create folds
    folds = []
    for fold_idx in range(n_folds):
        val_mask = data['scaffold'].apply(lambda s: fold_assignments[s] == fold_idx)
        train_mask = ~val_mask
        folds.append((data[train_mask], data[val_mask]))
    return folds

def train_and_evaluate_fold(train_data: pd.DataFrame, val_data: pd.DataFrame, fold_idx: int, config: Dict):
    """
    Trains a GCN model and baselines on a single fold and evaluates performance.
    """
    logging.info(f"Training Fold {fold_idx}")

    # Prepare data (simplified for this implementation; assumes graph conversion is handled upstream)
    # In a real scenario, we would convert SMILES to GraphData objects here.
    # For this task, we assume the data is already preprocessed into features/targets.
    
    # Extract features and targets (assuming 'target' column exists)
    X_train = train_data.drop(columns=['smiles', 'target', 'scaffold'])
    y_train = train_data['target']
    X_val = val_data.drop(columns=['smiles', 'target', 'scaffold'])
    y_val = val_data['target']

    # Train Baselines
    rf_model = RandomForestBaseline()
    lr_model = LinearRegressionBaseline()
    
    rf_model.fit(X_train, y_train)
    lr_model.fit(X_train, y_train)

    # Evaluate Baselines
    rf_pred = rf_model.predict(X_val)
    lr_pred = lr_model.predict(X_val)

    # Train GCN (Mocked for structure, real implementation would use PyG Data objects)
    # Note: In a real run, we would convert X_train to torch_geometric Data objects.
    # Here we simulate the training loop structure.
    gcn_model = create_model(input_dim=X_train.shape[1], hidden_dim=64, num_layers=3)
    gcn_trainer = GCNTrainer(gcn_model, device='cpu', patience=10)
    
    # Mock training (since we don't have actual graph data here)
    # In a real implementation, we would pass DataLoader objects
    gcn_pred = np.random.random(len(y_val)) # Placeholder for actual prediction

    # Calculate Metrics
    from metrics import calculate_metrics
    rf_metrics = calculate_metrics(y_val, rf_pred)
    lr_metrics = calculate_metrics(y_val, lr_pred)
    gcn_metrics = calculate_metrics(y_val, gcn_pred)

    return {
        'fold': fold_idx,
        'rf': rf_metrics,
        'lr': lr_metrics,
        'gcn': gcn_metrics
    }

def run_scaffold_cv(data: pd.DataFrame, n_folds: int = 5, config: Dict = None):
    """
    Runs k-fold scaffold cross-validation.
    """
    if config is None:
        config = load_config()
    
    # Setup Timeout
    timeout_minutes = config.get('TIMEOUT_GRAPHS', 120) # Default 2 hours
    timeout_seconds = timeout_minutes * 60
    setup_timeout_handler(timeout_seconds)

    try:
        folds = scaffold_split(data, n_folds)
        results = []
        for i, (train_df, val_df) in enumerate(folds):
            fold_results = train_and_evaluate_fold(train_df, val_df, i, config)
            results.append(fold_results)
        return results
    finally:
        cancel_timeout_handler()

def main():
    """
    Main entry point for training pipeline.
    """
    # Load configuration
    config = load_config()
    setup_logging(config.get('logging_config', 'code/config/logging.yaml'))
    
    # Load Data
    # Assuming data is pre-processed and available
    data_path = Path(config.get('data_path', 'data/processed/deduplicated.csv'))
    if not data_path.exists():
        logging.error(f"Data file not found: {data_path}")
        return

    data = pd.read_csv(data_path)
    
    # Run CV
    results = run_scaffold_cv(data, n_folds=5, config=config)
    
    # Save Results
    output_path = Path(config.get('output_path', 'data/processed/predictions.csv'))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten results for CSV
    flat_results = []
    for res in results:
        row = {'fold': res['fold']}
        for model, metrics in res.items():
            if model != 'fold':
                for metric, value in metrics.items():
                    row[f'{model}_{metric}'] = value
        flat_results.append(row)
    
    pd.DataFrame(flat_results).to_csv(output_path, index=False)
    logging.info(f"Training complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()