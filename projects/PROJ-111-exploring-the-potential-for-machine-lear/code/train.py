import os
import sys
import time
import logging
import argparse
import json
import signal
import torch
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports based on API surface
from config import get_config, Config
from logging_config import setup_logging, get_logger
from vae_model import VAE, create_vae_model
from vae_data_loader import create_vae_dataloader, SpinDataset
from checkpoint_manager import save_checkpoint, compute_file_checksum, validate_checkpoint_metadata

# Constants
DEFAULT_TIME_BUDGET_HOURS = 6.0
CHECKPOINT_INTERVAL_EPOCHS = 5
PARTIAL_RESULT_FILENAME = "partial_training_results.json"
FINAL_RESULT_FILENAME = "training_results.json"

def setup_training_environment(config: Config) -> logging.Logger:
    """Initialize logging, device, and random seeds."""
    logger = setup_logging(config.log_level, config.log_file)
    
    # Set device
    if torch.cuda.is_available() and not config.cpu_only:
        device = torch.device("cuda")
        logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU device")
    
    # Set seeds for reproducibility
    torch.manual_seed(config.seed)
    if device.type == 'cuda':
        torch.cuda.manual_seed_all(config.seed)
    
    return logger, device

def compute_vae_loss(model: VAE, batch: torch.Tensor, device: torch.device) -> Dict[str, torch.Tensor]:
    """Compute VAE loss components: Reconstruction + KL Divergence."""
    batch = batch.to(device)
    mu, logvar, reconstructed = model(batch)
    
    # Reconstruction loss (MSE)
    recon_loss = torch.nn.functional.mse_loss(reconstructed, batch, reduction='sum')
    
    # KL Divergence loss
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    
    total_loss = recon_loss + kl_loss
    
    return {
        "total": total_loss,
        "reconstruction": recon_loss,
        "kl": kl_loss
    }

def train_epoch(model: VAE, dataloader, optimizer, device: torch.device, logger: logging.Logger, epoch: int) -> Dict[str, float]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    total_recon = 0.0
    total_kl = 0.0
    samples = 0
    
    for batch_idx, data in enumerate(dataloader):
        losses = compute_vae_loss(model, data, device)
        
        optimizer.zero_grad()
        losses["total"].backward()
        optimizer.step()
        
        batch_size = data.size(0)
        total_loss += losses["total"].item()
        total_recon += losses["reconstruction"].item()
        total_kl += losses["kl"].item()
        samples += batch_size
        
        if batch_idx % 100 == 0:
            logger.debug(f"Epoch {epoch} [{batch_idx}/{len(dataloader)}] Loss: {losses['total'].item()/batch_size:.4f}")

    return {
        "loss": total_loss / samples,
        "recon_loss": total_recon / samples,
        "kl_loss": total_kl / samples
    }

def validate_epoch(model: VAE, dataloader, device: torch.device) -> Dict[str, float]:
    """Validate for one epoch."""
    model.eval()
    total_loss = 0.0
    total_recon = 0.0
    total_kl = 0.0
    samples = 0
    
    with torch.no_grad():
        for data in dataloader:
            losses = compute_vae_loss(model, data, device)
            batch_size = data.size(0)
            total_loss += losses["total"].item()
            total_recon += losses["reconstruction"].item()
            total_kl += losses["kl"].item()
            samples += batch_size

    return {
        "loss": total_loss / samples,
        "recon_loss": total_recon / samples,
        "kl_loss": total_kl / samples
    }

