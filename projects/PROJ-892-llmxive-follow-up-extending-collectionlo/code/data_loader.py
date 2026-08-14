"""
Data loading and manipulation utilities for LoRA adapters.
Handles downloading, hashing, and quantization of model weights.
"""
import os
import shutil
import hashlib
import json
import logging
import re
import torch
import safetensors
from safetensors.torch import save_file, load_file
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from contextlib import contextmanager

from state_manager import compute_sha256, load_artifacts_state, save_artifacts_state

logger = logging.getLogger(__name__)

@contextmanager
def no_grad_context():
    """Context manager to disable gradient calculation."""
    with torch.no_grad():
        yield

def ensure_download_dir(dir_path: str) -> Path:
    """Ensure a directory exists."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_collection_lora_adapter() -> Path:
    """
    Download the CollectionLoRA adapter from HuggingFace.
    Returns the path to the downloaded adapter file.
    """
    # This is a placeholder for the actual download logic.
    # In a real implementation, this would use huggingface_hub.
    # For testing purposes, we assume the file exists or raise an error.
    raise NotImplementedError("HuggingFace download not implemented in this snippet.")

def download_base_model(model_id: str, cache_dir: Optional[str] = None) -> Path:
    """Download base model from HuggingFace."""
    # Placeholder for actual download logic
    raise NotImplementedError("Base model download not implemented in this snippet.")

def download_lora_adapter(repo_id: str, filename: str, local_dir: str) -> Path:
    """Download a specific LoRA adapter file."""
    # Placeholder for actual download logic
    raise NotImplementedError("LoRA adapter download not implemented in this snippet.")

def load_adapter_weights(path: Path) -> Dict[str, torch.Tensor]:
    """Load adapter weights from a safetensors file."""
    if not path.exists():
        raise FileNotFoundError(f"Adapter file not found: {path}")
    return load_file(str(path))

def save_adapter_weights(weights: Dict[str, torch.Tensor], path: Path) -> None:
    """Save adapter weights to a safetensors file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    save_file(weights, str(path))

def get_model_info(path: Path) -> Dict[str, Any]:
    """Get metadata from a safetensors file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with safetensors.safe_open(str(path), framework="pt", device="cpu") as f:
        return f.metadata()

def apply_quantization(state_dict: Dict[str, torch.Tensor], method: str) -> Dict[str, torch.Tensor]:
    """
    Apply quantization to a state dict.
    
    Args:
        state_dict: Dictionary of tensors to quantize.
        method: Quantization method ('int8' or 'int4').
        
    Returns:
        Quantized state dict.
        
    Raises:
        ValueError: If method is not supported.
    """
    if method not in ['int8', 'int4']:
        raise ValueError(f"Unsupported quantization method: {method}. Use 'int8' or 'int4'.")
    
    if method == 'int8':
        return quantize_adapter_fp16_to_int8(state_dict)
    elif method == 'int4':
        return quantize_adapter_fp16_to_int4(state_dict)

def quantize_adapter_fp16_to_int8(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """
    Quantize FP16 adapter weights to INT8.
    Uses simple linear quantization.
    """
    quantized_dict = {}
    for key, tensor in state_dict.items():
        if tensor.dtype == torch.float16 or tensor.dtype == torch.float32:
            # Simple linear quantization: scale to [-128, 127]
            # In a real scenario, one might use torch.ao.quantization or specific LoRA quantization methods
            min_val, max_val = tensor.min(), tensor.max()
            if max_val == min_val:
                # Avoid division by zero
                quantized = torch.zeros_like(tensor, dtype=torch.int8)
            else:
                # Scale to [-128, 127]
                scale = 255.0 / (max_val - min_val)
                zero_point = -128 - scale * min_val
                quantized = torch.clamp(torch.round(scale * tensor + zero_point), -128, 127).to(torch.int8)
            quantized_dict[key] = quantized
        else:
            # If already int8, just copy (or handle as needed)
            quantized_dict[key] = tensor
    return quantized_dict

def quantize_adapter_fp16_to_int4(state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """
    Quantize FP16 adapter weights to INT4.
    INT4 values are stored in int8 tensors with range [-8, 7].
    """
    quantized_dict = {}
    for key, tensor in state_dict.items():
        if tensor.dtype == torch.float16 or tensor.dtype == torch.float32:
            min_val, max_val = tensor.min(), tensor.max()
            if max_val == min_val:
                quantized = torch.zeros_like(tensor, dtype=torch.int8)
            else:
                # Scale to [-8, 7]
                scale = 15.0 / (max_val - min_val)
                zero_point = -8 - scale * min_val
                quantized = torch.clamp(torch.round(scale * tensor + zero_point), -8, 7).to(torch.int8)
            quantized_dict[key] = quantized
        else:
            quantized_dict[key] = tensor
    return quantized_dict

def compute_subspace_ranks(state_dict: Dict[str, torch.Tensor], tol: float = 1e-5) -> Dict[str, int]:
    """
    Compute subspace ranks for LoRA matrices using SVD.
    """
    ranks = {}
    for key, tensor in state_dict.items():
        if 'lora_A' in key or 'lora_B' in key:
            # Compute SVD
            U, S, Vh = torch.svd(tensor.float())
            # Count non-zero singular values
            rank = torch.sum(S > tol).item()
            ranks[key] = int(rank)
    return ranks

def load_and_compute_subspace_ranks(adapter_path: Path, tol: float = 1e-5) -> Dict[str, int]:
    """
    Load adapter and compute subspace ranks.
    """
    state_dict = load_adapter_weights(adapter_path)
    return compute_subspace_ranks(state_dict, tol)

def register_downloaded_artifact(
    artifacts_state: Dict[str, Any],
    artifact_name: str,
    artifact_path: Path,
    artifact_type: str = "model"
) -> Dict[str, Any]:
    """Register a downloaded artifact in the state file."""
    hash_val = compute_sha256(artifact_path)
    if "artifacts" not in artifacts_state:
        artifacts_state["artifacts"] = {}
    
    artifacts_state["artifacts"][artifact_name] = {
        "type": artifact_type,
        "path": str(artifact_path),
        "sha256": hash_val
    }
    return artifacts_state

# Placeholder functions for other required exports
def save_artifacts_state(state: Dict[str, Any], path: Path) -> None:
    """Save artifacts state to YAML."""
    import yaml
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(state, f)

def load_artifacts_state(path: Path) -> Dict[str, Any]:
    """Load artifacts state from YAML."""
    import yaml
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return compute_sha256(path) # Delegates to state_manager