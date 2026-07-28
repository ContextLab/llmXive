"""
Training script for Polymer Degradation Pathway Prediction.

Implements k-fold cross-validation (or leave-one-out if n < 50) with
random seed pinning. Reports mean macro-F1 and convergence check.

Dependencies:
- T016: Requires processed datasets in data/processed/
- T021: Requires PolymerGNN model definition
- T022: Requires augmented datasets if applicable
"""
import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.utils import to_undirected
import torch.nn.functional as F

# Project imports matching API surface
from utils import get_logger, get_project_paths, setup_logging
from data_models import MolecularGraph
from model import PolymerGNN, validate_model_constraints, create_model_from_config
from preprocess import load_processed_polyester_dataset

# Constants
RANDOM_SEED = 42
MAX_EPOCHS = 100
LEARNING_RATE = 0.001
BATCH_SIZE = 32
CONVERGENCE_THRESHOLD = 0.05  # 5% loss change over last 5 epochs
CONVERGENCE_WINDOW = 5
MIN_SAMPLES_LOO = 50  # Use LOO if n < 50

logger = get_logger(__name__)


def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # Force CPU-only execution as per constraints
    os.environ["CUDA_VISIBLE_DEVICES"] = ""


def load_graph_data() -> List[Data]:
    """
    Load processed molecular graphs from data/processed/.
    Returns list of PyTorch Geometric Data objects.
    """
    paths = get_project_paths()
    processed_dir = paths["processed"]
    
    # Load from the main processed dataset file
    # Assuming T016 created data/processed/polyester_processed.pt or similar
    # We'll use the loader from preprocess module if available, otherwise construct manually
    try:
        # Try to load using the helper from preprocess if it returns Data objects
        graph_data = load_processed_polyester_dataset()
        if not isinstance(graph_data, list):
            # If it returns a single object or different structure, adapt
            graph_data = [graph_data] if graph_data is not None else []
        return graph_data
    except Exception as e:
        logger.error(f"Failed to load processed dataset: {e}")
        # Fallback: try to load from .pt file directly if it exists
        pt_file = Path(processed_dir) / "polyester_processed.pt"
        if pt_file.exists():
            logger.info(f"Loading from {pt_file}")
            return torch.load(pt_file, weights_only=False)
        else:
            raise FileNotFoundError(
                f"No processed dataset found. Expected {pt_file}. "
                "Ensure T016 has completed successfully."
            )


def stratified_k_fold_split(
    data: List[Data], n_splits: int = 5
) -> List[Tuple[List[int], List[int]]]:
    """
    Create stratified k-fold splits based on degradation labels.
    Returns list of (train_indices, val_indices) tuples.
    """
    if len(data) < n_splits:
        logger.warning(f"Dataset size ({len(data)}) < folds ({n_splits}). "
                     "Reducing folds to dataset size.")
        n_splits = len(data)
    
    # Extract labels
    labels = [d.y.item() if hasattr(d.y, 'item') else d.y for d in data]
    unique_labels = sorted(set(labels))
    
    # Group indices by label
    label_to_indices = {label: [] for label in unique_labels}
    for idx, label in enumerate(labels):
        label_to_indices[label].append(idx)
    
    # Shuffle indices within each label group
    for label in unique_labels:
        random.shuffle(label_to_indices[label])
    
    # Create folds
    folds = [[] for _ in range(n_splits)]
    for label, indices in label_to_indices.items():
        for i, idx in enumerate(indices):
            folds[i % n_splits].append(idx)
    
    # Generate train/val splits
    splits = []
    for i in range(n_splits):
        val_indices = folds[i]
        train_indices = []
        for j in range(n_splits):
            if i != j:
                train_indices.extend(folds[j])
        splits.append((train_indices, val_indices))
    
    return splits


def leave_one_out_splits(data: List[Data]) -> List[Tuple[List[int], List[int]]]:
    """
    Generate leave-one-out cross-validation splits.
    Returns list of (train_indices, val_indices) tuples.
    """
    n = len(data)
    splits = []
    for i in range(n):
        val_indices = [i]
        train_indices = [j for j in range(n) if j != i]
        splits.append((train_indices, val_indices))
    return splits


