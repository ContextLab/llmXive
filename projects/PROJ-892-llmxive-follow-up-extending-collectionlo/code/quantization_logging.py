"""
Quantization Logging and Hash Verification Module (T022)

This module implements the logging and verification logic for User Story 2.
It logs quantization steps and verifies SHA-256 hashes of quantized weights
and generated images as required by FR-013 and T022.

Dependencies:
- data_loader: apply_quantization, quantize_adapter_fp16_to_int8, quantize_adapter_fp16_to_int4
- generator: generate_images_for_adapters
- state_manager: compute_sha256, register_artifact, save_artifacts_state, load_artifacts_state
- config: loaded via main.py or direct load_config
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

from data_loader import (
    apply_quantization,
    quantize_adapter_fp16_to_int8,
    quantize_adapter_fp16_to_int4
)
from generator import generate_images_for_adapters
from state_manager import (
    compute_sha256,
    register_artifact,
    save_artifacts_state,
    load_artifacts_state,
    ensure_state_dir
)

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def verify_artifact_hash(artifact_path: Path, expected_hash: Optional[str] = None) -> Tuple[bool, str]:
    """
    Compute SHA-256 hash of an artifact and optionally verify against expected hash.

    Args:
        artifact_path: Path to the artifact file
        expected_hash: Optional expected hash for verification

    Returns:
        Tuple of (is_valid, computed_hash)
    """
    if not artifact_path.exists():
        logger.error(f"Artifact not found: {artifact_path}")
        return False, ""

    computed_hash = compute_sha256(artifact_path)
    
    if expected_hash:
        is_valid = computed_hash == expected_hash
        if not is_valid:
            logger.error(f"Hash mismatch for {artifact_path}: expected {expected_hash}, got {computed_hash}")
        else:
            logger.info(f"Hash verified for {artifact_path}")
    else:
        logger.info(f"Computed hash for {artifact_path}: {computed_hash}")
    
    return True if not expected_hash else is_valid, computed_hash

def log_quantization_step(
    source_adapter: Path,
    quantized_adapter: Path,
    quantization_type: str
) -> None:
    """
    Log the quantization step from source to quantized adapter.

    Args:
        source_adapter: Path to source FP16 adapter
        quantized_adapter: Path to quantized adapter
        quantization_type: Type of quantization (e.g., 'INT8', 'INT4')
    """
    logger.info(f"Starting {quantization_type} quantization")
    logger.info(f"Source adapter: {source_adapter}")
    logger.info(f"Target adapter: {quantized_adapter}")
    
    if not source_adapter.exists():
        raise FileNotFoundError(f"Source adapter not found: {source_adapter}")
    
    source_hash = compute_sha256(source_adapter)
    logger.info(f"Source adapter SHA-256: {source_hash}")

def log_quantized_generation(
    adapter_path: Path,
    generated_images_dir: Path,
    prompt_list: List[str],
    quantization_type: str
) -> List[Dict[str, Any]]:
    """
    Log the generation process for a quantized adapter and verify image hashes.

    Args:
        adapter_path: Path to the quantized adapter
        generated_images_dir: Directory where images will be saved
        prompt_list: List of prompts used for generation
        quantization_type: Type of quantization (e.g., 'INT8', 'INT4')

    Returns:
        List of dictionaries containing image paths and their hashes
    """
    logger.info(f"Generating images for {quantization_type} adapter")
    logger.info(f"Adapter path: {adapter_path}")
    logger.info(f"Output directory: {generated_images_dir}")
    logger.info(f"Number of prompts: {len(prompt_list)}")

    # Ensure output directory exists
    generated_images_dir.mkdir(parents=True, exist_ok=True)

    # Generate images
    generate_images_for_adapters(
        adapter_path=adapter_path,
        output_dir=generated_images_dir,
        prompts=prompt_list
    )

    # Verify and log hashes for all generated images
    image_hashes = []
    for img_file in generated_images_dir.glob("*.png"):
        is_valid, img_hash = verify_artifact_hash(img_file)
        if is_valid:
            image_hashes.append({
                "path": str(img_file),
                "hash": img_hash,
                "quantization_type": quantization_type
            })
            logger.info(f"Verified image: {img_file.name}, hash: {img_hash[:16]}...")
        else:
            logger.warning(f"Failed to verify image: {img_file.name}")

    return image_hashes

def register_quantized_artifacts(
    quantized_adapter_path: Path,
    image_hashes: List[Dict[str, Any]],
    quantization_type: str
) -> None:
    """
    Register quantized adapter and generated images in state/artifacts.yaml.

    Args:
        quantized_adapter_path: Path to quantized adapter
        image_hashes: List of image hash dictionaries
        quantization_type: Type of quantization
    """
    ensure_state_dir()
    state = load_artifacts_state()

    # Register quantized adapter
    adapter_hash = compute_sha256(quantized_adapter_path)
    register_artifact(
        state,
        name=f"adapter_{quantization_type.lower()}",
        path=str(quantized_adapter_path),
        hash=adapter_hash,
        type="quantized_adapter"
    )
    logger.info(f"Registered {quantization_type} adapter: {adapter_hash[:16]}...")

    # Register generated images
    for img_info in image_hashes:
        register_artifact(
            state,
            name=f"image_{quantization_type.lower()}_{Path(img_info['path']).stem}",
            path=img_info['path'],
            hash=img_info['hash'],
            type="generated_image",
            metadata={"quantization_type": quantization_type}
        )

    save_artifacts_state(state)
    logger.info(f"Updated state/artifacts.yaml with {len(image_hashes) + 1} artifacts")

def run_quantization_pipeline(
    config_path: Path,
    base_adapter_path: Path,
    quantization_types: List[str] = None
) -> Dict[str, Any]:
    """
    Run the full quantization pipeline with logging and verification.

    Args:
        config_path: Path to config.yaml
        base_adapter_path: Path to base FP16 adapter
        quantization_types: List of quantization types to apply (default: ['INT8', 'INT4'])

    Returns:
        Dictionary containing pipeline results and artifact hashes
    """
    if quantization_types is None:
        quantization_types = ['INT8', 'INT4']

    config = load_config(config_path)
    prompt_list = config.get('effect_prompts', [])

    results = {
        "quantization_steps": [],
        "artifacts": []
    }

    for q_type in quantization_types:
        logger.info(f"{'='*60}")
        logger.info(f"Processing {q_type} quantization")
        logger.info(f"{'='*60}")

        # Determine target path
        if q_type == 'INT8':
            quantize_func = quantize_adapter_fp16_to_int8
            target_path = Path("data/quantized/adapter_int8.safetensors")
        elif q_type == 'INT4':
            quantize_func = quantize_adapter_fp16_to_int4
            target_path = Path("data/quantized/adapter_int4.safetensors")
        else:
            logger.warning(f"Unknown quantization type: {q_type}, skipping")
            continue

        # Ensure quantization directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Log quantization step
        log_quantization_step(
            source_adapter=base_adapter_path,
            quantized_adapter=target_path,
            quantization_type=q_type
        )

        # Apply quantization
        logger.info(f"Applying {q_type} quantization...")
        quantize_func(
            source_path=base_adapter_path,
            target_path=target_path
        )

        # Verify quantized adapter hash
        adapter_valid, adapter_hash = verify_artifact_hash(target_path)
        if not adapter_valid:
            logger.error(f"Quantized adapter verification failed for {q_type}")
            continue

        # Generate images
        images_dir = Path(f"data/generated/{q_type.lower()}")
        image_hashes = log_quantized_generation(
            adapter_path=target_path,
            generated_images_dir=images_dir,
            prompt_list=prompt_list,
            quantization_type=q_type
        )

        # Register artifacts
        register_quantized_artifacts(
            quantized_adapter_path=target_path,
            image_hashes=image_hashes,
            quantization_type=q_type
        )

        results["quantization_steps"].append({
            "type": q_type,
            "adapter_path": str(target_path),
            "adapter_hash": adapter_hash,
            "images_generated": len(image_hashes),
            "status": "completed"
        })

        results["artifacts"].extend(image_hashes)
        results["artifacts"].append({
            "path": str(target_path),
            "hash": adapter_hash,
            "type": "quantized_adapter",
            "quantization_type": q_type
        })

        logger.info(f"{q_type} quantization completed successfully")

    return results

def main():
    """Main entry point for quantization logging and verification."""
    config_path = Path("code/config.yaml")
    base_adapter_path = Path("data/models/adapter_fp16.safetensors")

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        return

    if not base_adapter_path.exists():
        logger.error(f"Base adapter not found: {base_adapter_path}")
        logger.error("Please run T007b to download and prepare the FP16 adapter first")
        return

    logger.info("Starting quantization logging and verification pipeline (T022)")
    logger.info(f"Config: {config_path}")
    logger.info(f"Base adapter: {base_adapter_path}")

    results = run_quantization_pipeline(
        config_path=config_path,
        base_adapter_path=base_adapter_path,
        quantization_types=['INT8', 'INT4']
    )

    logger.info(f"Pipeline completed. Processed {len(results['quantization_steps'])} quantization types")
    logger.info(f"Total artifacts registered: {len(results['artifacts'])}")

    # Save results summary
    results_path = Path("data/quantization_results.json")
    import json
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {results_path}")

if __name__ == "__main__":
    main()
