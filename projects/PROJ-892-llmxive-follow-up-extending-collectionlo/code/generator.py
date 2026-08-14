import os
import torch
from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

from config import load_config
from data_loader import get_collection_lora_adapter, download_base_model
from state_manager import register_artifact, compute_sha256

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for generation
DEVICE = "cpu"
DTYPE = torch.float16
STABILITY_MODEL_ID = "runwayml/stable-diffusion-v1-5"

def _ensure_references_dir():
    """Ensure the references directory exists."""
    ref_dir = Path("data/references")
    ref_dir.mkdir(parents=True, exist_ok=True)
    return ref_dir

def generate_reference_image(seed: int = 42, prompt: str = "a simple test object", output_path: Optional[str] = None) -> str:
    """
    Generate a single 'known reference' image using a fixed seed and prompt.
    This image serves as ground truth for LPIPS self-consistency checks.

    Args:
        seed: Random seed for reproducibility.
        prompt: The text prompt to generate the image.
        output_path: Optional path to save the image. Defaults to 'data/references/baseline_ref.png'.

    Returns:
        Path to the saved image.
    """
    if output_path is None:
        output_path = "data/references/baseline_ref.png"
    
    output_path = Path(output_path)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating reference image with seed={seed}, prompt='{prompt}'")
    
    # Load base model
    logger.info("Loading base model...")
    base_model_path = download_base_model(STABILITY_MODEL_ID)
    
    # Load LoRA adapter (FP16)
    logger.info("Loading LoRA adapter...")
    adapter_path = get_collection_lora_adapter()

    # Import diffusers here to avoid circular imports if any
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    from safetensors.torch import load_file

    # Load the pipeline
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_path,
        torch_dtype=DTYPE,
        safety_checker=None, # Disable safety checker for research consistency
        requires_safety_checker=False
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(DEVICE)

    # Load LoRA weights
    # The adapter file is expected to be at data/models/adapter_fp16.safetensors
    # based on T007b-1 and T007b-2 requirements.
    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter file not found at {adapter_path}. Ensure T007b-1 is complete.")
    
    logger.info(f"Loading LoRA weights from {adapter_path}")
    lora_state_dict = load_file(adapter_path)
    pipe.load_lora_weights(lora_state_dict)
    
    # Set seed
    generator = torch.Generator(device=DEVICE).manual_seed(seed)

    # Generate image
    with torch.no_grad():
        image = pipe(
            prompt=prompt,
            generator=generator,
            num_inference_steps=30,
            height=512,
            width=512
        ).images[0]

    # Save image
    image.save(output_path)
    logger.info(f"Reference image saved to {output_path}")

    # Register artifact in state manager
    artifact_hash = compute_sha256(output_path)
    register_artifact(
        path=str(output_path),
        hash=artifact_hash,
        type="image",
        description=f"Reference image: seed={seed}, prompt='{prompt}'"
    )

    return str(output_path)

def generate_fp16_baseline_images(prompts: List[str], seeds: List[int], output_dir: str = "data/generated/fp16_baseline") -> List[str]:
    """
    Generate images for the FP16 baseline using the provided prompts and seeds.
    This is the main generation function for US1.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Loading base model and adapter for FP16 baseline generation...")
    base_model_path = download_base_model(STABILITY_MODEL_ID)
    adapter_path = get_collection_lora_adapter()

    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    from safetensors.torch import load_file

    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_path,
        torch_dtype=DTYPE,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(DEVICE)

    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter file not found at {adapter_path}.")
    
    lora_state_dict = load_file(adapter_path)
    pipe.load_lora_weights(lora_state_dict)

    generated_paths = []
    
    for i, (prompt, seed) in enumerate(zip(prompts, seeds)):
        logger.info(f"Generating image {i+1}/{len(prompts)}: seed={seed}, prompt='{prompt}'")
        generator = torch.Generator(device=DEVICE).manual_seed(seed)
        
        with torch.no_grad():
            image = pipe(
                prompt=prompt,
                generator=generator,
                num_inference_steps=30,
                height=512,
                width=512
            ).images[0]
        
        file_name = f"fp16_baseline_{i:04d}_seed{seed}.png"
        save_path = output_path / file_name
        image.save(save_path)
        generated_paths.append(str(save_path))
        
        # Register artifact
        artifact_hash = compute_sha256(save_path)
        register_artifact(
            path=str(save_path),
            hash=artifact_hash,
            type="image",
            description=f"FP16 Baseline: seed={seed}, prompt='{prompt}'"
        )

    return generated_paths

def generate_fp16_reference_images(prompts: List[str], seeds: List[int], output_dir: str = "data/references/fp16_refs") -> Dict[str, str]:
    """
    Generate a set of 'FP16 Reference Images' for ALL effect prompts.
    These are required for CESR calculation in US2.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Generating FP16 Reference Images for all effect prompts...")
    
    # Re-use the logic from generate_fp16_baseline_images but organize by prompt
    base_model_path = download_base_model(STABILITY_MODEL_ID)
    adapter_path = get_collection_lora_adapter()

    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    from safetensors.torch import load_file

    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_path,
        torch_dtype=DTYPE,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(DEVICE)

    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter file not found at {adapter_path}.")
    
    lora_state_dict = load_file(adapter_path)
    pipe.load_lora_weights(lora_state_dict)

    ref_map = {} # prompt -> path

    for i, (prompt, seed) in enumerate(zip(prompts, seeds)):
        logger.info(f"Generating reference for prompt '{prompt}' (seed={seed})")
        generator = torch.Generator(device=DEVICE).manual_seed(seed)
        
        with torch.no_grad():
            image = pipe(
                prompt=prompt,
                generator=generator,
                num_inference_steps=30,
                height=512,
                width=512
            ).images[0]
        
        # Sanitize prompt for filename
        safe_prompt = "".join(c if c.isalnum() or c in " -_" else "_" for c in prompt)[:50]
        file_name = f"ref_{safe_prompt}_seed{seed}.png"
        save_path = output_path / file_name
        image.save(save_path)
        
        ref_map[prompt] = str(save_path)

        # Register artifact
        artifact_hash = compute_sha256(save_path)
        register_artifact(
            path=str(save_path),
            hash=artifact_hash,
            type="image",
            description=f"FP16 Reference: seed={seed}, prompt='{prompt}'"
        )

    return ref_map

