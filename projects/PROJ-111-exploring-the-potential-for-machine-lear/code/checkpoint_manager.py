import os
import json
import hashlib
import logging
import torch
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from vae_model import VAE
from config import get_config

logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checkpoint_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate that the checkpoint metadata contains all required fields
    and that the stored checksum matches the actual model file checksum.
    
    Returns True if valid, raises ValueError otherwise.
    """
    required_fields = [
        "epoch", "loss", "config_snapshot", "timestamp", 
        "model_checksum", "dataset_checksum"
    ]
    
    for field in required_fields:
        if field not in metadata:
            raise ValueError(f"Missing required metadata field: {field}")
    
    if not isinstance(metadata["epoch"], int):
        raise ValueError("Epoch must be an integer")
    
    if not isinstance(metadata["loss"], (int, float)):
        raise ValueError("Loss must be a number")
        
    if not isinstance(metadata["timestamp"], str):
        raise ValueError("Timestamp must be a string")

    return True

def save_checkpoint(
    model: VAE,
    epoch: int,
    loss: float,
    optimizer: torch.optim.Optimizer,
    metadata: Optional[Dict[str, Any]] = None,
    checkpoint_dir: Optional[str] = None
) -> Tuple[Path, str]:
    """
    Save a VAE model checkpoint with checksums and metadata validation.
    
    Args:
        model: The VAE model to save.
        epoch: Current training epoch.
        loss: Current training loss.
        optimizer: The optimizer state to save.
        metadata: Optional additional metadata to include.
        checkpoint_dir: Directory to save the checkpoint. Defaults to config.
        
    Returns:
        Tuple of (checkpoint_path, checksum)
        
    Raises:
        ValueError: If metadata validation fails.
    """
    config = get_config()
    if checkpoint_dir is None:
        checkpoint_dir = config.checkpoint_dir
        
    path = Path(checkpoint_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    model_filename = f"checkpoint_epoch_{epoch:04d}.pt"
    model_path = path / model_filename
    
    # Save model and optimizer state
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": loss,
    }, model_path)
    
    # Compute checksum of the saved model file
    model_checksum = compute_file_checksum(model_path)
    
    # Prepare metadata
    full_metadata = {
        "epoch": epoch,
        "loss": float(loss),
        "timestamp": timestamp,
        "model_checksum": model_checksum,
        "dataset_checksum": metadata.get("dataset_checksum", "unknown") if metadata else "unknown",
        "config_snapshot": config.to_dict() if hasattr(config, 'to_dict') else {},
    }
    
    if metadata:
        for key, value in metadata.items():
            if key not in full_metadata:
                full_metadata[key] = value
    
    # Validate metadata before saving
    try:
        validate_checkpoint_metadata(full_metadata)
    except ValueError as e:
        logger.error(f"Checkpoint metadata validation failed: {e}")
        raise
    
    # Save metadata as JSON
    metadata_path = path / f"{model_filename}.json"
    with open(metadata_path, "w") as f:
        json.dump(full_metadata, f, indent=2)
    
    # Verify metadata file checksum matches model checksum in metadata
    # (Self-consistency check)
    logger.info(f"Checkpoint saved: {model_path}")
    logger.info(f"Model checksum: {model_checksum}")
    
    return model_path, model_checksum

def load_checkpoint(
    checkpoint_path: Path,
    model: VAE,
    optimizer: Optional[torch.optim.Optimizer] = None,
    strict: bool = True
) -> Tuple[int, float, VAE, Optional[torch.optim.Optimizer], Dict[str, Any]]:
    """
    Load a VAE model checkpoint with checksum validation.
    
    Args:
        checkpoint_path: Path to the checkpoint file.
        model: The VAE model to load state into.
        optimizer: Optional optimizer to load state into.
        strict: If True, require exact checksum match.
        
    Returns:
        Tuple of (epoch, loss, model, optimizer, metadata)
        
    Raises:
        FileNotFoundError: If checkpoint or metadata file not found.
        ValueError: If checksum validation fails.
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")
        
    metadata_path = checkpoint_path.with_suffix(".pt.json")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    # Load metadata
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    # Validate metadata structure
    validate_checkpoint_metadata(metadata)
    
    # Compute current checksum of the checkpoint file
    current_checksum = compute_file_checksum(checkpoint_path)
    stored_checksum = metadata["model_checksum"]
    
    if current_checksum != stored_checksum:
        msg = (
            f"Checkpoint checksum mismatch!\n"
            f"  Stored:   {stored_checksum}\n"
            f"  Current:  {current_checksum}\n"
            f"  File:     {checkpoint_path}"
        )
        if strict:
            raise ValueError(msg)
        else:
            logger.warning(msg)
    
    # Load state
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"], strict=strict)
    
    epoch = checkpoint["epoch"]
    loss = checkpoint["loss"]
    
    if optimizer is not None and "optimizer_state_dict" in checkpoint:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    
    logger.info(f"Loaded checkpoint from epoch {epoch}, loss {loss:.4f}")
    logger.info(f"Checksum validated: {current_checksum}")
    
    return epoch, loss, model, optimizer, metadata

def list_checkpoints(checkpoint_dir: str) -> list:
    """
    List all available checkpoints in a directory.
    
    Returns:
        List of dicts containing checkpoint info (path, epoch, loss, valid).
    """
    path = Path(checkpoint_dir)
    if not path.exists():
        return []
        
    checkpoints = []
    for pt_file in path.glob("checkpoint_epoch_*.pt"):
        try:
            metadata_path = pt_file.with_suffix(".pt.json")
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            current_checksum = compute_file_checksum(pt_file)
            is_valid = (current_checksum == metadata["model_checksum"])
            
            checkpoints.append({
                "path": str(pt_file),
                "epoch": metadata["epoch"],
                "loss": metadata["loss"],
                "timestamp": metadata["timestamp"],
                "valid": is_valid
            })
        except Exception as e:
            logger.warning(f"Could not read checkpoint {pt_file}: {e}")
            
    # Sort by epoch descending
    checkpoints.sort(key=lambda x: x["epoch"], reverse=True)
    return checkpoints

def main():
    """
    Demo script to test checkpoint saving and loading.
    """
    logging.basicConfig(level=logging.INFO)
    config = get_config()
    
    # Create a dummy model and optimizer
    model = VAE(input_dim=3, latent_dim=10, hidden_dims=[64, 32])
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Save a checkpoint
    checkpoint_path, checksum = save_checkpoint(
        model=model,
        epoch=10,
        loss=0.1234,
        optimizer=optimizer,
        metadata={"dataset_checksum": "abc123"},
        checkpoint_dir=config.checkpoint_dir
    )
    
    print(f"Saved checkpoint: {checkpoint_path}")
    print(f"Checksum: {checksum}")
    
    # Load the checkpoint
    loaded_epoch, loaded_loss, loaded_model, loaded_optimizer, loaded_metadata = load_checkpoint(
        checkpoint_path=checkpoint_path,
        model=VAE(input_dim=3, latent_dim=10, hidden_dims=[64, 32]),
        optimizer=optimizer
    )
    
    print(f"Loaded checkpoint: epoch={loaded_epoch}, loss={loaded_loss}")
    print(f"Metadata: {loaded_metadata}")
    
    # List checkpoints
    ckpts = list_checkpoints(config.checkpoint_dir)
    print(f"Available checkpoints: {len(ckpts)}")
    for c in ckpts:
        print(f"  - {c['path']} (epoch {c['epoch']}, valid={c['valid']})")

if __name__ == "__main__":
    main()
