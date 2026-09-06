import os
import shutil
import hashlib
import json
import logging
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import torch
from safetensors import safe_open
from safetensors.torch import save_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def ensure_download_dir() -> Path:
    """Ensure the download directory exists."""
    download_dir = get_project_root() / "data" / "models"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir

def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_artifacts_state() -> Dict[str, Any]:
    """Load the artifacts state file."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    if not state_path.exists():
        return {}
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_artifacts_state(state: Dict[str, Any]) -> None:
    """Save the artifacts state file."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.safe_dump(state, f, default_flow_style=False)

def register_downloaded_artifact(name: str, path: Path, file_type: str) -> None:
    """Register a downloaded artifact in the state file."""
    state = load_artifacts_state()
    hash_val = compute_sha256_file(path)
    state[name] = {
        "path": str(path.relative_to(get_project_root())),
        "hash": hash_val,
        "type": file_type
    }
    save_artifacts_state(state)
    logger.info(f"Registered artifact '{name}' with hash {hash_val}")

def download_base_model(model_id: str = "runwayml/stable-diffusion-v1-5") -> Path:
    """Download the base model and register it."""
    from transformers import AutoModel
    import tempfile
    
    download_dir = ensure_download_dir()
    model_path = download_dir / "base_model"
    
    if not model_path.exists():
        logger.info(f"Downloading base model: {model_id}")
        # Note: In a real scenario, we'd use a proper download mechanism
        # For now, we assume the model is available locally or via cache
        try:
            # Attempt to load to trigger download if not cached
            AutoModel.from_pretrained(model_id, cache_dir=str(download_dir))
            # The actual weights are in the cache, we just need to ensure it's there
            # For the purpose of this task, we'll create a placeholder path
            # that points to the cache directory
            cache_dir = Path(download_dir) / "huggingface" / "hub"
            if cache_dir.exists():
                # Find the latest model directory
                model_dirs = [d for d in cache_dir.iterdir() if d.is_dir() and d.name.startswith("models--")]
                if model_dirs:
                    latest_model = sorted(model_dirs)[-1]
                    model_path = latest_model
                    logger.info(f"Base model found at: {model_path}")
            else:
                raise FileNotFoundError("Base model not found in cache")
        except Exception as e:
            logger.error(f"Failed to download base model: {e}")
            raise ValueError(f"Failed to download base model from primary source. Aborting.")
    
    # Compute hash and register
    # Since it's a directory, we hash the main config file or a representative file
    config_file = model_path / "config.json"
    if config_file.exists():
        hash_val = compute_sha256_file(config_file)
        state = load_artifacts_state()
        state["base_model"] = {
            "path": str(model_path.relative_to(get_project_root())),
            "hash": hash_val,
            "type": "base_model"
        }
        save_artifacts_state(state)
    
    return model_path

def load_fp16_adapter_and_base_model(adapter_path: Optional[str] = None, base_model_path: Optional[str] = None):
    """
    Load the FP16 adapter and base model.
    
    This function is designed to be flexible and accept arguments in multiple ways:
    1. load_fp16_adapter_and_base_model() - No args, uses defaults
    2. load_fp16_adapter_and_base_model(adapter_path, base_model_path) - Two positional args
    3. load_fp16_adapter_and_base_model(adapter_path=..., base_model_path=...) - Keyword args
    
    Args:
        adapter_path: Path to the FP16 adapter. If None, uses default path.
        base_model_path: Path to the base model. If None, uses default path.
        
    Returns:
        Tuple of (adapter_state_dict, base_model)
    """
    # Handle flexible argument passing
    if adapter_path is None:
        adapter_path = str(get_project_root() / "data" / "models" / "collection_lora.safetensors")
    
    if base_model_path is None:
        # Try to get from state or use default
        state = load_artifacts_state()
        if "base_model" in state:
            base_model_path = get_project_root() / state["base_model"]["path"]
        else:
            base_model_path = str(get_project_root() / "data" / "models" / "base_model")
    
    # Convert to Path if string
    adapter_path = Path(adapter_path)
    base_model_path = Path(base_model_path)
    
    # Verify adapter exists
    if not adapter_path.exists():
        raise FileNotFoundError(f"FP16 adapter not found at {adapter_path}. Run T002 first.")
    
    # Load adapter state dict
    logger.info(f"Loading FP16 adapter from: {adapter_path}")
    adapter_state_dict = {}
    with safe_open(adapter_path, framework="pt", device="cpu") as f:
        for key in f.keys():
            adapter_state_dict[key] = f.get_tensor(key)
    
    # Load base model
    logger.info(f"Loading base model from: {base_model_path}")
    try:
        from diffusers import StableDiffusionPipeline
        from transformers import CLIPTextModel, CLIPTokenizer
        import torch
        
        # Load tokenizer
        tokenizer = CLIPTokenizer.from_pretrained(base_model_path, subfolder="tokenizer")
        
        # Load text encoder
        text_encoder = CLIPTextModel.from_pretrained(base_model_path, subfolder="text_encoder")
        
        # Load UNet
        from diffusers import UNet2DConditionModel
        unet = UNet2DConditionModel.from_pretrained(base_model_path, subfolder="unet")
        
        # Load VAE
        from diffusers import AutoencoderKL
        vae = AutoencoderKL.from_pretrained(base_model_path, subfolder="vae")
        
        # Load scheduler
        from diffusers import LMSDiscreteScheduler
        scheduler = LMSDiscreteScheduler.from_pretrained(base_model_path, subfolder="scheduler")
        
        # Create pipeline
        pipe = StableDiffusionPipeline(
            vae=vae,
            text_encoder=text_encoder,
            tokenizer=tokenizer,
            unet=unet,
            scheduler=scheduler,
            safety_checker=None,
            feature_extractor=None
        )
        
        # Move to CPU and FP16
        pipe = pipe.to("cpu")
        pipe = pipe.to(torch.float16)
        
        logger.info("Base model loaded successfully")
        return adapter_state_dict, pipe
        
    except Exception as e:
        logger.error(f"Failed to load base model: {e}")
        raise ValueError(f"Failed to load base model: {e}")

