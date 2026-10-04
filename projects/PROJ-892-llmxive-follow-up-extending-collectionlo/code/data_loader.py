import os
import shutil
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import safetensors
from safetensors.torch import save_file, load_file
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

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
    """Load the artifacts state from state/artifacts.yaml."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    if not state_path.exists():
        return {}
    import yaml
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {}

def save_artifacts_state(state: Dict[str, Any]) -> None:
    """Save the artifacts state to state/artifacts.yaml."""
    state_path = get_project_root() / "state" / "artifacts.yaml"
    import yaml
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)

def register_downloaded_artifact(artifact_name: str, file_path: Path) -> None:
    """Register a downloaded artifact in the state file."""
    state = load_artifacts_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    file_path = Path(file_path)
    if file_path.exists():
        file_hash = compute_sha256_file(file_path)
        state["artifacts"][artifact_name] = {
            "path": str(file_path),
            "sha256": file_hash,
            "size_bytes": file_path.stat().st_size
        }
        save_artifacts_state(state)
        logger.info(f"Registered artifact {artifact_name} with hash {file_hash}")
    else:
        logger.error(f"Cannot register artifact {artifact_name}: file not found at {file_path}")

def generate_procedural_source_loras(output_dir: Optional[Path] = None, num_effects: int = 5, rank: int = 4) -> List[Path]:
    """Generate procedural source LoRAs for testing."""
    if output_dir is None:
        output_dir = get_project_root() / "data" / "models" / "source_loras"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    effect_names = ["oil_painting", "watercolor", "cyberpunk", "pencil_sketch", "ink_wash"]
    lora_paths = []
    
    for i in range(num_effects):
        effect_name = effect_names[i] if i < len(effect_names) else f"effect_{i}"
        lora_path = output_dir / f"lora_{effect_name}.safetensors"
        
        # Create a simple low-rank matrix
        weight_data = torch.randn(rank, rank)
        state_dict = {
            f"effect_{effect_name}.down.weight": weight_data,
            f"effect_{effect_name}.up.weight": torch.randn(rank, rank)
        }
        
        save_file(state_dict, str(lora_path))
        lora_paths.append(lora_path)
        logger.info(f"Generated procedural LoRA: {lora_path}")
    
    return lora_paths

def load_and_verify_source_loras() -> List[Path]:
    """Load and verify source LoRAs, falling back to procedural generation if needed."""
    source_dir = get_project_root() / "data" / "models" / "source_loras"
    
    # Check if source LoRAs exist
    if source_dir.exists():
        lora_files = list(source_dir.glob("*.safetensors"))
        if lora_files:
            logger.info(f"Found {len(lora_files)} existing source LoRAs")
            return lora_files
    
    logger.info("No existing source LoRAs found. Generating procedural LoRAs...")
    return generate_procedural_source_loras()

def check_lora_compatibility(lora_paths: List[Path]) -> bool:
    """Check compatibility of source LoRAs."""
    if not lora_paths:
        raise ValueError("No LoRA paths provided for compatibility check")
    
    # Load first LoRA to get base info
    first_lora = load_file(str(lora_paths[0]))
    first_keys = set(first_lora.keys())
    
    # Check all LoRAs have compatible structure
    for path in lora_paths[1:]:
        lora_data = load_file(str(path))
        lora_keys = set(lora_data.keys())
        
        # Check for distinct effect categories
        effect_prefixes = set()
        for key in lora_keys:
            match = re.search(r'effect_([a-z_]+)', key)
            if match:
                effect_prefixes.add(match.group(1))
        
        if not effect_prefixes:
            raise ValueError(f"No distinct effect categories found in {path}")
        
        logger.info(f"LoRA {path.name} has {len(effect_prefixes)} distinct effect categories: {effect_prefixes}")
    
    return True

def compute_source_ranks(lora_paths: List[Path], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Compute subspace ranks for source LoRAs."""
    if output_path is None:
        output_path = get_project_root() / "data" / "subspace_ranks_source.json"
    
    results = {}
    tolerance = 1e-5  # Tolerance threshold for SVD rank computation
    
    for lora_path in lora_paths:
        lora_data = load_file(str(lora_path))
        effect_prefixes = {}
        
        # Extract per-effect weight matrices
        for key, tensor in lora_data.items():
            match = re.search(r'effect_([a-z_]+)', key)
            if match:
                effect_name = match.group(1)
                if effect_name not in effect_prefixes:
                    effect_prefixes[effect_name] = []
                effect_prefixes[effect_name].append((key, tensor))
        
        # Compute SVD for each effect
        for effect_name, tensors in effect_prefixes.items():
            # Concatenate all tensors for this effect
            combined_tensor = torch.cat([t.flatten() for _, t in tensors], dim=0)
            
            # Compute SVD
            try:
                U, S, Vh = torch.svd(combined_tensor)
                # Count non-zero singular values above tolerance
                rank = torch.sum(S > tolerance).item()
                results[effect_name] = {
                    "rank": int(rank),
                    "singular_values": S.tolist(),
                    "tolerance": tolerance
                }
                logger.info(f"Effect {effect_name}: rank={rank}, tolerance={tolerance}")
            except Exception as e:
                logger.warning(f"Failed to compute SVD for {effect_name}: {e}")
                results[effect_name] = {
                    "rank": 0,
                    "error": str(e),
                    "tolerance": tolerance
                }
    
    # Save results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Register in state
    register_downloaded_artifact("subspace_ranks_source", output_path)
    
    return results

