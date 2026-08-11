import os
import torch
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

from config import load_config
from data_loader import load_adapter_weights, get_collection_lora_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _ensure_device():
    """Select CPU or CUDA device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")

def generate_reference_image(output_path: str) -> str:
    """
    Generate a single 'known reference' image using a fixed seed from config.yaml.
    This image serves as the ground truth for LPIPS self-consistency checks.

    Args:
        output_path: Path where the generated image will be saved.

    Returns:
        Path to the saved image.
    """
    config = load_config()
    seed = config.get("seed", 42)
    prompt = config.get("reference_prompt", "a high quality photograph of a cat")
    base_model_id = config.get("base_model_id", "runwayml/stable-diffusion-v1-5")
    adapter_path = config.get("adapter_path", "data/models/adapter_fp16.safetensors")
    num_steps = config.get("num_inference_steps", 50)
    guidance = config.get("guidance_scale", 7.5)
    width = config.get("image_width", 512)
    height = config.get("image_height", 512)

    device = _ensure_device()
    logger.info(f"Using device: {device}")

    # Load base model
    logger.info(f"Loading base model: {base_model_id}")
    from diffusers import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe = pipe.to(device)

    # Load LoRA adapter
    logger.info(f"Loading adapter: {adapter_path}")
    adapter_weights = load_adapter_weights(adapter_path)
    pipe.load_lora_weights(adapter_weights)
    pipe.set_adapters(["default"])

    # Set seed for reproducibility
    generator = torch.Generator(device=device).manual_seed(seed)

    logger.info(f"Generating reference image with prompt: '{prompt}' (seed={seed})")
    image = pipe(
        prompt=prompt,
        generator=generator,
        num_inference_steps=num_steps,
        guidance_scale=guidance,
        width=width,
        height=height
    ).images[0]

    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    # Save image
    image.save(output_path)
    logger.info(f"Reference image saved to: {output_path}")

    return output_path

def generate_fp16_baseline_images(output_dir: str) -> List[str]:
    """
    Generate images using the fixed prompt list from config.yaml with FP16 adapter.
    Used for baseline fidelity measurement.

    Args:
        output_dir: Directory where generated images will be saved.

    Returns:
        List of paths to saved images.
    """
    config = load_config()
    prompts = config.get("effect_prompts", [])
    base_model_id = config.get("base_model_id", "runwayml/stable-diffusion-v1-5")
    adapter_path = config.get("adapter_path", "data/models/adapter_fp16.safetensors")
    num_steps = config.get("num_inference_steps", 50)
    guidance = config.get("guidance_scale", 7.5)
    width = config.get("image_width", 512)
    height = config.get("image_height", 512)

    device = _ensure_device()
    logger.info(f"Using device: {device}")

    # Load base model
    logger.info(f"Loading base model: {base_model_id}")
    from diffusers import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe = pipe.to(device)

    # Load LoRA adapter
    logger.info(f"Loading adapter: {adapter_path}")
    adapter_weights = load_adapter_weights(adapter_path)
    pipe.load_lora_weights(adapter_weights)
    pipe.set_adapters(["default"])

    output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for i, prompt in enumerate(prompts):
        logger.info(f"Generating baseline image {i+1}/{len(prompts)}: '{prompt}'")
        # Use a deterministic seed based on index for reproducibility
        generator = torch.Generator(device=device).manual_seed(42 + i)
        image = pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=num_steps,
            guidance_scale=guidance,
            width=width,
            height=height
        ).images[0]

        filename = f"baseline_{i:03d}.png"
        filepath = output_dir_obj / filename
        image.save(filepath)
        saved_paths.append(str(filepath))

    return saved_paths

def generate_fp16_reference_images(output_dir: str) -> Dict[str, str]:
    """
    Generate and save a set of 'FP16 Reference Images' for all effect prompts.
    Required for CESR calculation in US2.

    Args:
        output_dir: Directory where reference images will be saved.

    Returns:
        Dictionary mapping prompt text to saved image path.
    """
    config = load_config()
    prompts = config.get("effect_prompts", [])
    base_model_id = config.get("base_model_id", "runwayml/stable-diffusion-v1-5")
    adapter_path = config.get("adapter_path", "data/models/adapter_fp16.safetensors")
    num_steps = config.get("num_inference_steps", 50)
    guidance = config.get("guidance_scale", 7.5)
    width = config.get("image_width", 512)
    height = config.get("image_height", 512)

    device = _ensure_device()
    logger.info(f"Using device: {device}")

    # Load base model
    logger.info(f"Loading base model: {base_model_id}")
    from diffusers import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe = pipe.to(device)

    # Load LoRA adapter
    logger.info(f"Loading adapter: {adapter_path}")
    adapter_weights = load_adapter_weights(adapter_path)
    pipe.load_lora_weights(adapter_weights)
    pipe.set_adapters(["default"])

    output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(parents=True, exist_ok=True)

    results = {}
    for i, prompt in enumerate(prompts):
        logger.info(f"Generating FP16 reference for prompt: '{prompt}'")
        generator = torch.Generator(device=device).manual_seed(100 + i)
        image = pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=num_steps,
            guidance_scale=guidance,
            width=width,
            height=height
        ).images[0]

        # Sanitize filename
        safe_prompt = prompt.replace(" ", "_").replace(":", "_")[:50]
        filename = f"ref_{safe_prompt}.png"
        filepath = output_dir_obj / filename
        image.save(filepath)
        results[prompt] = str(filepath)

    return results

def generate_images_for_adapters(adapter_paths: Dict[str, str], output_dir: str) -> Dict[str, List[str]]:
    """
    Generate images for multiple adapters (e.g., INT8, INT4) using the prompt list.

    Args:
        adapter_paths: Dictionary mapping adapter name to path.
        output_dir: Directory where generated images will be saved.

    Returns:
        Dictionary mapping adapter name to list of saved image paths.
    """
    config = load_config()
    prompts = config.get("effect_prompts", [])
    base_model_id = config.get("base_model_id", "runwayml/stable-diffusion-v1-5")
    num_steps = config.get("num_inference_steps", 50)
    guidance = config.get("guidance_scale", 7.5)
    width = config.get("image_width", 512)
    height = config.get("image_height", 512)

    device = _ensure_device()

    output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for adapter_name, adapter_path in adapter_paths.items():
        logger.info(f"Processing adapter: {adapter_name} ({adapter_path})")

        # Load base model
        logger.info(f"Loading base model: {base_model_id}")
        from diffusers import StableDiffusionPipeline
        pipe = StableDiffusionPipeline.from_pretrained(
            base_model_id,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            safety_checker=None,
            requires_safety_checker=False
        )
        pipe = pipe.to(device)

        # Load LoRA adapter
        logger.info(f"Loading adapter: {adapter_path}")
        adapter_weights = load_adapter_weights(adapter_path)
        pipe.load_lora_weights(adapter_weights)
        pipe.set_adapters(["default"])

        saved_paths = []
        for i, prompt in enumerate(prompts):
            logger.info(f"Generating image for '{prompt}' with {adapter_name}")
            generator = torch.Generator(device=device).manual_seed(200 + i)
            image = pipe(
                prompt=prompt,
                generator=generator,
                num_inference_steps=num_steps,
                guidance_scale=guidance,
                width=width,
                height=height
            ).images[0]

            safe_prompt = prompt.replace(" ", "_").replace(":", "_")[:40]
            filename = f"{adapter_name}_{i:03d}_{safe_prompt}.png"
            filepath = output_dir_obj / filename
            image.save(filepath)
            saved_paths.append(str(filepath))

        all_results[adapter_name] = saved_paths

    return all_results

def generate_images(prompts: List[str], adapter_path: str, output_dir: str, seed_offset: int = 0) -> List[str]:
    """
    Generic image generation function for a list of prompts and a single adapter.

    Args:
        prompts: List of prompts to generate images for.
        adapter_path: Path to the LoRA adapter.
        output_dir: Directory to save images.
        seed_offset: Offset added to the base seed (42) for each prompt.

    Returns:
        List of paths to saved images.
    """
    config = load_config()
    base_model_id = config.get("base_model_id", "runwayml/stable-diffusion-v1-5")
    num_steps = config.get("num_inference_steps", 50)
    guidance = config.get("guidance_scale", 7.5)
    width = config.get("image_width", 512)
    height = config.get("image_height", 512)
    base_seed = config.get("seed", 42)

    device = _ensure_device()

    logger.info(f"Loading base model: {base_model_id}")
    from diffusers import StableDiffusionPipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_id,
        torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe = pipe.to(device)

    logger.info(f"Loading adapter: {adapter_path}")
    adapter_weights = load_adapter_weights(adapter_path)
    pipe.load_lora_weights(adapter_weights)
    pipe.set_adapters(["default"])

    output_dir_obj = Path(output_dir)
    output_dir_obj.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for i, prompt in enumerate(prompts):
        generator = torch.Generator(device=device).manual_seed(base_seed + seed_offset + i)
        image = pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=num_steps,
            guidance_scale=guidance,
            width=width,
            height=height
        ).images[0]

        filename = f"gen_{i:03d}.png"
        filepath = output_dir_obj / filename
        image.save(filepath)
        saved_paths.append(str(filepath))

    return saved_paths