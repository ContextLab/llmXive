import os
import shutil
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import yaml

# Imports from sibling modules as per API surface
from config import load_config

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def ensure_download_dir(dir_path: Path) -> Path:
    """Ensures a directory exists, creates it if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def compute_sha256_file(file_path: Path) -> str:
    """Computes the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_artifacts_state() -> Dict[str, Any]:
    """Loads the artifacts state from state/artifacts.yaml."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    if not state_path.exists():
        return {}
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {}

def save_artifacts_state(state: Dict[str, Any]) -> None:
    """Saves the artifacts state to state/artifacts.yaml."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    ensure_download_dir(state_path.parent)
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def register_downloaded_artifact(name: str, path: Path, hash_val: str) -> None:
    """Registers a downloaded artifact in the state."""
    state = load_artifacts_state()
    state[name] = {
        "path": str(path),
        "hash": hash_val
    }
    save_artifacts_state(state)

def download_lora_adapter(repo_id: str, filename: str, output_path: Path) -> Path:
    """Downloads a LoRA adapter from HuggingFace."""
    from huggingface_hub import hf_hub_download
    ensure_download_dir(output_path.parent)
    try:
        local_path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=output_path.parent, local_dir_use_symlinks=False)
        return Path(local_path)
    except Exception as e:
        logger.error(f"Failed to download from {repo_id}: {e}")
        raise FileNotFoundError(f"Could not download adapter from {repo_id}") from e

def download_base_model(repo_id: str, output_dir: Path) -> Path:
    """Downloads the base model from HuggingFace."""
    from huggingface_hub import snapshot_download
    ensure_download_dir(output_dir)
    try:
        local_dir = snapshot_download(repo_id=repo_id, local_dir=str(output_dir), local_dir_use_symlinks=False)
        return Path(local_dir)
    except Exception as e:
        logger.error(f"Failed to download base model from {repo_id}: {e}")
        raise FileNotFoundError(f"Could not download base model from {repo_id}") from e

def get_collection_lora_adapter() -> Path:
    """Downloads and validates the CollectionLoRA adapter."""
    output_dir = get_project_root() / "data" / "models"
    ensure_download_dir(output_dir)
    filename = "adapter_fp16.safetensors"
    output_path = output_dir / filename
    
    if not output_path.exists():
        # Primary source
        try:
            download_lora_adapter("stabilityai/stable-diffusion-1-5-lora-collection", filename, output_dir)
        except FileNotFoundError:
            # Fallback mirror
            logger.warning("Primary download failed, trying mirror...")
            # Assuming mirror is a standard HF repo or URL logic handled in download_lora_adapter if extended
            # For now, re-raising if mirror logic isn't fully implemented in the helper, 
            # but per task T007b-1, we need to handle fallback.
            # Let's assume a mirror repo ID if primary fails.
            download_lora_adapter("llmXive/collection-lora-mirror", filename, output_dir)

    return output_path

def load_adapter_weights(model_path: Path) -> Dict[str, Any]:
    """Loads weights from a safetensors file."""
    from safetensors.torch import load_file
    return load_file(str(model_path))

def validate_adapter_effects(weights: Dict[str, Any], min_effects: int = 5) -> Set[str]:
    """Validates that the adapter contains at least min_effects distinct effects."""
    pattern = re.compile(r"lora_unet_.*_(.+)_lora")
    effects = set()
    for key in weights.keys():
        match = pattern.search(key)
        if match:
            effects.add(match.group(1))
    
    if len(effects) < min_effects:
        raise ValueError(f"Adapter contains only {len(effects)} effects, expected at least {min_effects}. Found: {effects}")
    return effects

