import os
import torch
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from data_loader import load_adapter_weights, save_adapter_weights
from state_manager import compute_sha256, register_artifact

logger = logging.getLogger(__name__)

def generate_images(model, adapter, prompt: str, seed: int, output_dir: str) -> str:
    """Generate a single image using the provided model and adapter."""
    # Set seed for reproducibility
    torch.manual_seed(seed)
    
    # Prepare pipeline
    pipe = model.to('cpu')
    pipe.load_lora_weights(adapter)
    
    # Generate image
    image = pipe(
        prompt,
        num_inference_steps=50,
        guidance_scale=7.5,
        generator=torch.Generator(device='cpu').manual_seed(seed)
    ).images[0]
    
    # Save image
    output_path = Path(output_dir) / f"{prompt.replace(' ', '_')}.png"
    image.save(output_path)
    
    # Register artifact
    image_hash = compute_sha256(output_path)
    register_artifact(
        output_path, 
        {'prompt': prompt, 'type': 'generated', 'seed': seed},
        image_hash
    )
    
    return str(output_path)

def generate_reference_image(model, adapter, seed: int, prompt: str, output_path: str):
    """Generate a single reference image for baseline consistency checks."""
    torch.manual_seed(seed)
    
    pipe = model.to('cpu')
    pipe.load_lora_weights(adapter)
    
    image = pipe(
        prompt,
        num_inference_steps=50,
        guidance_scale=7.5,
        generator=torch.Generator(device='cpu').manual_seed(seed)
    ).images[0]
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    
    # Register artifact
    image_hash = compute_sha256(output_path)
    register_artifact(
        output_path, 
        {'prompt': prompt, 'type': 'baseline_reference', 'seed': seed},
        image_hash
    )
    
    logger.info(f"Generated baseline reference image: {output_path} (SHA-256: {image_hash})")

def generate_fp16_reference_images(model, adapter, prompts: List[str], seed: int, output_dir: str) -> Dict[str, str]:
    """Generate reference images for all prompts in FP16."""
    results = {}
    
    for prompt in prompts:
        output_path = Path(output_dir) / f"{prompt.replace(' ', '_')}.png"
        results[prompt] = generate_images(model, adapter, prompt, seed, str(output_dir))
    
    logger.info(f"Generated {len(prompts)} FP16 reference images")
    return results

def generate_images_for_adapters(model, adapter_paths: Dict[str, str], prompts: List[str], base_seed: int, output_base_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Generate images for multiple quantized adapters (INT8, INT4) using the same prompt list.
    
    Args:
        model: The base DiffusionPipeline model (loaded on CPU).
        adapter_paths: A dictionary mapping quantization level (e.g., 'int8', 'int4') 
                       to the path of the quantized adapter weights.
        prompts: List of effect prompts from config.yaml.
        base_seed: Base seed value for reproducibility.
        output_base_dir: Base directory where results will be saved (e.g., 'data/generated').
    
    Returns:
        A nested dictionary: {quantization_level: {prompt: output_path}}
    """
    all_results = {}
    
    for quant_level, adapter_path in adapter_paths.items():
        logger.info(f"Starting generation for {quant_level.upper()} adapter: {adapter_path}")
        
        # Create output directory for this quantization level
        output_dir = Path(output_base_dir) / quant_level
        os.makedirs(output_dir, exist_ok=True)
        
        level_results = {}
        
        for idx, prompt in enumerate(prompts):
            # Derive a deterministic seed for this prompt within this level
            # Using the base_seed + index to ensure different prompts get different seeds
            # but the same prompt/level combo always gets the same seed.
            seed = base_seed + idx
            
            logger.info(f"Generating image for prompt '{prompt}' with seed {seed}")
            
            try:
                # Call the existing generate_images function which handles pipeline setup
                # Note: We pass the specific quantized adapter path
                output_path = generate_images(model, adapter_path, prompt, seed, str(output_dir))
                level_results[prompt] = output_path
            except Exception as e:
                logger.error(f"Failed to generate image for {quant_level}/{prompt}: {e}")
                # We do not raise here; the main loop in main.py will handle OOM/SIGKILL
                # and skip this specific item, but we log the failure.
                level_results[prompt] = None
        
        all_results[quant_level] = level_results
        logger.info(f"Completed generation for {quant_level.upper()}. Saved to {output_dir}")
    
    return all_results