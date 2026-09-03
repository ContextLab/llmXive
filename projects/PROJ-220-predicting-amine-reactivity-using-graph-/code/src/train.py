import os
import sys
import time
import json
import signal
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

import torch
import torch.nn.functional as F
from torch_geometric.data import DataLoader

# Import existing project modules
from src.data.streaming_loader import load_batch
from src.models.gnn import HeterophilyGAT
from src.models.baseline import train_baseline_models, evaluate_model
from src.utils.memory_monitor import check_limits, graceful_exit, enforce_limits
from src.utils.sampling import sample_dataset
from src.data.split import scaffold_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_TRAINING_HOURS = 5.5
TIMEOUT_SECONDS = MAX_TRAINING_HOURS * 3600
CHECKPOINT_INTERVAL_EPOCHS = 10
MEMORY_THRESHOLD_MB = 6500

class TrainingTimeoutError(Exception):
    """Raised when training exceeds the allocated time limit."""
    pass

class CheckpointSaver:
    """Manages saving and loading training checkpoints."""
    
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, epoch: int, model: torch.nn.Module, optimizer: torch.optim.Optimizer,
             loss_history: list, reason: str = "checkpoint"):
        """Save training state to disk."""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}.pt"
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss_history': loss_history,
            'timestamp': datetime.now().isoformat(),
            'reason': reason
        }, checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path} (Reason: {reason})")
    
    def load_latest(self) -> Optional[Dict[str, Any]]:
        """Load the most recent checkpoint if it exists."""
        checkpoints = list(self.checkpoint_dir.glob("checkpoint_epoch_*.pt"))
        if not checkpoints:
            return None
        
        latest_checkpoint = max(checkpoints, key=lambda p: p.stat().st_mtime)
        logger.info(f"Loading checkpoint: {latest_checkpoint}")
        return torch.load(latest_checkpoint)

def estimate_time_remaining(
    start_time: float,
    current_epoch: int,
    total_epochs: int
) -> float:
    """
    Estimate remaining training time based on elapsed time and progress.
    
    Args:
        start_time: Unix timestamp when training started
        current_epoch: Current epoch index (0-indexed)
        total_epochs: Total planned epochs
    
    Returns:
        Estimated remaining time in seconds
    """
    elapsed = time.time() - start_time
    if current_epoch == 0:
        return float('inf')
    
    time_per_epoch = elapsed / (current_epoch + 1)
    remaining_epochs = total_epochs - current_epoch - 1
    return time_per_epoch * remaining_epochs

def train_with_timeout(
    model: torch.nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    total_epochs: int,
    device: str,
    checkpoint_dir: str = "artifacts/checkpoints"
) -> Tuple[torch.nn.Module, Dict[str, Any]]:
    """
    Train model with timeout enforcement and checkpointing.
    
    Interrupts training if estimated time remaining exceeds 5.5 hours,
    saves a checkpoint, and logs the reason for early exit.
    
    Args:
        model: The GNN model to train
        train_loader: DataLoader for training data
        val_loader: DataLoader for validation data
        optimizer: Optimizer for the model
        total_epochs: Maximum number of epochs to train
        device: Device to train on ('cpu' or 'cuda')
        checkpoint_dir: Directory to save checkpoints
    
    Returns:
        Tuple of (trained model, training metrics dict)
    """
    start_time = time.time()
    checkpoint_saver = CheckpointSaver(checkpoint_dir)
    
    loss_history = []
    best_val_loss = float('inf')
    best_model_state = None
    
    # Try to resume from checkpoint if available
    checkpoint = checkpoint_saver.load_latest()
    start_epoch = 0
    if checkpoint:
        start_epoch = checkpoint['epoch'] + 1
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        loss_history = checkpoint.get('loss_history', [])
        logger.info(f"Resuming from epoch {start_epoch}")
    
    try:
        for epoch in range(start_epoch, total_epochs):
            # Memory check
            if not check_limits(MEMORY_THRESHOLD_MB):
                logger.warning("Memory limit exceeded, triggering graceful exit")
                checkpoint_saver.save(epoch, model, optimizer, loss_history, "memory_limit")
                graceful_exit()
            
            # Train one epoch
            model.train()
            epoch_loss = 0.0
            num_batches = 0
            
            for batch in train_loader:
                batch = batch.to(device)
                optimizer.zero_grad()
                
                # Forward pass
                out = model(batch.x, batch.edge_index, batch.edge_type)
                loss = F.mse_loss(out, batch.y)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                num_batches += 1
            
            avg_loss = epoch_loss / max(num_batches, 1)
            loss_history.append(avg_loss)
            
            # Validation
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch in val_loader:
                    batch = batch.to(device)
                    out = model(batch.x, batch.edge_index, batch.edge_type)
                    val_loss += F.mse_loss(out, batch.y).item()
            
            val_loss /= max(len(val_loader), 1)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_model_state = model.state_dict().copy()
            
            logger.info(
                f"Epoch {epoch+1}/{total_epochs} - "
                f"Train Loss: {avg_loss:.4f}, Val Loss: {val_loss:.4f}"
            )
            
            # Save checkpoint at intervals
            if (epoch + 1) % CHECKPOINT_INTERVAL_EPOCHS == 0:
                checkpoint_saver.save(epoch, model, optimizer, loss_history, "interval")
            
            # Timeout check
            remaining = estimate_time_remaining(start_time, epoch, total_epochs)
            if remaining > TIMEOUT_SECONDS:
                logger.warning(
                    f"Estimated remaining time ({remaining/3600:.2f}h) exceeds "
                    f"limit ({MAX_TRAINING_HOURS}h). Saving checkpoint and exiting."
                )
                checkpoint_saver.save(
                    epoch, model, optimizer, loss_history, 
                    f"timeout_exceeded: {remaining/3600:.2f}h remaining"
                )
                raise TrainingTimeoutError(
                    f"Training interrupted: estimated time remaining "
                    f"({remaining/3600:.2f}h) exceeds limit ({MAX_TRAINING_HOURS}h)"
                )
    
    except TrainingTimeoutError as e:
        logger.error(str(e))
        # Return current best model state
        if best_model_state:
            model.load_state_dict(best_model_state)
        return model, {
            'epochs_completed': epoch + 1,
            'total_epochs_planned': total_epochs,
            'early_exit_reason': 'timeout',
            'final_train_loss': loss_history[-1] if loss_history else None,
            'best_val_loss': best_val_loss,
            'duration_seconds': time.time() - start_time
        }
    
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user")
        checkpoint_saver.save(epoch, model, optimizer, loss_history, "user_interrupt")
        return model, {
            'epochs_completed': epoch + 1,
            'total_epochs_planned': total_epochs,
            'early_exit_reason': 'user_interrupt',
            'final_train_loss': loss_history[-1] if loss_history else None,
            'best_val_loss': best_val_loss,
            'duration_seconds': time.time() - start_time
        }
    
    duration = time.time() - start_time
    return model, {
        'epochs_completed': total_epochs,
        'total_epochs_planned': total_epochs,
        'early_exit_reason': None,
        'final_train_loss': loss_history[-1] if loss_history else None,
        'best_val_loss': best_val_loss,
        'duration_seconds': duration
    }

