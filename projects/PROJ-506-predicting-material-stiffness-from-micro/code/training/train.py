import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
import random

from code.training.model import StiffnessPredictorCNN, create_model
from code.training.kfold_utils import (
    load_dataset_metadata,
    create_stratification_bins,
    create_combined_stratification,
    stratified_k_fold_split,
    get_fold_sizes
)
from code.utils.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(metadata_path: Path) -> Tuple[torch.Tensor, torch.Tensor, List[Dict]]:
    """
    Load dataset from metadata JSON file.
    
    Args:
        metadata_path: Path to the metadata JSON file
        
    Returns:
        Tuple of (images tensor, stiffness tensors, metadata list)
    """
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    images = []
    stiffnesses = []
    
    for entry in metadata:
        # Load image (assuming PNG format)
        img_path = Path(entry['image_path'])
        if not img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            continue
        
        # Load image using numpy (skimage.io is available in project)
        from skimage import io
        img = io.imread(img_path)
        # Normalize to [0, 1] if needed
        if img.max() > 1.0:
            img = img / 255.0
        # Ensure 3D tensor (H, W, C) - convert grayscale to single channel
        if img.ndim == 2:
            img = img.reshape(1, img.shape[0], img.shape[1])
        elif img.ndim == 3 and img.shape[2] == 1:
            img = img.reshape(1, img.shape[0], img.shape[1])
        elif img.ndim == 3:
            # Assume RGB, convert to grayscale
            img = np.mean(img, axis=2)
            img = img.reshape(1, img.shape[0], img.shape[1])
        
        images.append(img)
        stiffnesses.append(entry['stiffness_tensor'])
    
    images = np.array(images, dtype=np.float32)
    stiffnesses = np.array(stiffnesses, dtype=np.float32)
    
    # Convert to tensors
    images_tensor = torch.from_numpy(images)
    stiffness_tensor = torch.from_numpy(stiffnesses)
    
    return images_tensor, stiffness_tensor, metadata

def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device
) -> float:
    """
    Train for one epoch.
    
    Returns:
        Average training loss for the epoch
    """
    model.train()
    total_loss = 0.0
    num_batches = 0
    
    for batch_images, batch_stiffness in dataloader:
        batch_images = batch_images.to(device)
        batch_stiffness = batch_stiffness.to(device)
        
        optimizer.zero_grad()
        predictions = model(batch_images)
        loss = criterion(predictions, batch_stiffness)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / num_batches if num_batches > 0 else 0.0

def validate_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, Dict[str, float]]:
    """
    Validate for one epoch.
    
    Returns:
        Tuple of (average validation loss, metrics dict)
    """
    model.eval()
    total_loss = 0.0
    num_batches = 0
    all_predictions = []
    all_targets = []
    
    with torch.no_grad():
        for batch_images, batch_stiffness in dataloader:
            batch_images = batch_images.to(device)
            batch_stiffness = batch_stiffness.to(device)
            
            predictions = model(batch_images)
            loss = criterion(predictions, batch_stiffness)
            
            total_loss += loss.item()
            num_batches += 1
            
            all_predictions.extend(predictions.cpu().numpy())
            all_targets.extend(batch_stiffness.cpu().numpy())
    
    avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
    
    # Calculate metrics
    predictions = np.array(all_predictions)
    targets = np.array(all_targets)
    
    metrics = {
        'mae': mean_absolute_error(targets, predictions),
        'mse': mean_squared_error(targets, predictions),
        'r2': r2_score(targets, predictions)
    }
    
    return avg_loss, metrics

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    num_epochs: int,
    early_stopping_patience: int = 10,
    checkpoint_path: Optional[Path] = None
) -> Dict[str, List[float]]:
    """
    Train the model with early stopping and checkpointing.
    
    Args:
        model: The model to train
        train_loader: Training data loader
        val_loader: Validation data loader
        criterion: Loss function
        optimizer: Optimizer
        device: Device to train on
        num_epochs: Maximum number of epochs
        early_stopping_patience: Number of epochs to wait before early stopping
        checkpoint_path: Path to save model checkpoints
        
    Returns:
        Dictionary of training history
    """
    history = {
        'train_loss': [],
        'val_loss': [],
        'val_mae': [],
        'val_mse': [],
        'val_r2': []
    }
    
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    for epoch in range(num_epochs):
        # Training
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Validation
        val_loss, val_metrics = validate_epoch(model, val_loader, criterion, device)
        
        # Log progress
        logger.info(f"Epoch {epoch+1}/{num_epochs} - "
                   f"Train Loss: {train_loss:.6f}, "
                   f"Val Loss: {val_loss:.6f}, "
                   f"Val MAE: {val_metrics['mae']:.6f}, "
                   f"Val R2: {val_metrics['r2']:.6f}")
        
        # Record history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_mae'].append(val_metrics['mae'])
        history['val_mse'].append(val_metrics['mse'])
        history['val_r2'].append(val_metrics['r2'])
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
            
            # Save checkpoint if path provided
            if checkpoint_path:
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': best_model_state,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': val_loss,
                    'metrics': val_metrics
                }, checkpoint_path)
                logger.info(f"Checkpoint saved to {checkpoint_path}")
        else:
            patience_counter += 1
            if patience_counter >= early_stopping_patience:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break
    
    # Restore best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    return history