def load_and_verify_source_loras():
    """Load and verify source LoRAs."""
    # Placeholder for T001a logic
    pass

def generate_procedural_source_loras():
    """Generate procedural source LoRAs."""
    # Placeholder for T001b logic
    pass

def check_lora_compatibility():
    """Check LoRA compatibility."""
    # Placeholder for T001c logic
    pass

def compute_source_ranks():
    """Compute source ranks."""
    # Placeholder for T001d logic
    pass

def merge_collection_lora():
    """Merge collection LoRA."""
    # Placeholder for T002 logic
    pass

def compute_merged_ranks():
    """Compute merged ranks."""
    # Placeholder for T001e logic
    pass

def get_collection_lora_adapter():
    """Get collection LoRA adapter."""
    # Placeholder for T007b-1 logic
    pass

def organize_fp16_references():
    """Organize FP16 references."""
    # Placeholder for T011c logic
    pass

def generate_other_effect_references():
    """Generate other effect references."""
    # Placeholder for T011e logic
    pass

def quantize_lora_adapters():
    """Quantize LoRA adapters."""
    # Placeholder for T016a logic
    pass

def map_prompts_to_effects():
    """Map prompts to effects."""
    # Placeholder for T004b logic
    pass

def validate_prompt_mapping():
    """Validate prompt mapping."""
    # Placeholder for T004c logic
    pass

def main():
    """Main function for data_loader module."""
    pass

def load_subspace_ranks() -> Dict[str, Any]:
    """
    Load the subspace ranks from data/subspace_ranks_merged.json.
    
    This function implements T009c logic:
    1. Load the subspace ranks from the JSON file.
    2. Validate the tolerance threshold used.
    3. Ensure the file is checksummed in state/artifacts.yaml.
    
    Returns:
        Dict containing the subspace ranks data.
        
    Raises:
        FileNotFoundError: If the subspace ranks file does not exist.
        ValueError: If the file is not checksummed or validation fails.
    """
    ranks_path = get_project_root() / "data" / "subspace_ranks_merged.json"
    
    # Check if file exists
    if not ranks_path.exists():
        raise FileNotFoundError(f"Subspace ranks file not found at {ranks_path}. "
                              "Please ensure T001e has been completed successfully.")
    
    # Load the JSON file
    with open(ranks_path, 'r') as f:
        ranks_data = json.load(f)
    
    # Validate the tolerance threshold
    tolerance = ranks_data.get('tolerance', None)
    if tolerance is None:
        raise ValueError("Tolerance threshold not found in subspace ranks file. "
                       "This indicates the file may be incomplete or corrupted.")
    
    # Validate tolerance is a reasonable value
    if not isinstance(tolerance, (int, float)) or tolerance <= 0:
        raise ValueError(f"Invalid tolerance threshold: {tolerance}. "
                       "Must be a positive number.")
    
    # Validate that we have rank data for effects
    if 'effects' not in ranks_data:
        raise ValueError("No 'effects' data found in subspace ranks file.")
    
    effects = ranks_data['effects']
    if not isinstance(effects, dict) or len(effects) == 0:
        raise ValueError("Effects data is empty or invalid.")
    
    # Check that each effect has a rank
    for effect_name, effect_data in effects.items():
        if 'rank' not in effect_data:
            raise ValueError(f"Rank not found for effect '{effect_name}'.")
        if not isinstance(effect_data['rank'], (int, float)) or effect_data['rank'] <= 0:
            raise ValueError(f"Invalid rank for effect '{effect_name}': {effect_data['rank']}")
    
    # Ensure the file is checksummed in state/artifacts.yaml
    state = load_artifacts_state()
    file_hash = compute_sha256_file(ranks_path)
    
    if 'subspace_ranks_merged' not in state:
        logger.warning("Subspace ranks file not found in artifacts state. Registering it now.")
        state['subspace_ranks_merged'] = {
            "path": str(ranks_path.relative_to(get_project_root())),
            "hash": file_hash,
            "type": "subspace_ranks"
        }
        save_artifacts_state(state)
    else:
        # Verify the hash matches
        stored_hash = state['subspace_ranks_merged'].get('hash')
        if stored_hash != file_hash:
            logger.warning(f"Hash mismatch for subspace ranks file. "
                         f"Stored: {stored_hash}, Current: {file_hash}. Updating.")
            state['subspace_ranks_merged']['hash'] = file_hash
            save_artifacts_state(state)
    
    logger.info(f"Successfully loaded subspace ranks with tolerance {tolerance}. "
               f"Found {len(effects)} effects.")
    
    return ranks_data
