import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import from sibling modules based on provided API surface
from generation.image_saver import save_image, ImageSaveError
from generation.memory_monitor import TimeLimitEnforcer, MemoryLimitExceededError, TimeLimitExceededError
from generation.seed_manager import get_generation_seed
from setup.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    """Raised when image generation exceeds the time limit."""
    pass

def load_model(config: Config):
    """
    Load the CPU-optimized diffusion model (LCM-LoRA).
    
    Args:
        config: Configuration object containing model paths and settings.
        
    Returns:
        Loaded pipeline object.
        
    Raises:
        ModelLoadError: If model loading fails.
    """
    try:
        logger.info(f"Loading model: {config.model_path}")
        from diffusers import DiffusionPipeline, LCMScheduler
        import torch

        # Load the base model and LoRA
        pipeline = DiffusionPipeline.from_pretrained(
            config.model_path,
            torch_dtype=torch.float32, # CPU compatible
            safety_checker=None
        )
        
        # Load LoRA weights if specified
        if hasattr(config, 'lora_path') and config.lora_path:
            pipeline.load_lora_weights(config.lora_path)
        
        pipeline.scheduler = LCMScheduler.from_config(pipeline.scheduler.config)
        
        logger.info("Model loaded successfully.")
        return pipeline
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise ModelLoadError(f"Model loading failed: {str(e)}")

def load_prompt_file(prompt_path: Path) -> str:
    """
    Load a prompt from a text file.
    
    Args:
        prompt_path: Path to the prompt file.
        
    Returns:
        Prompt string.
        
    Raises:
        PromptFileNotFoundError: If file not found.
    """
    if not prompt_path.exists():
        raise PromptFileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def load_all_prompts(scene_ids: List[str], prompt_dir: Path, group: str) -> Dict[str, str]:
    """
    Load prompts for all scenes from a specific group directory.
    
    Args:
        scene_ids: List of scene IDs to load prompts for.
        prompt_dir: Directory containing prompt files.
        group: Group name (e.g., 'baseline', 'experimental', 'control').
        
    Returns:
        Dictionary mapping scene_id to prompt string.
    """
    prompts = {}
    for scene_id in scene_ids:
        prompt_file = prompt_dir / f"{scene_id}_{group}.txt"
        if prompt_file.exists():
            prompts[scene_id] = load_prompt_file(prompt_file)
        else:
            logger.warning(f"Prompt file not found for {scene_id}: {prompt_file}")
    return prompts

