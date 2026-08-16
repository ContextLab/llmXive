import os
import torch
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import json
from config import load_config
from data_loader import load_fp16_adapter_and_base_model, get_project_root
from state_manager import compute_sha256, register_artifact, save_artifacts_state, load_artifacts_state

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_reference_image(
    pipe,
    prompt: str,
    seed: int,
    width: int = 512,
    height: int = 512,
    device: str = "cpu"
) -> Image.Image:
    """
    Generate a single image using the provided pipeline, prompt, and seed.
    """
    logger.info(f"Generating reference image for prompt: '{prompt}' with seed {seed}")
    generator = torch.Generator(device=device).manual_seed(seed)
    
    # Move model to device if not already there (though for CPU runner, it stays on CPU)
    # Note: In a real scenario with GPU, we would move the pipeline to cuda.
    # For this task, we assume the pipeline is already loaded on the correct device.
    
    with torch.no_grad():
        image = pipe(
            prompt=prompt,
            generator=generator,
            width=width,
            height=height,
            num_inference_steps=50, # Reduced for speed in reference generation
            guidance_scale=7.5
        ).images[0]
    
    return image

def generate_fp16_baseline_images(
    pipe,
    prompts: List[str],
    seeds: List[int],
    output_dir: Path,
    width: int = 512,
    height: int = 512,
    device: str = "cpu"
) -> Dict[str, Path]:
    """
    Generate baseline images for a list of prompts and seeds.
    Saves images to output_dir and returns a mapping of prompt to file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    
    for prompt, seed in zip(prompts, seeds):
        # Sanitize prompt for filename
        safe_name = prompt.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_path = output_dir / f"{safe_name}_seed{seed}.png"
        
        if output_path.exists():
            logger.info(f"Skipping existing image: {output_path}")
        else:
            image = generate_reference_image(pipe, prompt, seed, width, height, device)
            image.save(output_path)
            logger.info(f"Saved image: {output_path}")
        
        results[prompt] = output_path
    
    return results

def generate_fp16_reference_images(
    config: Dict,
    output_dir_name: str = "fp16_refs"
) -> Dict[str, List[str]]:
    """
    T011c Implementation: Generate and save FP16 Reference Images for ALL 10 effect prompts.
    Uses seed 42 for all, resolution 512x512.
    Saves to data/references/fp16_refs/
    Returns a lookup table keyed by effect category (prompt).
    """
    project_root = get_project_root()
    prompts = config.get("prompts", [])
    seed = 42
    width = 512
    height = 512
    
    if not prompts:
        raise ValueError("No prompts found in config.yaml")
    
    logger.info(f"Starting FP16 Reference Image generation for {len(prompts)} prompts.")
    
    # Load the pipeline (FP16 adapter + base model)
    # This function is expected to be implemented in data_loader.py
    try:
        pipe = load_fp16_adapter_and_base_model()
    except Exception as e:
        logger.error("Failed to load FP16 adapter and base model.")
        raise e
    
    output_dir = project_root / "data" / "references" / output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    reference_lookup = {}
    state_file = project_root / "state" / "artifacts.yaml"
    
    # Ensure we load existing state to append new artifacts
    try:
        current_state = load_artifacts_state()
    except FileNotFoundError:
        current_state = {"artifacts": []}
    
    for prompt in prompts:
        safe_name = prompt.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_path = output_dir / f"{safe_name}_seed{seed}.png"
        
        logger.info(f"Generating reference for: {prompt} -> {output_path}")
        
        if not output_path.exists():
            image = generate_reference_image(pipe, prompt, seed, width, height, "cpu")
            image.save(output_path)
            logger.info(f"Saved reference image: {output_path}")
        else:
            logger.info(f"Reference image already exists: {output_path}")
        
        # Register artifact in state
        file_hash = compute_sha256(output_path)
        artifact_entry = {
            "path": str(output_path.relative_to(project_root)),
            "hash": file_hash,
            "type": "reference_image",
            "prompt": prompt,
            "seed": seed,
            "resolution": f"{width}x{height}"
        }
        
        # Check if already registered to avoid duplicates
        existing = False
        for entry in current_state["artifacts"]:
            if entry.get("path") == artifact_entry["path"]:
                existing = True
                break
        
        if not existing:
            current_state["artifacts"].append(artifact_entry)
        
        reference_lookup[prompt] = str(output_path)
    
    save_artifacts_state(current_state)
    logger.info("All FP16 Reference Images generated and state updated.")
    
    return reference_lookup

def generate_images_for_adapters(
    adapter_paths: Dict[str, Path],
    prompts: List[str],
    seeds: List[int],
    output_base_dir: Path,
    width: int = 512,
    height: int = 512,
    device: str = "cpu"
) -> Dict[str, Dict[str, Path]]:
    """
    Generate images for multiple quantized adapters.
    """
    results = {}
    for adapter_name, adapter_path in adapter_paths.items():
        logger.info(f"Processing adapter: {adapter_name}")
        # TODO: Load specific adapter and generate images
        # This is a placeholder for the full logic which would involve loading the quantized weights
        # and running generation similar to baseline.
        pass
    return results

def generate_images(
    pipe,
    prompts: List[str],
    seeds: List[int],
    output_dir: Path,
    width: int = 512,
    height: int = 512,
    device: str = "cpu"
) -> List[Path]:
    """
    Generic image generation function.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for prompt, seed in zip(prompts, seeds):
        safe_name = prompt.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_path = output_dir / f"{safe_name}_seed{seed}.png"
        if not output_path.exists():
            image = generate_reference_image(pipe, prompt, seed, width, height, device)
            image.save(output_path)
        paths.append(output_path)
    return paths

def main():
    """
    Entry point for T011c execution.
    Loads config, generates reference images, and saves the lookup table.
    """
    config = load_config()
    logger.info("Running T011c: Generate FP16 Reference Images")
    
    try:
        ref_lookup = generate_fp16_reference_images(config, "fp16_refs")
        
        # Save the lookup table to a JSON file for downstream tasks (T011d, T018)
        project_root = get_project_root()
        lookup_path = project_root / "data" / "references" / "fp16_refs_lookup.json"
        with open(lookup_path, "w") as f:
            json.dump(ref_lookup, f, indent=2)
        
        logger.info(f"Reference lookup table saved to {lookup_path}")
        logger.info("T011c completed successfully.")
        
    except Exception as e:
        logger.error(f"T011c failed: {e}")
        raise

if __name__ == "__main__":
    main()