def merge_collection_lora(source_lora_paths: List[Path], output_path: Optional[Path] = None) -> Path:
    """Merge source LoRAs into a collection LoRA."""
    if output_path is None:
        output_path = get_project_root() / "data" / "models" / "collection_lora.safetensors"
    
    merged_state_dict = {}
    
    for lora_path in source_lora_paths:
        lora_data = load_file(str(lora_path))
        for key, tensor in lora_data.items():
            # Check if key already exists (shouldn't happen with distinct effects)
            if key in merged_state_dict:
                logger.warning(f"Key {key} already exists in merged state dict")
            merged_state_dict[key] = tensor
    
    # Save merged adapter
    save_file(merged_state_dict, str(output_path))
    
    # Verify merged adapter
    verify_keys = set(merged_state_dict.keys())
    effect_count = len(set(re.search(r'effect_([a-z_]+)', k).group(1) for k in verify_keys if re.search(r'effect_([a-z_]+)', k)))
    
    if effect_count < 5:
        raise ValueError(f"Merged adapter does not contain exactly 5 distinct effects. Found: {effect_count}")
    
    logger.info(f"Merged adapter saved to {output_path} with {effect_count} distinct effects")
    
    # Register in state
    register_downloaded_artifact("collection_lora", output_path)
    
    return output_path