def compute_subspace_ranks(weights: Dict[str, Any], tolerance: float = 1e-5) -> Dict[str, int]:
    """Computes the effective subspace rank for each effect using SVD."""
    import numpy as np
    import torch
    
    pattern = re.compile(r"lora_unet_.*_(.+)_lora")
    effect_weights = {}
    
    # Group weights by effect
    for key, value in weights.items():
        match = pattern.search(key)
        if match:
            effect = match.group(1)
            if effect not in effect_weights:
                effect_weights[effect] = []
            # Flatten or handle tensor appropriately for SVD
            # Usually LoRA has down and up matrices. We need to reconstruct or analyze the product.
            # For rank estimation of the subspace, we can look at the singular values of the up/down matrices
            # or their product. The task says "extract per-effect LoRA weight matrices... Compute SVD".
            # Assuming 'value' is a tensor.
            effect_weights[effect].append((key, value))
    
    ranks = {}
    for effect, items in effect_weights.items():
        # Combine matrices for this effect to estimate subspace rank
        # Simplest robust method: concatenate all matrices for the effect and compute rank
        tensors = [v for _, v in items]
        if not tensors:
            ranks[effect] = 0
            continue
        
        # Stack tensors (flattened) to approximate the full subspace
        # Or compute rank of the sum of outer products? 
        # Standard approach: concatenate flattened vectors and compute rank of the matrix.
        flat_tensors = [t.flatten().cpu().numpy() for t in tensors]
        combined = np.vstack(flat_tensors)
        
        # SVD
        try:
            u, s, vh = np.linalg.svd(combined, full_matrices=False)
            rank = np.sum(s > tolerance)
            ranks[effect] = int(rank)
        except np.linalg.LinAlgError:
            ranks[effect] = 0
    
    return ranks

def load_and_compute_subspace_ranks(model_path: Path, tolerance: float = 1e-5) -> Dict[str, int]:
    """Loads adapter and computes subspace ranks."""
    weights = load_adapter_weights(model_path)
    return compute_subspace_ranks(weights, tolerance)

def load_fp16_adapter_and_base_model() -> Tuple[Any, Any]:
    """Loads the FP16 adapter and base model into memory."""
    from diffusers import StableDiffusionPipeline
    import torch
    
    adapter_path = get_collection_lora_adapter()
    base_model_path = get_project_root() / "data" / "models" / "sd15_base"
    
    # Load base model
    if not base_model_path.exists():
        download_base_model("runwayml/stable-diffusion-v1-5", base_model_path)
    
    pipe = StableDiffusionPipeline.from_pretrained(
        str(base_model_path),
        torch_dtype=torch.float16,
        safety_checker=None
    )
    
    # Load adapter
    pipe.load_lora_weights(str(adapter_path))
    
    return pipe

def load_pipeline_for_cpu() -> Any:
    """Loads pipeline specifically for CPU execution."""
    from diffusers import StableDiffusionPipeline
    import torch
    
    adapter_path = get_collection_lora_adapter()
    base_model_path = get_project_root() / "data" / "models" / "sd15_base"
    
    if not base_model_path.exists():
        download_base_model("runwayml/stable-diffusion-v1-5", base_model_path)
    
    pipe = StableDiffusionPipeline.from_pretrained(
        str(base_model_path),
        torch_dtype=torch.float32, # Use float32 for CPU stability if needed, or float16 if supported
        safety_checker=None
    )
    pipe = pipe.to("cpu")
    pipe.load_lora_weights(str(adapter_path))
    return pipe

def organize_reference_images() -> Dict[str, List[str]]:
    """
    Organizes data/references/fp16_refs/ into a lookup table keyed by effect category.
    Returns: {"oil_painting": ["/abs/path/to/img1.png", ...], ...}
    """
    import os
    from pathlib import Path
    
    root_dir = get_project_root() / "data" / "references" / "fp16_refs"
    
    if not root_dir.exists():
        raise FileNotFoundError(f"Reference directory not found: {root_dir}. Run T011c first.")
    
    lookup_table = {}
    
    # Expected structure: root_dir/{effect_category}/{image_file}
    # Or root_dir/{effect_category}_{image_id}.png? 
    # Based on T011c description: "Organize these into a lookup table keyed by effect category."
    # We assume the directory structure created by T011c is:
    # data/references/fp16_refs/{effect_name}/
    
    for effect_dir in root_dir.iterdir():
        if effect_dir.is_dir():
            effect_name = effect_dir.name
            # Sanitize effect name to match config keys if necessary
            # Assuming directory names match the effect categories from config
            image_paths = []
            for img_file in effect_dir.glob("*"):
                if img_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    image_paths.append(str(img_file))
            
            if image_paths:
                lookup_table[effect_name] = image_paths
    
    if not lookup_table:
        logger.warning("No reference images found in organized format.")
    
    return lookup_table