def generate_images_for_adapters(adapter_paths: Dict[str, str], prompts: List[str], seeds: List[int], output_dir: str = "data/generated") -> List[Dict[str, str]]:
    """
    Generate images for a list of adapters (e.g., INT8, INT4) using the same prompts.
    Returns a list of dicts mapping adapter_name -> generated_path.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_model_path = download_base_model(STABILITY_MODEL_ID)

    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
    from safetensors.torch import load_file

    results = []

    for adapter_name, adapter_path in adapter_paths.items():
        logger.info(f"Processing adapter: {adapter_name} ({adapter_path})")
        
        if not Path(adapter_path).exists():
            logger.error(f"Adapter {adapter_path} not found. Skipping.")
            continue

        pipe = StableDiffusionPipeline.from_pretrained(
            base_model_path,
            torch_dtype=DTYPE,
            safety_checker=None,
            requires_safety_checker=False
        )
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe = pipe.to(DEVICE)

        # Load adapter weights
        try:
            lora_state_dict = load_file(adapter_path)
            pipe.load_lora_weights(lora_state_dict)
        except Exception as e:
            logger.error(f"Failed to load weights for {adapter_name}: {e}")
            continue

        adapter_results = {"adapter": adapter_name, "images": []}

        for i, (prompt, seed) in enumerate(zip(prompts, seeds)):
            generator = torch.Generator(device=DEVICE).manual_seed(seed)
            
            with torch.no_grad():
                image = pipe(
                    prompt=prompt,
                    generator=generator,
                    num_inference_steps=30,
                    height=512,
                    width=512
                ).images[0]
            
            safe_prompt = "".join(c if c.isalnum() or c in " -_" else "_" for c in prompt)[:50]
            file_name = f"{adapter_name}_{i:04d}_{safe_prompt}_seed{seed}.png"
            save_path = output_path / file_name
            image.save(save_path)
            
            adapter_results["images"].append({
                "prompt": prompt,
                "seed": seed,
                "path": str(save_path)
            })
            
            artifact_hash = compute_sha256(save_path)
            register_artifact(
                path=str(save_path),
                hash=artifact_hash,
                type="image",
                description=f"Generated for {adapter_name}: seed={seed}, prompt='{prompt}'"
            )
        
        results.append(adapter_results)

    return results

def generate_images(prompts: List[str], seeds: List[int], adapter_path: Optional[str] = None, output_dir: str = "data/generated") -> List[str]:
    """
    Generic generation function. If adapter_path is provided, loads it; otherwise uses base model.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_model_path = download_base_model(STABILITY_MODEL_ID)

    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

    pipe = StableDiffusionPipeline.from_pretrained(
        base_model_path,
        torch_dtype=DTYPE,
        safety_checker=None,
        requires_safety_checker=False
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(DEVICE)

    if adapter_path and Path(adapter_path).exists():
        from safetensors.torch import load_file
        lora_state_dict = load_file(adapter_path)
        pipe.load_lora_weights(lora_state_dict)
        logger.info(f"Loaded adapter from {adapter_path}")

    generated_paths = []
    for i, (prompt, seed) in enumerate(zip(prompts, seeds)):
        generator = torch.Generator(device=DEVICE).manual_seed(seed)
        
        with torch.no_grad():
            image = pipe(
                prompt=prompt,
                generator=generator,
                num_inference_steps=30,
                height=512,
                width=512
            ).images[0]
        
        file_name = f"gen_{i:04d}_seed{seed}.png"
        save_path = output_path / file_name
        image.save(save_path)
        generated_paths.append(str(save_path))
        
        artifact_hash = compute_sha256(save_path)
        register_artifact(
            path=str(save_path),
            hash=artifact_hash,
            type="image",
            description=f"Generic generation: seed={seed}, prompt='{prompt}'"
        )

    return generated_paths