def save_training_checkpoint(
    model: VAE, 
    optimizer, 
    epoch: int, 
    metrics: Dict[str, float], 
    config: Config, 
    logger: logging.Logger,
    is_final: bool = False
) -> str:
    """Save model and optimizer state with metadata."""
    checkpoint_dir = Path(config.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    state = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "metrics": metrics,
        "config": {
            "lr": config.lr,
            "batch_size": config.batch_size,
            "latent_dim": config.latent_dim,
            "seed": config.seed
        }
    }
    
    if is_final:
        path = checkpoint_dir / "best_model.pt"
        logger.info(f"Saving final model to {path}")
    else:
        path = checkpoint_dir / f"checkpoint_epoch_{epoch}.pt"
        logger.info(f"Saving checkpoint to {path}")
        
    torch.save(state, path)
    
    # Compute checksum for integrity
    checksum = compute_file_checksum(path)
    metadata_path = path.with_suffix(".meta.json")
    
    metadata = {
        "file": str(path),
        "checksum": checksum,
        "epoch": epoch,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
        
    validate_checkpoint_metadata(metadata)
    return str(path)

def load_checkpoint(checkpoint_path: str, model: VAE, optimizer, device: torch.device) -> Dict[str, Any]:
    """Load model and optimizer state from checkpoint."""
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint

def write_partial_results(
    config: Config,
    epoch: int,
    metrics: Dict[str, float],
    time_elapsed: float,
    reason: str,
    logger: logging.Logger
):
    """Write partial results to disk when time budget is exceeded."""
    results = {
        "status": "partial",
        "reason": reason,
        "time_budget_hours": DEFAULT_TIME_BUDGET_HOURS,
        "time_elapsed_hours": time_elapsed / 3600.0,
        "epochs_completed": epoch,
        "final_metrics": metrics,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path = Path(config.output_dir) / PARTIAL_RESULT_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.warning(f"Partial results written to {output_path} due to: {reason}")

def write_final_results(
    config: Config,
    epoch: int,
    metrics: Dict[str, float],
    time_elapsed: float,
    logger: logging.Logger
):
    """Write final training results to disk."""
    results = {
        "status": "completed",
        "time_budget_hours": DEFAULT_TIME_BUDGET_HOURS,
        "time_elapsed_hours": time_elapsed / 3600.0,
        "epochs_completed": epoch,
        "final_metrics": metrics,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path = Path(config.output_dir) / FINAL_RESULT_FILENAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Final results written to {output_path}")

def main():
    """Main training loop with time-budget enforcement (FR-004)."""
    config = get_config()
    logger, device = setup_training_environment(config)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Train VAE on spin configurations")
    parser.add_argument("--epochs", type=int, default=config.epochs, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=config.batch_size, help="Batch size")
    parser.add_argument("--lr", type=float, default=config.lr, help="Learning rate")
    parser.add_argument("--time-budget", type=float, default=DEFAULT_TIME_BUDGET_HOURS, help="Time budget in hours")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume")
    args = parser.parse_args()
    
    # Update config with args
    config.epochs = args.epochs
    config.batch_size = args.batch_size
    config.lr = args.lr
    
    time_budget_seconds = args.time_budget * 3600.0
    start_time = time.time()
    
    logger.info(f"Starting training with time budget: {args.time_budget} hours")
    logger.info(f"Data path: {config.data_dir}")
    logger.info(f"Output path: {config.output_dir}")
    
    # Initialize Model
    model = create_vae_model(
        input_dim=3, # 3 spin components
        hidden_dims=[32, 16], # Example dimensions, adjusted for LxL
        latent_dim=config.latent_dim
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=config.lr)
    
    start_epoch = 0
    if args.resume:
        logger.info(f"Resuming from checkpoint: {args.resume}")
        checkpoint = load_checkpoint(args.resume, model, optimizer, device)
        start_epoch = checkpoint["epoch"] + 1
        logger.info(f"Resumed from epoch {start_epoch}")
    
    # Setup Data Loaders
    # Note: Assuming processed data exists from T005/T014
    train_loader, val_loader = create_vae_dataloader(
        data_dir=config.data_dir,
        batch_size=config.batch_size,
        num_workers=config.num_workers,
        pin_memory=True
    )
    
    logger.info(f"Training set size: {len(train_loader.dataset)}")
    logger.info(f"Validation set size: {len(val_loader.dataset)}")
    
    best_val_loss = float('inf')
    patience_counter = 0
    early_stopping_patience = config.early_stopping_patience
    
    try:
        for epoch in range(start_epoch, config.epochs):
            # Check time budget BEFORE starting epoch
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            if elapsed_time > time_budget_seconds:
                logger.warning(f"Time budget exceeded at epoch {epoch}. Saving partial results.")
                # Train one last partial epoch if we have time, or just break
                # We break immediately to ensure we don't exceed budget further
                train_metrics = {"loss": 0, "recon_loss": 0, "kl_loss": 0} # Placeholder if we didn't run
                write_partial_results(config, epoch, train_metrics, elapsed_time, "Time budget exceeded", logger)
                break
            
            # Train Epoch
            train_metrics = train_epoch(model, train_loader, optimizer, device, logger, epoch)
            
            # Validate Epoch
            val_metrics = validate_epoch(model, val_loader, device)
            
            logger.info(
                f"Epoch {epoch} | Train Loss: {train_metrics['loss']:.4f} | "
                f"Val Loss: {val_metrics['loss']:.4f} | "
                f"Time: {elapsed_time/3600:.2f}h"
            )
            
            # Save checkpoint if best
            if val_metrics['loss'] < best_val_loss:
                best_val_loss = val_metrics['loss']
                save_training_checkpoint(
                    model, optimizer, epoch, val_metrics, config, logger, is_final=False
                )
                patience_counter = 0
            else:
                patience_counter += 1
            
            # Early stopping check
            if patience_counter >= early_stopping_patience:
                logger.info(f"Early stopping triggered at epoch {epoch}")
                write_final_results(config, epoch, val_metrics, time.time() - start_time, logger)
                save_training_checkpoint(model, optimizer, epoch, val_metrics, config, logger, is_final=True)
                return
            
            # Periodic checkpoint
            if (epoch + 1) % CHECKPOINT_INTERVAL_EPOCHS == 0:
                save_training_checkpoint(
                    model, optimizer, epoch, val_metrics, config, logger, is_final=False
                )
                
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user. Saving partial results.")
        write_partial_results(
            config, epoch, val_metrics, time.time() - start_time, "User interrupted", logger
        )
        
    else:
        # Normal completion
        final_metrics = validate_epoch(model, val_loader, device)
        write_final_results(config, epoch, final_metrics, time.time() - start_time, logger)
        save_training_checkpoint(model, optimizer, epoch, final_metrics, config, logger, is_final=True)
        logger.info("Training completed successfully.")

if __name__ == "__main__":
    main()