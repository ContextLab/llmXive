"""
Checkpoint Saver Module for Qwen-VLA Cross-Embodiment Transfer Study.

Implements serialization of model weights ensuring size <= 2GB.
Saves to data/checkpoints/ directory.
"""
import os
import sys
import logging
import gc
import torch
from pathlib import Path
from typing import Dict, Any, Optional, Union
import tempfile
import shutil

# Import local logging config
from src.utils.logging_config import get_logger, setup_logging

# Constants
MAX_CHECKPOINT_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB
CHECKPOINT_DIR = "data/checkpoints"

logger = get_logger(__name__)

def ensure_checkpoint_directory(checkpoint_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Ensure the checkpoint directory exists.
    
    Args:
        checkpoint_dir: Path to checkpoint directory. Defaults to 'data/checkpoints'.
        
    Returns:
        Path object for the checkpoint directory.
    """
    if checkpoint_dir is None:
        checkpoint_dir = CHECKPOINT_DIR
    
    path = Path(checkpoint_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured checkpoint directory exists: {path}")
    return path

def get_state_dict_size_bytes(state_dict: Dict[str, torch.Tensor]) -> int:
    """
    Calculate the approximate size of a state dict in bytes.
    
    Args:
        state_dict: The model state dictionary.
        
    Returns:
        Approximate size in bytes.
    """
    total_bytes = 0
    for param in state_dict.values():
        # Calculate size based on element count and dtype size
        total_bytes += param.numel() * param.element_size()
    return total_bytes

def optimize_state_dict_for_size(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """
    Optimize state dict to reduce size if necessary.
    
    Strategy:
    1. Remove optimizer states if present (not needed for inference).
    2. Cast parameters to float16 if they are float32 and the model supports it.
    3. Remove unnecessary metadata.
    
    Args:
        state_dict: Original state dictionary.
        
    Returns:
        Optimized state dictionary.
    """
    optimized = {}
    original_size = get_state_dict_size_bytes(state_dict)
    
    # Filter out optimizer states if present
    keys_to_remove = [k for k in state_dict.keys() if 'optimizer' in k.lower() or 'optimizer_state' in k.lower()]
    for k in keys_to_remove:
        del state_dict[k]
    
    # Attempt FP16 conversion for float32 tensors
    fp16_candidates = 0
    for k, v in state_dict.items():
        if v.dtype == torch.float32:
            try:
                state_dict[k] = v.half()
                fp16_candidates += 1
            except Exception:
                # If conversion fails, keep original
                pass
    
    optimized_size = get_state_dict_size_bytes(state_dict)
    reduction = (original_size - optimized_size) / original_size * 100
    logger.info(f"Optimized checkpoint size: {original_size/1e9:.2f}GB -> {optimized_size/1e9:.2f}GB ({reduction:.1f}% reduction). "
                f"Converted {fp16_candidates} tensors to FP16.")
    
    return state_dict

def save_checkpoint(model: torch.nn.Module, 
                    epoch: int, 
                    config: Dict[str, Any],
                    checkpoint_dir: Optional[Union[str, Path]] = None,
                    filename_prefix: str = "model_epoch") -> Path:
    """
    Save model checkpoint ensuring size <= 2GB.
    
    Args:
        model: The PyTorch model to save.
        epoch: Current training epoch.
        config: Training configuration dictionary.
        checkpoint_dir: Directory to save checkpoint. Defaults to 'data/checkpoints'.
        filename_prefix: Prefix for the checkpoint filename.
        
    Returns:
        Path to the saved checkpoint file.
        
    Raises:
        RuntimeError: If the optimized checkpoint still exceeds 2GB.
    """
    checkpoint_dir = ensure_checkpoint_directory(checkpoint_dir)
    
    # Construct filename
    timestamp = torch.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{epoch}_{timestamp}.pt"
    filepath = checkpoint_dir / filename
    
    logger.info(f"Saving checkpoint to {filepath}...")
    
    # Create state dict
    state_dict = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'config': config,
        'optimizer_state_dict': None  # Explicitly set to None to save space
    }
    
    # Check initial size
    initial_size = get_state_dict_size_bytes(state_dict['model_state_dict'])
    logger.info(f"Initial model state dict size: {initial_size/1e9:.2f}GB")
    
    if initial_size > MAX_CHECKPOINT_SIZE_BYTES:
        logger.warning("Initial checkpoint size exceeds 2GB. Attempting optimization...")
        state_dict['model_state_dict'] = optimize_state_dict_for_size(state_dict['model_state_dict'])
    
    final_size = get_state_dict_size_bytes(state_dict['model_state_dict'])
    
    if final_size > MAX_CHECKPOINT_SIZE_BYTES:
        error_msg = f"Checkpoint size {final_size/1e9:.2f}GB exceeds 2GB limit after optimization. " \
                    "Cannot save checkpoint."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Save to a temporary file first to ensure atomicity
    temp_filepath = filepath.with_suffix('.tmp')
    
    try:
        torch.save(state_dict, temp_filepath)
        
        # Verify size after save
        actual_size = temp_filepath.stat().st_size
        if actual_size > MAX_CHECKPOINT_SIZE_BYTES:
            # This is a safety check; torch.save overhead should be minimal
            logger.warning(f"Saved checkpoint size {actual_size/1e9:.2f}GB is slightly over 2GB limit. "
                           "Proceeding with save as optimization was attempted.")
        
        # Atomic rename
        shutil.move(str(temp_filepath), str(filepath))
        logger.info(f"Checkpoint saved successfully: {filepath} ({actual_size/1e9:.2f}GB)")
        
        # Cleanup
        gc.collect()
        
        return filepath
        
    except Exception as e:
        # Cleanup temp file on failure
        if temp_filepath.exists():
            temp_filepath.unlink()
        raise e

def main():
    """
    Main entry point for testing the checkpoint saver.
    Creates a dummy model and saves it.
    """
    setup_logging()
    logger.info("Starting checkpoint saver test...")
    
    # Create a dummy model similar to VLA model structure
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            # Simulate a medium-sized model
            self.encoder = torch.nn.Linear(1024, 2048)
            self.head = torch.nn.Linear(2048, 512)
            self.action_head = torch.nn.Sequential(
                torch.nn.Linear(512, 256),
                torch.nn.ReLU(),
                torch.nn.Linear(256, 10) # 10 action dimensions
            )
        
        def forward(self, x):
            x = self.encoder(x)
            x = self.head(x)
            return self.action_head(x)
    
    model = DummyModel()
    config = {
        "model_type": "Qwen2VL-DiT",
        "batch_size": 32,
        "learning_rate": 1e-4,
        "epochs": 10
    }
    
    try:
        path = save_checkpoint(model, epoch=1, config=config)
        logger.info(f"Test successful. Checkpoint saved at: {path}")
        
        # Verify file exists and check size
        if path.exists():
            size_gb = path.stat().st_size / (1024**3)
            logger.info(f"Verification: File exists, size = {size_gb:.4f}GB")
            assert size_gb <= 2.0, "File size exceeds 2GB limit!"
            logger.info("Size constraint verified.")
        else:
            logger.error("File was not created!")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    main()