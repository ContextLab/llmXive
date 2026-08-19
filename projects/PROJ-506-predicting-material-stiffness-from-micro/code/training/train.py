"""
Training script for the stiffness prediction CNN.

Implements training loop with Adam optimizer, k-fold cross-validation,
and convergence criteria.
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from code.training.model import create_model
from code.training.kfold_utils import stratified_k_fold_split, load_dataset_metadata
from code.utils.metrics import mean_squared_error, r2_score

logger = logging.getLogger(__name__)

def load_dataset(metadata_file: Path) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """
    Load dataset from metadata file.
    
    Args:
        metadata_file: Path to metadata JSON file
        
    Returns:
        Tuple of (images, stiffness_tensors, metadata_list)
    """
    import json
    from skimage import io
    import numpy as np
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    images = []
    stiffness = []
    
    for entry in metadata:
        # Load image
        img = io.imread(entry['image_path'])
        img = (img > 128).astype(np.float32)
        img = img.reshape(1, 128, 128)  # Add channel dimension
        images.append(img)
        
        # Load stiffness tensor
        stiff = np.array(entry['stiffness_tensor'])
        stiffness.append(stiff)
    
    return np.array(images), np.array(stiffness), metadata

def train_epoch(
    model: torch.nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: str
) -> float:
    """
    Train for one epoch.
    
    Args:
        model: Model to train
        dataloader: Training data loader
        criterion: Loss function
        optimizer: Optimizer
        device: Device to use
        
    Returns:
        Average training loss for the epoch
    """
    model.train()
    total_loss = 0.0
    
    for batch_images, batch_targets in dataloader:
        batch_images = batch_images.to(device)
        batch_targets = batch_targets.to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(batch_images)
        loss = criterion(outputs, batch_targets)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(dataloader)

def validate_epoch(
    model: torch.nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: str
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Validate for one epoch.
    
    Args:
        model: Model to validate
        dataloader: Validation data loader
        criterion: Loss function
        device: Device to use
        
    Returns:
        Tuple of (average validation loss, predictions, targets)
    """
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch_images, batch_targets in dataloader:
            batch_images = batch_images.to(device)
            batch_targets = batch_targets.to(device)
            
            # Forward pass
            outputs = model(batch_images)
            loss = criterion(outputs, batch_targets)
            
            total_loss += loss.item()
            all_preds.append(outputs.cpu().numpy())
            all_targets.append(batch_targets.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    all_preds = np.concatenate(all_preds, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)
    
    return avg_loss, all_preds, all_targets

def train_model(
    images: np.ndarray,
    stiffness: np.ndarray,
    metadata: List[Dict],
    n_folds: int = 5,
    epochs: int = 50,
    batch_size: int = 32,
    patience: int = 10,
    device: str = 'cpu'
) -> Dict:
    """
    Train model with k-fold cross-validation.
    
    Args:
        images: Input images array
        stiffness: Target stiffness tensors
        metadata: List of metadata dictionaries
        n_folds: Number of folds for cross-validation
        epochs: Maximum number of epochs
        batch_size: Batch size for training
        patience: Early stopping patience
        device: Device to use
        
    Returns:
        Dictionary with training results
    """
    logger.info(f"Starting training with {n_folds}-fold cross-validation")
    
    # Convert to tensors
    X_tensor = torch.FloatTensor(images)
    y_tensor = torch.FloatTensor(stiffness)
    
    # Create stratification labels
    density_labels = np.array([m['inclusion_density'] for m in metadata])
    topology_labels = np.array([m['topology_type'] for m in metadata])
    
    # Combine for stratification
    strat_labels = [f"{d:.1f}_{t}" for d, t in zip(density_labels, topology_labels)]
    
    fold_results = []
    
    # Perform k-fold split
    for fold_idx, (train_idx, val_idx) in enumerate(
        stratified_k_fold_split(
            n_samples=len(images),
            strat_labels=strat_labels,
            n_folds=n_folds
        )
    ):
        logger.info(f"--- Fold {fold_idx + 1}/{n_folds} ---")
        
        # Split data
        X_train, X_val = X_tensor[train_idx], X_tensor[val_idx]
        y_train, y_val = y_tensor[train_idx], y_tensor[val_idx]
        
        # Create data loaders
        train_dataset = TensorDataset(X_train, y_train)
        val_dataset = TensorDataset(X_val, y_val)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # Initialize model
        model = create_model(input_size=128, output_dim=4, device=device)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Training loop with early stopping
        best_val_loss = float('inf')
        patience_counter = 0
        epoch_losses = []
        
        for epoch in range(epochs):
            train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
            val_loss, val_preds, val_targets = validate_epoch(model, val_loader, criterion, device)
            
            epoch_losses.append({'train': train_loss, 'val': val_loss})
            
            # Calculate R2 for this fold
            r2 = r2_score(val_targets.flatten(), val_preds.flatten())
            
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, "
                        f"Val Loss: {val_loss:.4f}, R2: {r2:.4f}")
            
            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model state
                best_model_state = model.state_dict().copy()
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
        
        # Load best model for evaluation
        model.load_state_dict(best_model_state)
        
        # Final validation
        _, final_preds, final_targets = validate_epoch(model, val_loader, criterion, device)
        final_mse = mean_squared_error(final_targets.flatten(), final_preds.flatten())
        final_r2 = r2_score(final_targets.flatten(), final_preds.flatten())
        
        fold_results.append({
            'fold': fold_idx + 1,
            'final_mse': final_mse,
            'final_r2': final_r2,
            'best_val_loss': best_val_loss,
            'epochs_run': len(epoch_losses)
        })
        
        # Save fold model
        model_path = Path("code/models")
        model_path.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), model_path / f"model_fold_{fold_idx+1}.pth")
        logger.info(f"Saved model for fold {fold_idx + 1}")
    
    # Aggregate results
    avg_mse = np.mean([r['final_mse'] for r in fold_results])
    avg_r2 = np.mean([r['final_r2'] for r in fold_results])
    mse_std = np.std([r['final_mse'] for r in fold_results])
    r2_std = np.std([r['final_r2'] for r in fold_results])
    
    return {
        'fold_results': fold_results,
        'avg_mse': avg_mse,
        'avg_r2': avg_r2,
        'mse_std': mse_std,
        'r2_std': r2_std
    }

def save_model(model: torch.nn.Module, path: Path) -> None:
    """Save model weights to disk."""
    torch.save(model.state_dict(), path)
    logger.info(f"Model saved to {path}")

def main(args) -> int:
    """
    Main entry point for training.
    
    Args:
        args: Namespace with metadata_file, n_folds, epochs, etc.
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load dataset
        logger.info("Loading dataset...")
        images, stiffness, metadata = load_dataset(Path(args.metadata_file))
        logger.info(f"Loaded {len(images)} samples")
        
        # Train model
        results = train_model(
            images=images,
            stiffness=stiffness,
            metadata=metadata,
            n_folds=args.n_folds,
            epochs=args.epochs,
            batch_size=args.batch_size,
            patience=args.patience,
            device=args.device
        )
        
        # Log results
        logger.info(f"Training complete. Avg MSE: {results['avg_mse']:.4f}, "
                    f"Avg R2: {results['avg_r2']:.4f}")
        
        # Save results
        results_path = Path("data/processed/training_results.json")
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        return 0
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train stiffness prediction model")
    parser.add_argument("--metadata_file", type=str, default="data/raw/metadata.json")
    parser.add_argument("--n_folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()
    exit(main(args))
