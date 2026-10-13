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

# New imports for deterministic seed‑locking and fallback handling
from generation.reference_geometry import (
    load_physics_constraint,
    render_reference_geometry
)

import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image

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
    Load the CPU‑optimized diffusion model (LCM‑LoRA).

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

        pipeline = DiffusionPipeline.from_pretrained(
            config.model_path,
            torch_dtype=torch.float32,  # CPU compatible
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
        data = json.load(f)
    # The manifest stores seeds under the top‑level key "seeds"
    return data.get("seeds", {})


def _pil_to_numpy(img: Image.Image) -> np.ndarray:
    """Convert a PIL image to a NumPy array suitable for SSIM."""
    arr = np.array(img.convert('L'))  # grayscale
    return arr


def _compute_ssim(img1: Image.Image, img2: Image.Image) -> float:
    """Compute Structural Similarity Index between two PIL images."""
    arr1 = _pil_to_numpy(img1)
    arr2 = _pil_to_numpy(img2)
    # Ensure same shape
    if arr1.shape != arr2.shape:
        raise ValueError("Images must have the same dimensions for SSIM calculation.")
    return ssim(arr1, arr2, data_range=arr1.max() - arr1.min())


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
    Generate a single image with timeout enforcement.

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
        Generated PIL Image.

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
    retry_delay: float = 5.0,
    fallback_candidate_count: int = 5
) -> Tuple[bool, str]:
    """
    Generate images for a specific scene, applying the fallback SSIM logic when needed.

    Returns a tuple ``(success, mode)`` where ``mode`` is either ``'exact'`` or ``'fallback'``.
    """
    if scene_id not in prompts:
        logger.error(f"No prompt found for scene {scene_id}")
        return False, "exact"

    if scene_id not in seed_manifest:
        logger.error(f"No seed entry for scene {scene_id}")
        return False, "exact"

    prompt = prompts[scene_id]
    seed_info = seed_manifest[scene_id]
    seed = seed_info.get(group, seed_info.get('baseline'))  # fallback to baseline

    if seed is None:
        logger.error(f"No seed found for group {group} in scene {scene_id}")
        return False, "exact"

    # Prepare output path
    group_dir = output_dir / group
    group_dir.mkdir(parents=True, exist_ok=True)
    output_file = group_dir / f"{scene_id}.png"

    # Load reference geometry (used for SSIM fallback)
    try:
        physics_json = load_physics_constraint(scene_id, constraints_dir=Path("data/derived/physics_constraints"))
        reference_image = render_reference_geometry(physics_json, size=(512, 512))
    except Exception as e:
        logger.warning(f"Could not render reference geometry for {scene_id}: {e}")
        reference_image = None  # fallback will just use the first candidate

    attempt = 0
    best_image = None
    best_score = -1.0
    mode = "exact"

    while attempt < max_retries:
        try:
            logger.info(f"Generating image for {scene_id} ({group}), attempt {attempt + 1}/{max_retries}")

            # If we have a reference image we try the SSIM fallback path
            if reference_image is not None:
                candidates = []
                for idx in range(fallback_candidate_count):
                    img = generate_single_image(
                        pipeline,
                        prompt,
                        seed,
                        timeout_seconds=600
                    )
                    candidates.append(img)

                # Compute SSIM scores
                for img in candidates:
                    try:
                        score = _compute_ssim(img, reference_image)
                    except Exception as ssim_err:
                        logger.debug(f"SSIM computation failed: {ssim_err}")
                        score = -1.0
                    if score > best_score:
                        best_score = score
                        best_image = img
                mode = "fallback"
            else:
                # No reference geometry – generate a single image (exact mode)
                best_image = generate_single_image(
                    pipeline,
                    prompt,
                    seed,
                    timeout_seconds=600
                )
                mode = "exact"

            # Save the selected image
            save_image(best_image, output_file, group, scene_id)
            logger.info(f"Successfully saved image to {output_file}")
            return True, mode

        except GenerationTimeoutError as e:
            logger.warning(f"Timeout on attempt {attempt + 1} for {scene_id}: {e}")
            attempt += 1
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Generation error on attempt {attempt + 1} for {scene_id}: {e}")
            attempt += 1
            time.sleep(retry_delay)

    logger.error(f"Failed to generate image for {scene_id} after {max_retries} attempts")
    return False, mode


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

    Returns a dictionary mapping scene_id -> group -> success status.
    Additionally writes ``seed_lock_status.json`` describing the mode used per scene.
    """
    logger.info("Starting diffusion generation pipeline...")

    # Load model
    pipeline = load_model(config)

    # Load prompts per group
    all_prompts: Dict[str, Dict[str, str]] = {}
    for group in groups:
        group_prompts = load_all_prompts(scene_ids, prompt_dir, group)
        all_prompts[group] = group_prompts

    # Load seed manifest
    seed_manifest = load_seed_manifest(seed_manifest_path)

    # Ensure output directories exist
    for group in groups:
        (output_dir / group).mkdir(parents=True, exist_ok=True)

    # Track results and seed‑lock status
    results: Dict[str, Dict[str, bool]] = {scene_id: {group: False for group in groups} for scene_id in scene_ids}
    seed_lock_status: Dict[str, Dict[str, str]] = {}

    for scene_id in scene_ids:
        seed_lock_status[scene_id] = {}
        for group in groups:
            if scene_id not in all_prompts.get(group, {}):
                logger.warning(f"Skipping {scene_id} ({group}): Prompt not found")
                continue

            success, mode = generate_images_for_scene(
                pipeline,
                scene_id,
                all_prompts[group],
                seed_manifest,
                output_dir,
                group,
                max_retries=max_retries
            )
            results[scene_id][group] = success
            seed_lock_status[scene_id][group] = mode

    # Write seed lock status JSON
    lock_status_path = output_dir.parent / "seed_lock_status.json"
    with open(lock_status_path, 'w', encoding='utf-8') as f:
        json.dump(seed_lock_status, f, indent=2)
    logger.info(f"Seed lock status written to {lock_status_path}")

    # Log generation failures
    failures = []
    for scene_id, group_map in results.items():
        for group, succeeded in group_map.items():
            if not succeeded:
                failures.append({
                    "scene_id": scene_id,
                    "group": group,
                    "reason": "Max retries exceeded"
                })

    failure_log_path = output_dir.parent / "generation_failure_log.json"
    with open(failure_log_path, 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2)
    if failures:
        logger.info(f"Logged {len(failures)} generation failures to {failure_log_path}")
    else:
        logger.info("No generation failures recorded.")

    return results


def main():
    """Main entry point for the diffusion runner."""
    config = Config()

    # Placeholder scene list – in real runs this will be derived from the CSV.
    scene_ids = ["scene_001", "scene_002"]
    groups = ["baseline", "experimental", "control"]
    prompt_dir = Path(config.paths.derived_prompts)
    seed_manifest_path = Path(config.paths.seed_manifest)
    output_dir = Path(config.paths.generated_images)

    run_diffusion_generation(
        config,
        scene_ids,
        groups,
        prompt_dir,
        seed_manifest_path,
        output_dir,
        max_retries=3
    )

    logger.info("Diffusion generation completed.")


if __name__ == "__main__":
    main()
