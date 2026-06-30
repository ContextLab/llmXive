import os
import logging
import torch
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import asdict

from src.models.entities import ModelCheckpoint
from src.utils.resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)

MAX_CHECKPOINT_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB

def estimate_state_dict_size(state_dict: Dict[str, torch.Tensor]) -> int:
    """
    Estimate the size in bytes of a state dict if saved as a standard .pt file.
    This is a conservative estimate based on element count * dtype size.
    """
    total_bytes = 0
    for tensor in state_dict.values():
        # Element count * itemsize gives raw tensor size
        total_bytes += tensor.numel() * tensor.element_size()
        # Add overhead for dictionary keys and metadata (conservative)
        total_bytes += len(str(tensor.shape)) + 64
    return total_bytes

def compress_state_dict(
    state_dict: Dict[str, torch.Tensor],
    target_size_bytes: int = MAX_CHECKPOINT_SIZE_BYTES
) -> Tuple[Dict[str, torch.Tensor], bool]:
    """
    Attempt to compress the state dict to fit within target_size_bytes.
    Strategy:
    1. Remove optimizer states if present (not needed for inference/zero-shot eval).
    2. Convert float32 tensors to float16 if they are large enough to matter.
    3. Return the compressed dict and a boolean indicating if target was met.
    """
    compressed = {}
    is_compressed = False

    for key, tensor in state_dict.items():
        # Skip optimizer states if keys contain 'optimizer' or similar patterns
        # Standard practice: we only save model weights for inference
        if 'optimizer' in key.lower() or 'rng' in key.lower():
            logger.debug(f"Skipping {key} (optimizer/RNG state)")
            continue

        original_size = tensor.numel() * tensor.element_size()
        
        # If tensor is float32 and large, try to downcast to float16
        if tensor.dtype == torch.float32 and tensor.numel() > 10000:
            compressed_tensor = tensor.half()
            new_size = compressed_tensor.numel() * compressed_tensor.element_size()
            if new_size < original_size:
                compressed[key] = compressed_tensor
                is_compressed = True
                logger.debug(f"Downcast {key} from {tensor.dtype} to {compressed_tensor.dtype}")
            else:
                compressed[key] = tensor
        else:
            compressed[key] = tensor

    estimated_size = estimate_state_dict_size(compressed)
    if estimated_size <= target_size_bytes:
        return compressed, True
    
    # If still too big, we might need to warn, but usually removing optimizer states is enough
    # for a 2B model + DiT head.
    if estimated_size > target_size_bytes:
        logger.warning(f"Compressed checkpoint size ({estimated_size} bytes) exceeds target ({target_size_bytes}). "
                       f"Consider reducing model size or using quantization.")
    
    return compressed, estimated_size <= target_size_bytes

def save_checkpoint(
    model: torch.nn.Module,
    epoch: int,
    output_dir: str,
    metadata: Optional[Dict[str, Any]] = None,
    filename_prefix: str = "model_epoch"
) -> ModelCheckpoint:
    """
    Serialize model weights ensuring size ≤2GB and save to disk.
    
    Args:
        model: The PyTorch model to save.
        epoch: The current epoch number.
        output_dir: Directory to save the checkpoint.
        metadata: Optional dictionary of additional metadata (hyperparams, etc.).
        filename_prefix: Prefix for the filename.
        
    Returns:
        ModelCheckpoint entity with path and size info.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"{filename_prefix}_{epoch}.pt"
    full_path = output_path / filename

    # Extract state dict
    state_dict = model.state_dict()
    
    # Attempt compression
    compressed_state_dict, success = compress_state_dict(state_dict)
    
    # Save
    torch.save(compressed_state_dict, full_path)
    
    # Verify size
    file_size = full_path.stat().st_size
    if file_size > MAX_CHECKPOINT_SIZE_BYTES:
        logger.error(f"Checkpoint {full_path} exceeds 2GB limit ({file_size} bytes).")
        raise ValueError(f"Checkpoint size {file_size} exceeds limit {MAX_CHECKPOINT_SIZE_BYTES}")
    
    logger.info(f"Saved checkpoint to {full_path} (size: {file_size / (1024*1024):.2f} MB)")

    # Create entity
    checkpoint_entity = ModelCheckpoint(
        path=str(full_path),
        epoch=epoch,
        size_bytes=file_size,
        metadata=metadata or {},
        created_at=datetime.now(timezone.utc).isoformat()
    )

    return checkpoint_entity

from datetime import datetime, timezone