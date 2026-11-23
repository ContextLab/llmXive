"""
Training loop for Polymer Degradation GNN with k-fold cross-validation.
Implements random seed pinning, convergence checks, and macro-F1 reporting.
"""
import os
import sys
import json
import logging
import random
import time
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import numpy as np
from torch_geometric.data import Data, Batch
from torch_geometric.loader import DataLoader
from sklearn.model_selection import StratifiedKFold, LeaveOneOut
from sklearn.metrics import f1_score

# Import local utilities
from utils import get_logger, get_project_paths, setup_logging
from model import PolymerGNN, create_model_from_config, validate_model_constraints

# Constants
SEED = 42
DEFAULT_K_FOLDS = 5
CONVERGENCE_WINDOW = 5
CONVERGENCE_THRESHOLD = 0.05  # 5% change
DEVICE = "cpu"  # Enforced CPU-only per FR-003

logger = get_logger(__name__)

def set_seed(seed: int = SEED) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Random seed set to {seed}")

def load_graph_data(csv_path: str) -> Tuple[List[Data], List[int]]:
    """
    Load graph data from processed CSV.
    Expected columns: 'node_features' (tensor string), 'edge_index' (tensor string), 'label'
    """
    logger.info(f"Loading graph data from {csv_path}")
    data_list = []
    labels = []
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Parse node features and edge index from string representations
                # Assuming format stored as stringified lists or tensors
                # For robustness, we expect the preprocessing to save valid tensor strings
                node_features = torch.tensor(
                    json.loads(row['node_features']), dtype=torch.float
                )
                edge_index = torch.tensor(
                    json.loads(row['edge_index']), dtype=torch.long
                ).view(2, -1)
                label = int(row['label'])
                
                data = Data(x=node_features, edge_index=edge_index, y=label)
                data_list.append(data)
                labels.append(label)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Skipping malformed row: {e}")
                continue

    if len(data_list) == 0:
        raise ValueError("No valid data records loaded from CSV.")

    logger.info(f"Loaded {len(data_list)} graphs with labels: {np.bincount(labels)}")
    return data_list, labels

def stratified_k_fold_split(
    data_list: List[Data], 
    labels: List[int], 
    n_splits: int = DEFAULT_K_FOLDS
) -> List[Tuple[List[int], List[int]]]:
    """
    Perform stratified k-fold cross-validation split on indices.
    Returns list of (train_indices, val_indices) tuples.
    """
    if len(set(labels)) < 2:
        logger.warning("Less than 2 classes found; falling back to random split.")
        # Fallback if stratification fails
        indices = list(range(len(data_list)))
        random.shuffle(indices)
        split_idx = int(len(indices) * 0.8)
        return [(indices[:split_idx], indices[split_idx:])]

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    folds = []
    for train_idx, val_idx in skf.split(data_list, labels):
        folds.append((list(train_idx), list(val_idx)))
    
    logger.info(f"Generated {len(folds)} stratified folds")
    return folds

def leave_one_out_splits(
    data_list: List[Data], 
    labels: List[int]
) -> List[Tuple[List[int], List[int]]]:
    """
    Perform leave-one-out cross-validation.
    """
    loo = LeaveOneOut()
    folds = []
    for train_idx, val_idx in loo.split(data_list):
        folds.append((list(train_idx), list(val_idx)))
    
    logger.info(f"Generated {len(folds)} leave-one-out folds")
    return folds

def train_epoch(
    model: nn.Module, 
    loader: DataLoader, 
    optimizer: torch.optim.Optimizer, 
    criterion: nn.Module, 
    device: str
) -> float:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out = model(batch.x, batch.edge_index, batch.batch)
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    
    return total_loss / len(loader.dataset)

