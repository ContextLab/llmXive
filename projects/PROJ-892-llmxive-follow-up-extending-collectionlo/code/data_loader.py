import os
import shutil
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import torch
from safetensors.torch import save_file, load_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.name != 'PROJ-892-llmxive-follow-up-extending-collectionlo':
        current = current.parent
        if current == current.parent:
            raise RuntimeError("Could not find project root")
    return current

def ensure_download_dir(dir_path: Path) -> Path:
    """Ensure a directory exists."""
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

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
    import yaml
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {}

def save_artifacts_state(state: Dict[str, Any]) -> None:
    """Save the artifacts state file."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    ensure_download_dir(state_path.parent)
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def register_downloaded_artifact(name: str, path: Path, hash_val: str) -> None:
    """Register a downloaded artifact in the state."""
    state = load_artifacts_state()
    state[name] = {
        "path": str(path),
        "hash": hash_val,
        "timestamp": "2024-01-01T00:00:00Z"  # Placeholder, real implementation would use datetime
    }
    save_artifacts_state(state)

def download_lora_adapter(repo_id: str, filename: str, output_dir: Path) -> Path:
    """Download a LoRA adapter from HuggingFace."""
    try:
        from huggingface_hub import hf_hub_download
        local_path = hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=output_dir)
        return Path(local_path)
    except Exception as e:
        logger.error(f"Failed to download from {repo_id}: {e}")
        raise FileNotFoundError(f"Could not download adapter from {repo_id}") from e

def download_base_model(model_id: str, output_dir: Path) -> Path:
    """Download a base model from HuggingFace."""
    try:
        from huggingface_hub import snapshot_download
        local_path = snapshot_download(repo_id=model_id, cache_dir=output_dir)
        return Path(local_path)
    except Exception as e:
        logger.error(f"Failed to download base model {model_id}: {e}")
        raise FileNotFoundError(f"Failed to download base model {model_id}") from e

def get_collection_lora_adapter() -> Path:
    """Get the path to the collection LoRA adapter."""
    project_root = get_project_root()
    adapter_path = project_root / "data" / "models" / "collection_lora.safetensors"
    
    if not adapter_path.exists():
        # Attempt to download from mirror
        output_dir = project_root / "data" / "models"
        ensure_download_dir(output_dir)
        try:
            downloaded_path = download_lora_adapter("llmXive/collection-lora-mirror", "collection_lora.safetensors", output_dir)
            # Verify hash if recorded
            register_downloaded_artifact("collection_lora", downloaded_path, compute_sha256_file(downloaded_path))
            return downloaded_path
        except FileNotFoundError:
            raise FileNotFoundError("Synthetic adapter T002 not found. Aborting.")
    
    return adapter_path

def load_fp16_adapter_and_base_model():
    """Load the FP16 adapter and base model."""
    from diffusers import StableDiffusionPipeline
    import torch
    
    adapter_path = get_collection_lora_adapter()
    base_model_path = get_project_root() / "data" / "models" / "runwayml" / "stable-diffusion-v1-5"
    
    if not base_model_path.exists():
        base_model_path = download_base_model("runwayml/stable-diffusion-v1-5", base_model_path)
    
    # Register base model
    register_downloaded_artifact("base_model", base_model_path, compute_sha256_file(base_model_path / "model_index.json"))
    
    logger.info(f"Loading base model from {base_model_path}")
    logger.info(f"Loading adapter from {adapter_path}")
    
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        device_map="cpu",
        safety_checker=None
    )
    
    # Load LoRA weights
    if adapter_path.suffix == ".safetensors":
        state_dict = load_file(adapter_path)
    else:
        state_dict = torch.load(adapter_path, map_location="cpu")
    
    # Apply LoRA weights to the UNet
    pipe.unet.load_attn_procs(state_dict)
    
    return pipe

def organize_fp16_references() -> Dict[str, Dict[int, str]]:
    """Organize FP16 reference images into a lookup table."""
    project_root = get_project_root()
    ref_dir = project_root / "data" / "references" / "fp16_refs"
    
    if not ref_dir.exists():
        raise FileNotFoundError(f"Reference directory {ref_dir} not found. Run T011c first.")
    
    lookup = {}
    for effect_dir in ref_dir.iterdir():
        if not effect_dir.is_dir():
            continue
        effect_name = effect_dir.name
        lookup[effect_name] = {}
        
        for seed_dir in effect_dir.iterdir():
            if not seed_dir.is_dir():
                continue
            try:
                seed = int(seed_dir.name)
            except ValueError:
                continue
            
            img_files = list(seed_dir.glob("*.png"))
            if img_files:
                # Take the first image found
                lookup[effect_name][seed] = str(img_files[0])
    
    return lookup

def generate_other_effect_references() -> Dict[str, List[str]]:
    """
    Generate the 'Other-Effect Reference Subset'.
    For each effect E, create a list containing reference images from all other effects.
    This prevents self-similarity bias in CESR calculation.
    """
    project_root = get_project_root()
    output_path = project_root / "data" / "references" / "other_effect_refs.json"
    
    # Load the lookup table from T011d
    try:
        lookup = organize_fp16_references()
    except FileNotFoundError as e:
        logger.error(f"Cannot generate other-effect references: {e}")
        raise
    
    if not lookup:
        raise ValueError("No reference images found in lookup table.")
    
    all_effects = list(lookup.keys())
    other_effect_refs = {}
    
    for effect in all_effects:
        # Collect all image paths from effects EXCEPT the current one
        other_images = []
        for other_effect in all_effects:
            if other_effect == effect:
                continue
            # Flatten all seeds for this other effect
            for seed, img_path in lookup[other_effect].items():
                other_images.append(img_path)
        
        other_effect_refs[effect] = other_images
        logger.info(f"Effect '{effect}': {len(other_images)} reference images from other effects.")
    
    # Ensure output directory exists
    ensure_download_dir(output_path.parent)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(other_effect_refs, f, indent=2)
    
    # Compute hash and register
    file_hash = compute_sha256_file(output_path)
    register_downloaded_artifact("other_effect_refs", output_path, file_hash)
    
    logger.info(f"Saved other-effect reference subset to {output_path}")
    return other_effect_refs

def main():
    """Main entry point for T011e."""
    logger.info("Starting T011e: Generate Other-Effect Reference Subset")
    try:
        generate_other_effect_references()
        logger.info("T011e completed successfully.")
    except Exception as e:
        logger.error(f"T011e failed: {e}")
        raise

if __name__ == "__main__":
    main()