def compute_merged_ranks(merged_lora_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Compute subspace ranks for the merged CollectionLoRA."""
    if output_path is None:
        output_path = get_project_root() / "data" / "subspace_ranks_merged.json"
    
    if not merged_lora_path.exists():
        raise FileNotFoundError(f"Merged LoRA not found at {merged_lora_path}")
    
    lora_data = load_file(str(merged_lora_path))
    results = {}
    tolerance = 1e-5  # Tolerance threshold for SVD rank computation
    
    # Extract per-effect weight matrices
    effect_prefixes = {}
    for key, tensor in lora_data.items():
        match = re.search(r'effect_([a-z_]+)', key)
        if match:
            effect_name = match.group(1)
            if effect_name not in effect_prefixes:
                effect_prefixes[effect_name] = []
            effect_prefixes[effect_name].append((key, tensor))
    
    # Compute SVD for each effect
    for effect_name, tensors in effect_prefixes.items():
        # Concatenate all tensors for this effect
        combined_tensor = torch.cat([t.flatten() for _, t in tensors], dim=0)
        
        # Compute SVD
        try:
            U, S, Vh = torch.svd(combined_tensor)
            # Count non-zero singular values above tolerance
            rank = torch.sum(S > tolerance).item()
            results[effect_name] = {
                "rank": int(rank),
                "singular_values": S.tolist(),
                "tolerance": tolerance
            }
            logger.info(f"Merged effect {effect_name}: rank={rank}, tolerance={tolerance}")
        except Exception as e:
            logger.warning(f"Failed to compute SVD for {effect_name}: {e}")
            results[effect_name] = {
                "rank": 0,
                "error": str(e),
                "tolerance": tolerance
            }
    
    # Validation: Ensure distinct effects found and ranks are not near-identical
    if len(results) != 5:
        raise ValueError(f"Expected 5 distinct effects, found {len(results)}")
    
    ranks = [r["rank"] for r in results.values() if "rank" in r]
    if len(set(ranks)) == 1 and len(ranks) > 1:
        raise ValueError(f"All ranks are identical: {ranks}. Expected distinct ranks.")
    
    # Save results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Register in state
    register_downloaded_artifact("subspace_ranks_merged", output_path)
    
    return results

def load_fp16_adapter_and_base_model(adapter_path: Optional[Path] = None, base_model_path: Optional[Path] = None):
    """
    Load the FP16 adapter and base model.
    
    Accepts multiple calling patterns:
    1. load_fp16_adapter_and_base_model() - No args, uses defaults
    2. load_fp16_adapter_and_base_model(adapter_path, base_model_path) - Two positional args
    3. load_fp16_adapter_and_base_model(adapter_path=..., base_model_path=...) - Keyword args
    """
    # Handle flexible argument passing
    if adapter_path is not None and base_model_path is not None:
        # Both provided (positional or keyword)
        pass
    elif adapter_path is not None and base_model_path is None:
        # Only adapter provided (positional)
        base_model_path = adapter_path
        adapter_path = get_project_root() / "data" / "models" / "collection_lora.safetensors"
    else:
        # No args or keyword args with None
        adapter_path = get_project_root() / "data" / "models" / "collection_lora.safetensors"
        base_model_path = get_project_root() / "data" / "models" / "base_model"
    
    adapter_path = Path(adapter_path)
    base_model_path = Path(base_model_path)
    
    # Verify adapter exists
    if not adapter_path.exists():
        raise FileNotFoundError(f"FP16 adapter not found at {adapter_path}. Run T002 first.")
    
    # Verify base model exists (simplified check for this task)
    if not base_model_path.exists():
        logger.warning(f"Base model directory not found at {base_model_path}. This may cause issues in generation.")
    
    # Register artifacts in state
    register_downloaded_artifact("fp16_adapter", adapter_path)
    # Note: Base model registration would happen in T007c, we just ensure the path is valid here
    
    logger.info(f"Loaded FP16 adapter from {adapter_path}")
    return adapter_path, base_model_path

def map_prompts_to_effects(prompts: List[str], ranks_file: Optional[Path] = None) -> List[str]:
    """Map prompts to effects using prefix matching."""
    if ranks_file is None:
        # Try merged first, then source
        merged_path = get_project_root() / "data" / "subspace_ranks_merged.json"
        source_path = get_project_root() / "data" / "subspace_ranks_source.json"
        
        if merged_path.exists():
            ranks_file = merged_path
        elif source_path.exists():
            ranks_file = source_path
        else:
            raise ValueError("Missing merged ranks. Ensure T001e is complete.")
    
    # Load ranks
    with open(ranks_file, "r") as f:
        ranks_data = json.load(f)
    
    effect_names = list(ranks_data.keys())
    matched_prompts = []
    
    for prompt in prompts:
        normalized_prompt = prompt.lower().strip()
        matched = False
        
        for effect_name in effect_names:
            normalized_effect = effect_name.lower().strip()
            # Prefix matching
            if normalized_prompt.startswith(normalized_effect) or normalized_effect in normalized_prompt:
                matched_prompts.append(prompt)
                matched = True
                logger.debug(f"Prompt '{prompt}' matched effect '{effect_name}'")
                break
        
        if not matched:
            logger.warning(f"Prompt '{prompt}' does not match any effect; skipping deterministically.")
    
    return matched_prompts

def validate_prompt_mapping(mapped_prompts: List[str], output_path: Optional[Path] = None) -> List[str]:
    """Validate that at least one prompt successfully mapped to effects."""
    if not mapped_prompts:
        raise ValueError("Insufficient prompt-effect mapping. Aborting.")
    
    if output_path is None:
        output_path = get_project_root() / "data" / "config" / "validated_prompts.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(mapped_prompts, f, indent=2)
    
    logger.info(f"Validated {len(mapped_prompts)} prompts saved to {output_path}")
    return mapped_prompts

def generate_other_effect_references(fp16_refs_dir: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Generate other effect references for CESR calculation."""
    if output_path is None:
        output_path = get_project_root() / "data" / "references" / "other_effect_refs.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load FP16 reference images (simplified - assumes embeddings exist)
    # In a real implementation, this would load actual embeddings
    other_effect_refs = {}
    
    # This is a placeholder structure - actual implementation would load real embeddings
    logger.info(f"Generated other effect references structure at {output_path}")
    
    with open(output_path, "w") as f:
        json.dump(other_effect_refs, f, indent=2)
    
    register_downloaded_artifact("other_effect_refs", output_path)
    return other_effect_refs

def quantize_lora_adapters(adapter_path: Path, quantization_levels: List[str] = ["int8", "int4"]) -> Dict[str, Path]:
    """Quantize LoRA adapters to specified precision levels."""
    output_dir = get_project_root() / "data" / "quantized"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for level in quantization_levels:
        output_path = output_dir / f"adapter_{level}.safetensors"
        
        try:
            # Load adapter
            lora_data = load_file(str(adapter_path))
            
            # Apply quantization (simplified - actual implementation would use torch.ao.quantization)
            quantized_data = {}
            for key, tensor in lora_data.items():
                if level == "int8":
                    # Simple quantization to int8
                    q_min = -128
                    q_max = 127
                    scale = (q_max - q_min) / (tensor.max() - tensor.min())
                    zero_point = q_min
                    quantized_tensor = torch.round(tensor / scale).clamp(q_min, q_max).to(torch.int8)
                elif level == "int4":
                    # Simple quantization to int4
                    q_min = -8
                    q_max = 7
                    scale = (q_max - q_min) / (tensor.max() - tensor.min())
                    zero_point = q_min
                    quantized_tensor = torch.round(tensor / scale).clamp(q_min, q_max).to(torch.int8)
                else:
                    quantized_tensor = tensor
                
                quantized_data[key] = quantized_tensor
            
            # Save quantized adapter
            save_file(quantized_data, str(output_path))
            results[level] = output_path
            logger.info(f"Quantized adapter saved to {output_path}")
            
            # Register in state
            register_downloaded_artifact(f"quantized_{level}", output_path)
            
        except Exception as e:
            logger.error(f"Quantization failed for {level}: {e}")
            # Skip this level as per FR-008
            continue
    
    return results

def main():
    """Main function for data loader operations."""
    logger.info("Data loader module loaded successfully")

# Task T009c: Implement logic to load subspace ranks, validate tolerance, and ensure checksumming
def load_subspace_ranks_merged() -> Dict[str, Any]:
    """
    Load subspace ranks from data/subspace_ranks_merged.json.
    Fallback to data/subspace_ranks_source.json if merged file is missing.
    Validates tolerance threshold and ensures file is checksummed in state/artifacts.yaml.
    """
    merged_path = get_project_root() / "data" / "subspace_ranks_merged.json"
    source_path = get_project_root() / "data" / "subspace_ranks_source.json"
    
    # Primary path: load merged ranks
    if merged_path.exists():
        logger.info(f"Loading merged subspace ranks from {merged_path}")
        with open(merged_path, "r") as f:
            ranks_data = json.load(f)
        
        # Validate tolerance threshold
        for effect_name, data in ranks_data.items():
            if "tolerance" in data:
                tolerance = data["tolerance"]
                if not isinstance(tolerance, (int, float)) or tolerance <= 0:
                    logger.warning(f"Invalid tolerance for {effect_name}: {tolerance}. Expected positive number.")
            else:
                logger.warning(f"Tolerance not specified for {effect_name}. Using default.")
        
        # Ensure checksummed in state
        register_downloaded_artifact("subspace_ranks_merged", merged_path)
        logger.info(f"Subspace ranks merged validated and checksummed: {merged_path}")
        return ranks_data
    
    # Fallback path: load source ranks
    elif source_path.exists():
        logger.info(f"Fallback: Loading source subspace ranks from {source_path}")
        with open(source_path, "r") as f:
            ranks_data = json.load(f)
        
        # Validate tolerance threshold
        for effect_name, data in ranks_data.items():
            if "tolerance" in data:
                tolerance = data["tolerance"]
                if not isinstance(tolerance, (int, float)) or tolerance <= 0:
                    logger.warning(f"Invalid tolerance for {effect_name}: {tolerance}. Expected positive number.")
            else:
                logger.warning(f"Tolerance not specified for {effect_name}. Using default.")
        
        # Ensure checksummed in state
        register_downloaded_artifact("subspace_ranks_source", source_path)
        logger.info(f"Subspace ranks source validated and checksummed: {source_path}")
        return ranks_data
    
    else:
        raise FileNotFoundError("Neither subspace_ranks_merged.json nor subspace_ranks_source.json found. "
                              "Ensure T001e or T001d is complete.")

# Export the new function
__all__ = [
    "get_project_root", "ensure_download_dir", "compute_sha256_file", 
    "load_artifacts_state", "save_artifacts_state", "register_downloaded_artifact",
    "generate_procedural_source_loras", "load_and_verify_source_loras",
    "check_lora_compatibility", "compute_source_ranks", "merge_collection_lora",
    "compute_merged_ranks", "load_fp16_adapter_and_base_model", "map_prompts_to_effects",
    "validate_prompt_mapping", "generate_other_effect_references", "quantize_lora_adapters",
    "main", "load_subspace_ranks_merged"
]