def evaluate_model(
    model: nn.Module, 
    loader: DataLoader, 
    criterion: nn.Module, 
    device: str
) -> Tuple[float, List[int], List[int]]:
    """Evaluate model, return loss, true labels, predicted labels."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_true = []
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = criterion(out, batch.y)
            total_loss += loss.item() * batch.num_graphs
            
            preds = out.argmax(dim=1).cpu().tolist()
            all_preds.extend(preds)
            all_true.extend(batch.y.cpu().tolist())
    
    avg_loss = total_loss / len(loader.dataset) if len(loader.dataset) > 0 else 0.0
    return avg_loss, all_true, all_preds

def check_convergence(
    history: List[float], 
    window: int = CONVERGENCE_WINDOW, 
    threshold: float = CONVERGENCE_THRESHOLD
) -> bool:
    """
    Check if loss has converged.
    Converged if the relative change in the last 'window' epochs is < threshold.
    """
    if len(history) < window:
        return False
    
    recent = history[-window:]
    # Check max relative change in the window
    max_change = 0.0
    for i in range(1, len(recent)):
        if abs(recent[i-1]) > 1e-9:
            change = abs(recent[i] - recent[i-1]) / abs(recent[i-1])
            max_change = max(max_change, change)
    
    converged = max_change < threshold
    logger.debug(f"Convergence check: max_change={max_change:.4f}, threshold={threshold}, converged={converged}")
    return converged

def train_fold(
    fold_idx: int,
    train_indices: List[int],
    val_indices: List[int],
    data_list: List[Data],
    model_cfg: Dict[str, Any],
    device: str,
    epochs: int = 50,
    lr: float = 0.01,
    batch_size: int = 32
) -> Dict[str, Any]:
    """Train and evaluate a single fold."""
    logger.info(f"--- Training Fold {fold_idx + 1} ---")
    
    # Create datasets
    train_data = [data_list[i] for i in train_indices]
    val_data = [data_list[i] for i in val_indices]
    
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    # Assuming input_dim is inferred or passed in config
    # For robustness, we try to infer from first graph if not in config
    if 'input_dim' not in model_cfg:
        sample_x = train_data[0].x
        model_cfg['input_dim'] = sample_x.shape[1]
    
    model = create_model_from_config(model_cfg).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    history = []
    best_val_loss = float('inf')
    best_model_state = None
    
    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss, val_true, val_preds = evaluate_model(model, val_loader, criterion, device)
        
        # Calculate F1
        if len(set(val_true)) > 1:
            macro_f1 = f1_score(val_true, val_preds, average='macro')
        else:
            macro_f1 = 0.0
        
        history.append(val_loss)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Macro-F1: {macro_f1:.4f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
        
        # Early stopping check (convergence)
        if check_convergence(history):
            logger.info(f"Converged at epoch {epoch+1}")
            break
    
    # Final evaluation with best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    final_val_loss, final_true, final_preds = evaluate_model(model, val_loader, criterion, device)
    final_macro_f1 = f1_score(final_true, final_preds, average='macro') if len(set(final_true)) > 1 else 0.0
    
    return {
        "fold": fold_idx + 1,
        "best_val_loss": best_val_loss,
        "final_val_loss": final_val_loss,
        "final_macro_f1": final_macro_f1,
        "epochs_run": len(history),
        "converged": check_convergence(history)
    }

def main():
    """Main training entry point."""
    set_seed(SEED)
    paths = get_project_paths()
    
    # Configuration
    # Determine input dataset based on augmentation status
    # T016d -> final_augmented_dataset.csv
    input_csv = paths['processed'] / "final_augmented_dataset.csv"
    
    if not input_csv.exists():
        # Fallback to pre-augmented if augmented doesn't exist (should be covered by T025)
        input_csv = paths['processed'] / "pre_augmented_graph_dataset.csv"
        if not input_csv.exists():
            raise FileNotFoundError(f"Neither {paths['processed'] / 'final_augmented_dataset.csv'} nor {paths['processed'] / 'pre_augmented_graph_dataset.csv'} found.")
    
    logger.info(f"Using dataset: {input_csv}")
    
    # Load data
    data_list, labels = load_graph_data(str(input_csv))
    n_samples = len(data_list)
    
    # Determine CV strategy
    if n_samples < 50:
        logger.warning(f"Dataset size ({n_samples}) < 50. Using Leave-One-Out.")
        folds = leave_one_out_splits(data_list, labels)
    else:
        logger.info(f"Dataset size ({n_samples}) >= 50. Using Stratified K-Fold (k={DEFAULT_K_FOLDS}).")
        folds = stratified_k_fold_split(data_list, labels, n_splits=DEFAULT_K_FOLDS)
    
    # Model Config
    model_cfg = {
        "num_layers": 3,
        "hidden_dim": 128,
        "num_classes": len(set(labels)),
        "dropout": 0.1
    }
    
    # Validate constraints
    validate_model_constraints(model_cfg)
    
    # Training Results
    results = []
    for i, (train_idx, val_idx) in enumerate(folds):
        fold_result = train_fold(
            fold_idx=i,
            train_indices=train_idx,
            val_indices=val_idx,
            data_list=data_list,
            model_cfg=model_cfg,
            device=DEVICE,
            epochs=100,  # Max epochs
            lr=0.01,
            batch_size=32
        )
        results.append(fold_result)
    
    # Aggregate Results
    mean_f1 = np.mean([r['final_macro_f1'] for r in results])
    mean_val_loss = np.mean([r['final_val_loss'] for r in results])
    converged_count = sum(1 for r in results if r['converged'])
    
    summary = {
        "dataset_size": n_samples,
        "cv_strategy": "LOO" if n_samples < 50 else f"K-Fold ({DEFAULT_K_FOLDS})",
        "num_folds": len(folds),
        "mean_macro_f1": float(mean_f1),
        "mean_val_loss": float(mean_val_loss),
        "convergence_rate": f"{converged_count}/{len(folds)}",
        "fold_results": results,
        "seed": SEED,
        "device": DEVICE
    }
    
    # Save results
    report_path = paths['reports'] / "training_results.json"
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Training complete. Mean Macro-F1: {mean_f1:.4f}")
    logger.info(f"Results saved to {report_path}")
    
    return summary

if __name__ == "__main__":
    setup_logging()
    main()