def main():
    """Main training entry point with timeout enforcement."""
    parser = argparse.ArgumentParser(description="Train GNN model with timeout enforcement")
    parser.add_argument('--data_dir', type=str, default='data/processed',
                      help='Directory containing processed graph data')
    parser.add_argument('--epochs', type=int, default=100,
                      help='Maximum number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32,
                      help='Batch size for training')
    parser.add_argument('--lr', type=float, default=0.001,
                      help='Learning rate')
    parser.add_argument('--checkpoint_dir', type=str, default='artifacts/checkpoints',
                      help='Directory to save checkpoints')
    parser.add_argument('--device', type=str, default='cpu',
                      help='Device to train on (cpu or cuda)')
    args = parser.parse_args()
    
    logger.info(f"Starting training with timeout limit of {MAX_TRAINING_HOURS} hours")
    logger.info(f"Configuration: epochs={args.epochs}, batch_size={args.batch_size}, lr={args.lr}")
    
    # Load data using streaming loader
    logger.info("Loading data with streaming loader...")
    # Note: In production, this would use the actual streaming loader
    # For now, we assume data is available in the expected format
    try:
        train_data, val_data, test_data = scaffold_split(
            Path(args.data_dir),
            test_size=0.2,
            val_size=0.1
        )
    except FileNotFoundError as e:
        logger.error(f"Data directory not found: {e}")
        sys.exit(1)
    
    # Create data loaders
    train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=args.batch_size)
    test_loader = DataLoader(test_data, batch_size=args.batch_size)
    
    # Initialize model
    device = args.device
    model = HeterophilyGAT().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    
    # Train with timeout
    trained_model, train_metrics = train_with_timeout(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        optimizer=optimizer,
        total_epochs=args.epochs,
        device=device,
        checkpoint_dir=args.checkpoint_dir
    )
    
    # Evaluate baseline models
    logger.info("Training baseline models...")
    baseline_metrics = train_baseline_models(train_data, val_data, test_data)
    
    # Evaluate GNN
    logger.info("Evaluating GNN model...")
    gnn_metrics = evaluate_model(trained_model, test_loader, device)
    
    # Compile final metrics
    final_metrics = {
        'training': train_metrics,
        'baseline': baseline_metrics,
        'gnn': gnn_metrics,
        'timeout_config': {
            'max_hours': MAX_TRAINING_HOURS,
            'timeout_seconds': TIMEOUT_SECONDS
        }
    }
    
    # Save metrics
    metrics_path = Path('data/derived/training_metrics.json')
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(final_metrics, f, indent=2, default=str)
    
    logger.info(f"Training complete. Metrics saved to {metrics_path}")
    logger.info(f"Final metrics: {json.dumps(final_metrics, indent=2, default=str)}")
    
    return final_metrics

if __name__ == '__main__':
    main()