def save_model(
    model: nn.Module,
    optimizer: optim.Optimizer,
    history: Dict,
    fold: int,
    output_dir: Path
):
    """
    Save model and training history.
    
    Args:
        model: Trained model
        optimizer: Optimizer state
        history: Training history
        fold: Fold number
        output_dir: Directory to save to
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / f"model_fold_{fold}.pth"
    history_path = output_dir / f"history_fold_{fold}.json"
    
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict()
    }, model_path)
    
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    logger.info(f"Model saved to {model_path}")
    logger.info(f"History saved to {history_path}")

def main():
    """
    Main training function with stratified k-fold cross-validation.
    
    This implementation:
    1. Loads dataset metadata
    2. Creates stratification bins based on inclusion_density, topology_type,
       shape_factor, and connectivity (as defined in T012 and T017b)
    3. Performs stratified k-fold split
    4. Trains the model on each fold
    5. Saves model artifacts and reports metrics
    """
    # Configuration
    device = torch.device('cpu')  # CPU-optimized as per requirements
    num_folds = 5
    batch_size = 32
    num_epochs = 50  # Sufficient for convergence, can be adjusted
    early_stopping_patience = 10
    learning_rate = 0.001
    metadata_path = Path('data/processed/derivation_log.json')
    output_dir = Path('code/models')
    
    # Set random seeds for reproducibility
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)
    
    logger.info("Loading dataset metadata...")
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        logger.error("Please run the data generation pipeline first (code/main.py)")
        return
    
    images, stiffnesses, metadata = load_dataset(metadata_path)
    logger.info(f"Loaded {len(images)} samples")
    
    if len(images) == 0:
        logger.error("No valid images loaded. Check metadata and image paths.")
        return
    
    # Create stratification bins
    logger.info("Creating stratification bins...")
    stratification_data = []
    
    for i, entry in enumerate(metadata):
        # Extract features for stratification
        inclusion_density = entry.get('inclusion_density', 0.0)
        topology_type = entry.get('topology_type', 'unknown')
        shape_factor = entry.get('shape_factor', 0.0)
        connectivity = entry.get('connectivity', 0.0)
        
        # Create bins for continuous variables
        # Density bins: 0-0.1, 0.1-0.2, ..., 0.9-1.0
        density_bin = int(inclusion_density * 10)
        
        # Shape factor bins: 0-0.25, 0.25-0.5, 0.5-0.75, 0.75-1.0
        shape_bin = int(shape_factor * 4)
        
        # Connectivity bins: 0-0.25, 0.25-0.5, 0.5-0.75, 0.75-1.0
        conn_bin = int(connectivity * 4)
        
        stratification_data.append({
            'index': i,
            'density_bin': density_bin,
            'topology_type': topology_type,
            'shape_bin': shape_bin,
            'conn_bin': conn_bin
        })
    
    # Create combined stratification labels
    combined_strat_labels = create_combined_stratification(stratification_data)
    logger.info(f"Created {len(set(combined_strat_labels))} unique stratification groups")
    
    # Perform stratified k-fold split
    logger.info(f"Performing {num_folds}-fold stratified cross-validation...")
    fold_indices = list(stratified_k_fold_split(
        len(images),
        combined_strat_labels,
        n_splits=num_folds
    ))
    
    fold_results = []
    
    for fold_idx, (train_idx, val_idx) in enumerate(fold_indices):
        logger.info(f"\n{'='*60}")
        logger.info(f"Fold {fold_idx + 1}/{num_folds}")
        logger.info(f"{'='*60}")
        
        # Split data
        train_images = images[train_idx]
        train_stiffness = stiffnesses[train_idx]
        val_images = images[val_idx]
        val_stiffness = stiffnesses[val_idx]
        
        logger.info(f"Train size: {len(train_idx)}, Validation size: {len(val_idx)}")
        
        # Create data loaders
        train_dataset = TensorDataset(
            torch.from_numpy(train_images),
            torch.from_numpy(train_stiffness)
        )
        val_dataset = TensorDataset(
            torch.from_numpy(val_images),
            torch.from_numpy(val_stiffness)
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0
        )
        
        # Initialize model
        model = create_model().to(device)
        
        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # Train model
        logger.info(f"Training fold {fold_idx + 1}...")
        history = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            num_epochs=num_epochs,
            early_stopping_patience=early_stopping_patience,
            checkpoint_path=output_dir / f"checkpoint_fold_{fold_idx}.pth"
        )
        
        # Save model
        save_model(
            model=model,
            optimizer=optimizer,
            history=history,
            fold=fold_idx,
            output_dir=output_dir
        )
        
        # Record fold results
        fold_results.append({
            'fold': fold_idx,
            'train_size': len(train_idx),
            'val_size': len(val_idx),
            'final_train_loss': history['train_loss'][-1],
            'final_val_loss': history['val_loss'][-1],
            'final_val_mae': history['val_mae'][-1],
            'final_val_mse': history['val_mse'][-1],
            'final_val_r2': history['val_r2'][-1],
            'best_val_loss': min(history['val_loss']),
            'epochs_trained': len(history['train_loss'])
        })
        
        logger.info(f"Fold {fold_idx + 1} completed - "
                   f"Final Val MAE: {history['val_mae'][-1]:.6f}, "
                   f"Final Val R2: {history['val_r2'][-1]:.6f}")
    
    # Aggregate results
    logger.info(f"\n{'='*60}")
    logger.info("Cross-Validation Results Summary")
    logger.info(f"{'='*60}")
    
    avg_mae = np.mean([r['final_val_mae'] for r in fold_results])
    avg_mse = np.mean([r['final_val_mse'] for r in fold_results])
    avg_r2 = np.mean([r['final_val_r2'] for r in fold_results])
    std_mae = np.std([r['final_val_mae'] for r in fold_results])
    std_mse = np.std([r['final_val_mse'] for r in fold_results])
    std_r2 = np.std([r['final_val_r2'] for r in fold_results])
    
    logger.info(f"Average MAE: {avg_mae:.6f} (+/- {std_mae:.6f})")
    logger.info(f"Average MSE: {avg_mse:.6f} (+/- {std_mse:.6f})")
    logger.info(f"Average R2:  {avg_r2:.6f} (+/- {std_r2:.6f})")
    
    # Save summary
    summary_path = output_dir / "cv_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            'num_folds': num_folds,
            'fold_results': fold_results,
            'aggregate_metrics': {
                'mean_mae': float(avg_mae),
                'std_mae': float(std_mae),
                'mean_mse': float(avg_mse),
                'std_mse': float(std_mse),
                'mean_r2': float(avg_r2),
                'std_r2': float(std_r2)
            }
        }, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")
    logger.info("Training complete!")

if __name__ == "__main__":
    main()