def train_epoch(
    model: PolymerGNN, 
    loader: DataLoader, 
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> float:
    """Train for one epoch and return average loss."""
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # Forward pass
        out = model(batch.x, batch.edge_index, batch.batch)
        
        # Compute loss (assuming classification)
        loss = F.cross_entropy(out, batch.y)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / max(num_batches, 1)


def evaluate_model(
    model: PolymerGNN,
    loader: DataLoader,
    device: torch.device
) -> Tuple[float, float]:
    """Evaluate model and return (loss, macro-F1)."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []
    num_batches = 0
    
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = F.cross_entropy(out, batch.y)
            
            total_loss += loss.item()
            preds = torch.argmax(out, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch.y.cpu().numpy())
            num_batches += 1
    
    avg_loss = total_loss / max(num_batches, 1)
    
    # Calculate macro-F1
    from sklearn.metrics import f1_score
    macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    
    return avg_loss, macro_f1


def check_convergence(loss_history: List[float]) -> bool:
    """
    Check if loss has converged (within 5% over last CONVERGENCE_WINDOW epochs).
    """
    if len(loss_history) < CONVERGENCE_WINDOW:
        return False
    
    recent_losses = loss_history[-CONVERGENCE_WINDOW:]
    avg_recent = np.mean(recent_losses)
    
    # Check if all recent losses are within 5% of the average
    for loss in recent_losses:
        if abs(loss - avg_recent) / (avg_recent + 1e-8) > CONVERGENCE_THRESHOLD:
            return False
    
    return True


def train_fold(
    train_indices: List[int],
    val_indices: List[int],
    data: List[Data],
    device: torch.device,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Train model on one fold and return metrics."""
    # Prepare data
    train_data = [data[i] for i in train_indices]
    val_data = [data[i] for i in val_indices]
    
    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=BATCH_SIZE, shuffle=False)
    
    # Initialize model
    model = create_model_from_config(config)
    model = model.to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    
    loss_history = []
    best_val_f1 = 0.0
    patience_counter = 0
    max_patience = 10
    converged = False
    final_epoch = 0
    
    for epoch in range(1, MAX_EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss, val_f1 = evaluate_model(model, val_loader, device)
        
        loss_history.append(val_loss)
        scheduler.step(val_loss)
        
        logger.info(f"Epoch {epoch:03d} | Train Loss: {train_loss:.4f} | "
                   f"Val Loss: {val_loss:.4f} | Val F1: {val_f1:.4f}")
        
        # Early stopping
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            patience_counter = 0
            # Save best model state
            best_model_state = model.state_dict().copy()
        else:
            patience_counter += 1
        
        # Convergence check
        if check_convergence(loss_history):
            converged = True
            logger.info(f"Convergence detected at epoch {epoch}")
            final_epoch = epoch
            break
        
        if patience_counter >= max_patience:
            logger.info(f"Early stopping at epoch {epoch}")
            final_epoch = epoch
            break
        
        final_epoch = epoch
    
    # Load best model
    model.load_state_dict(best_model_state)
    
    # Final evaluation
    final_val_loss, final_val_f1 = evaluate_model(model, val_loader, device)
    
    return {
        "fold_val_loss": final_val_loss,
        "fold_val_f1": final_val_f1,
        "epochs_run": final_epoch,
        "converged": converged,
        "best_val_f1": best_val_f1
    }


def main():
    """Main training loop with cross-validation."""
    # Setup
    setup_logging(level=logging.INFO)
    set_seed(RANDOM_SEED)
    
    paths = get_project_paths()
    device = torch.device("cpu")  # Force CPU as per constraints
    
    logger.info("Starting training for Polymer Degradation Pathways")
    logger.info(f"Device: {device}")
    logger.info(f"Random seed: {RANDOM_SEED}")
    
    # Load data
    logger.info("Loading processed dataset...")
    try:
        data = load_graph_data()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    n_samples = len(data)
    logger.info(f"Loaded {n_samples} samples")
    
    if n_samples == 0:
        logger.error("No samples found in dataset. Exiting.")
        sys.exit(1)
    
    # Determine CV strategy
    if n_samples < MIN_SAMPLES_LOO:
        logger.info(f"Dataset size ({n_samples}) < {MIN_SAMPLES_LOO}. "
                   f"Using Leave-One-Out cross-validation.")
        splits = leave_one_out_splits(data)
        n_folds = n_samples
    else:
        n_folds = min(5, n_samples)  # At most 5 folds
        logger.info(f"Using {n_folds}-fold stratified cross-validation.")
        splits = stratified_k_fold_split(data, n_folds)
    
    # Model configuration
    config = {
        "num_features": data[0].x.shape[1] if hasattr(data[0].x, 'shape') else 0,
        "num_classes": len(set(d.y.item() if hasattr(d.y, 'item') else d.y for d in data)),
        "hidden_dim": 128,
        "num_layers": 3,
        "dropout": 0.1
    }
    
    # Validate model constraints
    if not validate_model_constraints(config):
        logger.error("Model configuration violates constraints (layers > 3 or dim > 128).")
        sys.exit(1)
    
    logger.info(f"Model config: {config}")
    
    # Training
    fold_results = []
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        logger.info(f"\n{'='*50}")
        logger.info(f"Fold {fold_idx + 1}/{len(splits)}")
        logger.info(f"Train size: {len(train_idx)}, Val size: {len(val_idx)}")
        
        result = train_fold(train_idx, val_idx, data, device, config)
        result["fold_number"] = fold_idx + 1
        fold_results.append(result)
        logger.info(f"Fold {fold_idx + 1} - Val F1: {result['fold_val_f1']:.4f}, "
                   f"Converged: {result['converged']}")
    
    # Aggregate results
    mean_f1 = np.mean([r["fold_val_f1"] for r in fold_results])
    std_f1 = np.std([r["fold_val_f1"] for r in fold_results])
    mean_loss = np.mean([r["fold_val_loss"] for r in fold_results])
    converged_count = sum(1 for r in fold_results if r["converged"])
    
    results = {
        "n_samples": n_samples,
        "n_folds": len(splits),
        "cv_strategy": "leave_one_out" if n_samples < MIN_SAMPLES_LOO else "k_fold",
        "mean_macro_f1": mean_f1,
        "std_macro_f1": std_f1,
        "mean_val_loss": mean_loss,
        "converged_folds": converged_count,
        "total_folds": len(splits),
        "fold_results": fold_results,
        "config": config,
        "random_seed": RANDOM_SEED
    }
    
    # Save results
    reports_dir = Path(paths["reports"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = reports_dir / "training_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n{'='*50}")
    logger.info("TRAINING COMPLETE")
    logger.info(f"Mean Macro-F1: {mean_f1:.4f} (+/- {std_f1:.4f})")
    logger.info(f"Mean Validation Loss: {mean_loss:.4f}")
    logger.info(f"Convergence: {converged_count}/{len(splits)} folds")
    logger.info(f"Results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    main()