def load_seed_manifest(manifest_path: Path) -> Dict[str, Dict[str, int]]:
    """
    Load the seed manifest JSON.
    
    Args:
        manifest_path: Path to the seed manifest file.
        
    Returns:
        Dictionary mapping scene_id to seed info.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Seed manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_single_image(
    pipeline,
    prompt: str,
    seed: int,
    width: int = 512,
    height: int = 512,
    num_inference_steps: int = 4,
    guidance_scale: float = 1.0,
    timeout_seconds: int = 600
):
    """
    Generate a single image with retry logic and timeout enforcement.
    
    Args:
        pipeline: Loaded diffusion pipeline.
        prompt: Text prompt for generation.
        seed: Random seed for reproducibility.
        width: Image width.
        height: Image height.
        num_inference_steps: Number of inference steps.
        guidance_scale: Guidance scale for generation.
        timeout_seconds: Maximum time allowed for generation.
        
    Returns:
        Generated image object (PIL Image).
        
    Raises:
        GenerationTimeoutError: If generation times out.
        DiffusionGenerationError: If generation fails after retries.
    """
    import torch
    
    # Set seed
    generator = torch.Generator(device="cpu").manual_seed(seed)
    
    time_enforcer = TimeLimitEnforcer(timeout_seconds)
    
    try:
        with time_enforcer:
            image = pipeline(
                prompt=prompt,
                generator=generator,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale
            ).images[0]
        return image
    except TimeLimitExceededError:
        raise GenerationTimeoutError(f"Generation timed out after {timeout_seconds} seconds")

def generate_images_for_scene(
    pipeline,
    scene_id: str,
    prompts: Dict[str, str],
    seed_manifest: Dict[str, Dict[str, int]],
    output_dir: Path,
    group: str,
    max_retries: int = 3,
    retry_delay: float = 5.0
) -> bool:
    """
    Generate images for a specific scene with retry logic.
    
    Args:
        pipeline: Loaded diffusion pipeline.
        scene_id: Unique scene identifier.
        prompts: Dictionary of prompts for this scene.
        seed_manifest: Dictionary of seeds for this scene.
        output_dir: Directory to save generated images.
        group: Group name (baseline, experimental, control).
        max_retries: Maximum number of retry attempts.
        retry_delay: Delay between retries in seconds.
        
    Returns:
        True if generation succeeded, False if it failed after all retries.
    """
    if scene_id not in prompts:
        logger.error(f"No prompt found for scene {scene_id}")
        return False
    
    if scene_id not in seed_manifest:
        logger.error(f"No seed found for scene {scene_id}")
        return False
    
    prompt = prompts[scene_id]
    seed_info = seed_manifest[scene_id]
    seed = seed_info.get(group, seed_info.get('baseline')) # Fallback to baseline seed if group missing
    
    if seed is None:
        logger.error(f"No seed found for group {group} in scene {scene_id}")
        return False
    
    output_path = output_dir / group
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / f"{scene_id}.png"
    
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Generating image for {scene_id} ({group}), attempt {attempt + 1}/{max_retries}")
            image = generate_single_image(
                pipeline,
                prompt,
                seed,
                timeout_seconds=600 # 10 minutes per image
            )
            
            # Save the image
            save_image(image, output_file)
            logger.info(f"Successfully saved image to {output_file}")
            return True
            
        except GenerationTimeoutError as e:
            logger.warning(f"Timeout on attempt {attempt + 1} for {scene_id}: {e}")
            attempt += 1
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Generation error on attempt {attempt + 1} for {scene_id}: {e}")
            attempt += 1
            time.sleep(retry_delay)
    
    logger.error(f"Failed to generate image for {scene_id} after {max_retries} attempts")
    return False

def run_diffusion_generation(
    config: Config,
    scene_ids: List[str],
    groups: List[str],
    prompt_dir: Path,
    seed_manifest_path: Path,
    output_dir: Path,
    max_retries: int = 3
) -> Dict[str, Dict[str, bool]]:
    """
    Run the full diffusion generation pipeline for multiple scenes and groups.
    
    Args:
        config: Configuration object.
        scene_ids: List of scene IDs to process.
        groups: List of groups to generate (baseline, experimental, control).
        prompt_dir: Directory containing prompt files.
        seed_manifest_path: Path to the seed manifest.
        output_dir: Directory to save generated images.
        max_retries: Maximum retry attempts per image.
        
    Returns:
        Dictionary mapping scene_id -> group -> success status.
    """
    logger.info("Starting diffusion generation pipeline...")
    
    # Load model
    pipeline = load_model(config)
    
    # Load prompts
    all_prompts = {}
    for group in groups:
        group_prompts = load_all_prompts(scene_ids, prompt_dir, group)
        all_prompts[group] = group_prompts
    
    # Load seeds
    seed_manifest = load_seed_manifest(seed_manifest_path)
    
    # Ensure output directories exist
    for group in groups:
        (output_dir / group).mkdir(parents=True, exist_ok=True)
    
    # Track results
    results = {scene_id: {group: False for group in groups} for scene_id in scene_ids}
    failures = []
    
    for scene_id in scene_ids:
        for group in groups:
            # Check if prompt exists
            if scene_id not in all_prompts.get(group, {}):
                logger.warning(f"Skipping {scene_id} ({group}): Prompt not found")
                continue
            
            success = generate_images_for_scene(
                pipeline,
                scene_id,
                all_prompts[group],
                seed_manifest,
                output_dir,
                group,
                max_retries=max_retries
            )
            
            results[scene_id][group] = success
            
            if not success:
                failures.append({
                    "scene_id": scene_id,
                    "group": group,
                    "reason": "Max retries exceeded"
                })
    
    # Log failure log
    failure_log_path = output_dir.parent / "generation_failure_log.json"
    if failures:
        with open(failure_log_path, 'w', encoding='utf-8') as f:
            json.dump(failures, f, indent=2)
        logger.info(f"Logged {len(failures)} generation failures to {failure_log_path}")
    else:
        # Write empty log if no failures (for consistency)
        with open(failure_log_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
    
    return results

def main():
    """Main entry point for the diffusion runner."""
    config = Config()
    
    # Default parameters (can be overridden by CLI args in a full implementation)
    scene_ids = ["scene_001", "scene_002"] # Placeholder for actual list
    groups = ["baseline", "experimental", "control"]
    prompt_dir = Path(config.paths.derived_prompts)
    seed_manifest_path = Path(config.paths.seed_manifest)
    output_dir = Path(config.paths.generated_images)
    
    results = run_diffusion_generation(
        config,
        scene_ids,
        groups,
        prompt_dir,
        seed_manifest_path,
        output_dir,
        max_retries=3
    )
    
    success_count = sum(
        sum(1 for g in groups if results[s][g])
        for s in scene_ids
    )
    total = len(scene_ids) * len(groups)
    
    logger.info(f"Generation complete: {success_count}/{total} images generated successfully.")
    
    if success_count < total:
        sys.exit(1)

if __name__ == "__main__":
    main()