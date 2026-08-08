"""
Diffusion Runner for Image Generation (CPU-optimized).

Implements T018: Generate images for Baseline, Experimental, and Control groups
using the LCM-LoRA model with strict seed locking.

Dependencies:
- diffusers
- torch
- transformers
- PIL
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import torch
from PIL import Image
from diffusers import LCMScheduler, StableDiffusionPipeline
from transformers import logging as transformers_logging

# Project imports
from generation.seed_manager import SeedManager, get_generation_seed
from generation.image_saver import save_image, ImageSaveError
from generation.memory_monitor import (
    MemoryLimitExceededError,
    TimeLimitExceededError,
    get_memory_usage_mb,
    check_memory_limit,
    TimeLimitEnforcer,
    monitor_batch_generation
)

# Suppress transformers warnings
transformers_logging.set_verbosity_error()

# Constants
MODEL_ID = "latent-consistency/lcm-lora-sdv1-5"
BASELINE_GROUP = "baseline"
EXPERIMENTAL_GROUP = "experimental"
CONTROL_GROUP = "control"
GENERATION_GROUPS = [BASELINE_GROUP, EXPERIMENTAL_GROUP, CONTROL_GROUP]

# Configuration defaults
DEFAULT_IMAGE_SIZE = (512, 512)
DEFAULT_NUM_INFERENCE_STEPS = 4
DEFAULT_GUIDANCE_SCALE = 1.0
DEFAULT_MEMORY_LIMIT_MB = 12000
DEFAULT_TIME_LIMIT_SECONDS = 300
DEFAULT_MAX_RETRIES = 3

class DiffusionGenerationError(Exception):
    """Base exception for diffusion generation errors."""
    pass

class ModelLoadError(DiffusionGenerationError):
    """Raised when the diffusion model fails to load."""
    pass

class PromptFileNotFoundError(DiffusionGenerationError):
    """Raised when a required prompt file is not found."""
    pass

class GenerationTimeoutError(DiffusionGenerationError):
    """Raised when generation exceeds the time limit."""
    pass

def load_prompt_file(prompt_path: Path) -> List[Dict[str, Any]]:
    """
    Load prompts from a text file.
    
    Expected format: One prompt per line, or JSON lines.
    For this implementation, we assume simple text files with one prompt per line.
    Returns a list of dicts with 'scene_id' and 'prompt'.
    """
    if not prompt_path.exists():
        raise PromptFileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    prompts = []
    with open(prompt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                # Assume filename is derived from line or we need to parse it
                # Since T013/T013b output {scene_id}_{group}.txt, we need to extract scene_id
                # However, the file content is just the prompt text.
                # We'll assume the prompt file name contains the scene_id and group.
                # This function is called with the full path, so we can extract info from the path.
                prompts.append({
                    'prompt': line,
                    'source_file': str(prompt_path)
                })
    return prompts

def load_all_prompts(prompts_dir: Path) -> Dict[str, Dict[str, str]]:
    """
    Load all prompt files from the prompts directory.
    
    Returns a dict: {scene_id: {group: prompt_text}}
    """
    scene_prompts = {}
    
    # Expected files: {scene_id}_{group}.txt
    for group in GENERATION_GROUPS:
        pattern = f"*_{group}.txt"
        for prompt_file in prompts_dir.glob(pattern):
            # Extract scene_id from filename: {scene_id}_{group}.txt
            stem = prompt_file.stem
            parts = stem.rsplit('_', 1)
            if len(parts) != 2:
                continue
            scene_id, file_group = parts
            if file_group != group:
                continue
            
            if scene_id not in scene_prompts:
                scene_prompts[scene_id] = {}
            
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_text = f.read().strip()
                scene_prompts[scene_id][group] = prompt_text
            except Exception as e:
                print(f"Warning: Could not read prompt file {prompt_file}: {e}")
    
    return scene_prompts

def load_model(model_id: str, device: str = "cpu") -> Tuple[Any, Any]:
    """
    Load the CPU-optimized diffusion model.
    
    Returns: (pipeline, scheduler)
    """
    try:
        # Load pipeline
        print(f"Loading model: {model_id}")
        pipeline = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # CPU uses float32
            safety_checker=None,  # Disable safety checker for speed
            requires_safety_checker=False
        )
        
        # Set to CPU
        pipeline = pipeline.to(device)
        
        # Use LCM scheduler
        pipeline.scheduler = LCMScheduler.from_config(pipeline.scheduler.config)
        
        # Enable memory optimizations for CPU
        pipeline.enable_attention_slicing()
        
        print("Model loaded successfully")
        return pipeline, pipeline.scheduler
        
    except Exception as e:
        raise ModelLoadError(f"Failed to load model {model_id}: {e}")

def generate_single_image(
    pipeline: Any,
    prompt: str,
    seed: int,
    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE,
    num_inference_steps: int = DEFAULT_NUM_INFERENCE_STEPS,
    guidance_scale: float = DEFAULT_GUIDANCE_SCALE,
    time_limit: int = DEFAULT_TIME_LIMIT_SECONDS
) -> Optional[Image.Image]:
    """
    Generate a single image with the given prompt and seed.
    
    Returns: PIL Image or None if generation failed.
    """
    try:
        # Set seed
        generator = torch.Generator(device=pipeline.device).manual_seed(seed)
        
        # Generate
        with torch.no_grad():
            result = pipeline(
                prompt=prompt,
                generator=generator,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                height=image_size[1],
                width=image_size[0]
            )
        
        return result.images[0]
        
    except Exception as e:
        print(f"Generation failed for prompt: {e}")
        return None

def generate_images_for_scene(
    pipeline: Any,
    scene_id: str,
    scene_prompts: Dict[str, str],
    output_dir: Path,
    seed_manager: SeedManager
) -> Dict[str, str]:
    """
    Generate images for all groups for a single scene.
    
    Returns: {group: output_path}
    """
    results = {}
    
    for group in GENERATION_GROUPS:
        if group not in scene_prompts:
            print(f"Warning: No prompt found for scene {scene_id}, group {group}")
            continue
        
        prompt = scene_prompts[group]
        
        # Get seed for this scene/group
        if group in [BASELINE_GROUP, EXPERIMENTAL_GROUP]:
            # Baseline and Experimental share the same seed
            seed = seed_manager.get_baseline_experimental_seeds(scene_id)
        else:
            # Control group has its own seed
            seed = seed_manager.get_generation_seed(scene_id, group)
        
        output_path = output_dir / group / f"{scene_id}.png"
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate with retry logic
        success = False
        for attempt in range(DEFAULT_MAX_RETRIES):
            try:
                image = generate_single_image(
                    pipeline=pipeline,
                    prompt=prompt,
                    seed=seed,
                    time_limit=DEFAULT_TIME_LIMIT_SECONDS
                )
                
                if image is not None:
                    save_image(image, output_path)
                    results[group] = str(output_path)
                    success = True
                    print(f"Generated: {output_path} (seed={seed}, attempt={attempt+1})")
                    break
                else:
                    print(f"Attempt {attempt+1} failed for {scene_id}/{group}")
                    
            except Exception as e:
                print(f"Attempt {attempt+1} failed with exception: {e}")
                continue
        
        if not success:
            print(f"Failed to generate image for {scene_id}/{group} after {DEFAULT_MAX_RETRIES} attempts")
            # Log failure but continue with other scenes
            failure_log = output_dir.parent / "generation_failures.json"
            failures = []
            if failure_log.exists():
                with open(failure_log, 'r') as f:
                    failures = json.load(f)
            failures.append({
                "scene_id": scene_id,
                "group": group,
                "prompt": prompt,
                "seed": seed,
                "error": "Generation failed after max retries"
            })
            with open(failure_log, 'w') as f:
                json.dump(failures, f, indent=2)
    
    return results

def run_diffusion_generation(
    prompts_dir: Path,
    output_base_dir: Path,
    model_id: str = MODEL_ID,
    device: str = "cpu",
    memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
    time_limit_per_batch: int = DEFAULT_TIME_LIMIT_SECONDS
) -> Dict[str, Any]:
    """
    Main function to run the diffusion generation pipeline.
    
    Args:
        prompts_dir: Path to directory containing prompt files
        output_base_dir: Base path for output images
        model_id: HuggingFace model ID
        device: Device to use ('cpu' or 'cuda')
        memory_limit_mb: Maximum memory usage in MB
        time_limit_per_batch: Time limit per batch in seconds
    
    Returns:
        Dict with generation statistics
    """
    print("=" * 60)
    print("DIFFUSION GENERATION PIPELINE")
    print("=" * 60)
    
    # Load prompts
    print(f"\nLoading prompts from: {prompts_dir}")
    scene_prompts = load_all_prompts(prompts_dir)
    
    if not scene_prompts:
        raise PromptFileNotFoundError(f"No prompt files found in {prompts_dir}")
    
    print(f"Found {len(scene_prompts)} scenes with prompts")
    
    # Initialize seed manager
    seed_manager = SeedManager()
    
    # Load model
    print(f"\nLoading model: {model_id}")
    pipeline, scheduler = load_model(model_id, device)
    
    # Create output directories
    output_dir = Path(output_base_dir) / "generated_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    stats = {
        "total_scenes": len(scene_prompts),
        "successful_scenes": 0,
        "failed_scenes": 0,
        "groups_generated": {group: 0 for group in GENERATION_GROUPS},
        "total_images": 0,
        "start_time": time.time(),
        "end_time": None,
        "duration_seconds": None
    }
    
    # Generate images
    print(f"\nGenerating images for {len(scene_prompts)} scenes...")
    print(f"Output directory: {output_dir}")
    
    for scene_id, prompts in scene_prompts.items():
        print(f"\nProcessing scene: {scene_id}")
        
        # Check memory
        try:
            check_memory_limit(memory_limit_mb)
        except MemoryLimitExceededError as e:
            print(f"Memory limit exceeded: {e}")
            stats["failed_scenes"] += 1
            continue
        
        # Generate for this scene
        results = generate_images_for_scene(
            pipeline=pipeline,
            scene_id=scene_id,
            scene_prompts=prompts,
            output_dir=output_dir,
            seed_manager=seed_manager
        )
        
        if results:
            stats["successful_scenes"] += 1
            for group, path in results.items():
                stats["groups_generated"][group] += 1
                stats["total_images"] += 1
        else:
            stats["failed_scenes"] += 1
    
    # Finalize statistics
    stats["end_time"] = time.time()
    stats["duration_seconds"] = stats["end_time"] - stats["start_time"]
    
    # Save statistics
    stats_file = output_dir / "generation_statistics.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"Total scenes: {stats['total_scenes']}")
    print(f"Successful: {stats['successful_scenes']}")
    print(f"Failed: {stats['failed_scenes']}")
    print(f"Total images: {stats['total_images']}")
    print(f"Duration: {stats['duration_seconds']:.2f} seconds")
    print(f"Output: {output_dir}")
    print("=" * 60)
    
    return stats

def main():
    """CLI entry point for diffusion generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate images using diffusion model")
    parser.add_argument(
        "--prompts-dir",
        type=str,
        default="data/derived/prompts",
        help="Path to directory containing prompt files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/derived",
        help="Base output directory for generated images"
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default=MODEL_ID,
        help="HuggingFace model ID"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use for generation"
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=DEFAULT_MEMORY_LIMIT_MB,
        help="Memory limit in MB"
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=DEFAULT_TIME_LIMIT_SECONDS,
        help="Time limit per batch in seconds"
    )
    
    args = parser.parse_args()
    
    try:
        run_diffusion_generation(
            prompts_dir=Path(args.prompts_dir),
            output_base_dir=Path(args.output_dir),
            model_id=args.model_id,
            device=args.device,
            memory_limit_mb=args.memory_limit,
            time_limit_per_batch=args.time_limit
        )
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
