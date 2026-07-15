import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import torch
from huggingface_hub import snapshot_download, hf_hub_download
import safetensors.torch as sf
from state_manager import register_artifact, compute_sha256
import logging

logger = logging.getLogger(__name__)

def ensure_download_dir():
    """Ensure the download directory exists."""
    download_dir = Path("data/models")
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir

def download_base_model(model_name: str = "runwayml/stable-diffusion-v1-5"):
    """Download the base model from HuggingFace."""
    logger.info(f"Downloading base model: {model_name}")
    # In a real scenario, this would download the full model.
    # For this task, we assume the base model is available or handled elsewhere.
    return Path("data/models/base_model")

def download_lora_adapter(repo_id: str, filename: str):
    """Download a LoRA adapter from HuggingFace."""
    logger.info(f"Downloading LoRA adapter from {repo_id}/{filename}")
    local_path = hf_hub_download(repo_id=repo_id, filename=filename)
    return Path(local_path)

def get_collection_lora_adapter():
    """Get the CollectionLoRA adapter path."""
    # This is a placeholder for the actual adapter logic
    adapter_path = Path("data/models/adapter_fp16.safetensors")
    if not adapter_path.exists():
        # Assume it's downloaded by T007b logic
        raise FileNotFoundError(f"Adapter not found at {adapter_path}")
    return adapter_path

def load_adapter_weights(adapter_path: Path) -> Dict[str, torch.Tensor]:
    """Load LoRA adapter weights from a safetensors file."""
    logger.info(f"Loading adapter weights from {adapter_path}")
    weights = sf.load_file(adapter_path)
    return weights

def save_adapter_weights(weights: Dict[str, torch.Tensor], output_path: Path):
    """Save LoRA adapter weights to a safetensors file."""
    logger.info(f"Saving adapter weights to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.save_file(weights, str(output_path))

def register_downloaded_artifact(path: Path, artifact_type: str):
    """Register a downloaded artifact in the state manager."""
    sha256_hash = compute_sha256(path)
    register_artifact(str(path), sha256_hash, artifact_type)

def get_model_info(adapter_path: Path) -> Dict[str, Any]:
    """Get information about the model from the adapter."""
    weights = load_adapter_weights(adapter_path)
    return {
        "num_layers": len([k for k in weights.keys() if "lora" in k]),
        "total_params": sum(v.numel() for v in weights.values()),
    }

def compute_subspace_ranks(adapter_path: Path, tolerance: float = 1e-5) -> Dict[str, int]:
    """Compute the effective subspace rank for each LoRA weight matrix."""
    weights = load_adapter_weights(adapter_path)
    ranks = {}
    for name, tensor in weights.items():
        if "lora" in name:
            U, S, Vh = torch.svd(tensor)
            rank = (S > tolerance).sum().item()
            ranks[name] = int(rank)
    return ranks

def apply_quantization(adapter_path: Path, output_path: Path, bits: int = 8):
    """
    Apply zero-shot post-training quantization (FP16 -> INT8/INT4) on CPU.
    Uses torch.ao.quantization for the process.
    """
    logger.info(f"Applying {bits}-bit quantization to {adapter_path}")
    
    if not adapter_path.exists():
        raise FileNotFoundError(f"Input adapter not found: {adapter_path}")
    
    # Load original weights
    original_weights = sf.load_file(adapter_path)
    
    # Prepare quantized weights dictionary
    quantized_weights = {}
    
    # Quantization parameters
    if bits == 8:
        dtype = torch.qint8
        scale = 1.0 / 128.0
    elif bits == 4:
        dtype = torch.qint4
        # For 4-bit, we scale to 16 levels. 
        # Note: torch.qint4 is not directly supported in all versions, 
        # so we simulate it by quantizing to int8 and packing, or using float16 
        # with reduced precision if 4-bit quantization is not natively supported.
        # For this implementation, we will use a custom quantization approach for 4-bit
        # by mapping values to 16 levels.
        scale = 1.0 / 8.0
    else:
        raise ValueError(f"Unsupported bits: {bits}")
    
    for name, tensor in original_weights.items():
        if "lora" in name:
            # Move to CPU
            tensor_cpu = tensor.cpu()
            
            # Determine min/max for quantization
            tensor_min = tensor_cpu.min()
            tensor_max = tensor_cpu.max()
            
            # Scale and zero-point calculation
            qmin = -128 if bits == 8 else -8
            qmax = 127 if bits == 8 else 7
            
            if tensor_max == tensor_min:
                # Handle constant tensor
                quantized_tensor = torch.full_like(tensor_cpu, qmin, dtype=torch.int8)
            else:
                # Linear quantization
                scale = (tensor_max - tensor_min) / (qmax - qmin)
                zero_point = qmin - (tensor_min / scale)
                
                # Quantize
                quantized_tensor = torch.round((tensor_cpu / scale) + zero_point)
                quantized_tensor = torch.clamp(quantized_tensor, qmin, qmax)
                quantized_tensor = quantized_tensor.to(torch.int8)
            
            # Store as quantized tensor (we keep as int8 for simplicity, 
            # real 4-bit would require packing)
            quantized_weights[name] = quantized_tensor
        else:
            # Keep non-LoRA weights as is (or quantize if needed)
            quantized_weights[name] = tensor.cpu()
    
    # Save quantized weights
    save_adapter_weights(quantized_weights, output_path)
    
    # Register artifact
    register_downloaded_artifact(output_path, f"quantized_adapter_{bits}bit")
    
    logger.info(f"Quantized adapter saved to {output_path}")

def quantize_adapter_fp16_to_int8(input_path: Path, output_path: Path):
    """Convenience function for INT8 quantization."""
    apply_quantization(input_path, output_path, bits=8)

def quantize_adapter_fp16_to_int4(input_path: Path, output_path: Path):
    """Convenience function for INT4 quantization."""
    apply_quantization(input_path, output_path, bits=4)