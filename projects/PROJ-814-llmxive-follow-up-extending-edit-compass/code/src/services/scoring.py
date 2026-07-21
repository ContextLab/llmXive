import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import torch
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
from skimage.metrics import structural_similarity as ssim
import lpips
from torchvision import transforms

from src.utils.logging import get_logger
from src.data_models import EditInstance, ScoreRecord

# Constants
MAX_RAM_GB = 7.0
SAFETY_BUFFER_GB = 0.5
TARGET_RAM_GB = MAX_RAM_GB - SAFETY_BUFFER_GB  # 6.5 GB
IMAGE_SIZE = 512
IMAGE_CHANNELS = 3
FLOAT32_BYTES = 4  # bytes per float32

# Initialize logger
logger = get_logger(__name__)

# Global models (lazy loaded)
_embedding_model = None
_lpips_model = None

def load_embedding_model(device: str = "cpu") -> SentenceTransformer:
    """Load the sentence-transformer model for logic scoring."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    return _embedding_model

def load_lpips_model(device: str = "cpu") -> lpips.LPIPS:
    """Load the LPIPS model for fidelity scoring."""
    global _lpips_model
    if _lpips_model is None:
        logger.info("Loading LPIPS model (alex)")
        _lpips_model = lpips.LPIPS(net="alex").to(device)
        _lpips_model.eval()
    return _lpips_model

def load_filtered_instances(input_path: Path) -> List[Dict[str, Any]]:
    """Load filtered instances from JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Filtered data not found at {input_path}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "instances" in data:
        return data["instances"]
    else:
        raise ValueError(f"Unexpected data format in {input_path}")

def resize_image(image_path: Path, size: int = IMAGE_SIZE) -> Image.Image:
    """Resize image to target size, maintaining aspect ratio."""
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    # Ensure exact size for consistent tensor shapes
    new_img = Image.new("RGB", (size, size), (255, 255, 255))
    new_img.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    return new_img

def preprocess_image_for_lpips(image: Image.Image) -> torch.Tensor:
    """Preprocess image for LPIPS (normalized to [-1, 1])."""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    return transform(image).unsqueeze(0)

def preprocess_image_for_ssim(image: Image.Image) -> np.ndarray:
    """Preprocess image for SSIM (normalized to [0, 1], grayscale)."""
    img_np = np.array(image.convert("L"), dtype=np.float32) / 255.0
    return img_np

def compute_ssim(image1: Image.Image, image2: Image.Image) -> float:
    """Compute Structural Similarity Index."""
    img1_np = preprocess_image_for_ssim(image1)
    img2_np = preprocess_image_for_ssim(image2)
    score, _ = ssim(img1_np, img2_np, full=True)
    return float(score)

def compute_lpips(image1: Image.Image, image2: Image.Image, device: str = "cpu") -> float:
    """Compute Learned Perceptual Image Patch Similarity."""
    lpips_net = load_lpips_model(device)
    img1_tensor = preprocess_image_for_lpips(image1).to(device)
    img2_tensor = preprocess_image_for_lpips(image2).to(device)
    
    with torch.no_grad():
        loss = lpips_net(img1_tensor, img2_tensor)
    return float(loss.mean().item())

def compute_logic_score(instruction: str, description: str, device: str = "cpu") -> float:
    """Compute logic score as cosine similarity between instruction and VLM description."""
    if not instruction or not description:
        return 0.0
    
    model = load_embedding_model(device)
    embeddings = model.encode([instruction, description], convert_to_tensor=True)
    cosine_sim = torch.nn.functional.cosine_similarity(embeddings[0:1], embeddings[1:2])
    return float(cosine_sim.item())

def calculate_fidelity_score(ssim_val: float, lpips_val: float) -> float:
    """
    Calculate combined fidelity score.
    Formula: 0.5 * SSIM + 0.5 * (1 - LPIPS)
    """
    return 0.5 * ssim_val + 0.5 * (1.0 - lpips_val)

def calculate_logic_scores_batch(instructions: List[str], descriptions: List[str], device: str = "cpu") -> List[float]:
    """Compute logic scores for a batch of instruction-description pairs."""
    if not instructions or not descriptions:
        return []
    
    model = load_embedding_model(device)
    all_texts = instructions + descriptions
    embeddings = model.encode(all_texts, convert_to_tensor=True)
    
    scores = []
    for i in range(len(instructions)):
        inst_emb = embeddings[i]
        desc_emb = embeddings[len(instructions) + i]
        sim = torch.nn.functional.cosine_similarity(inst_emb.unsqueeze(0), desc_emb.unsqueeze(0))
        scores.append(float(sim.item()))
    
    return scores

def process_fidelity_batch(
    source_images: List[Image.Image],
    edited_images: List[Image.Image],
    device: str = "cpu"
) -> List[Tuple[float, float, float]]:
    """
    Process a batch of image pairs for fidelity scoring.
    Returns list of (ssim, lpips, fidelity_score) tuples.
    """
    results = []
    for src, edt in zip(source_images, edited_images):
        ssim_val = compute_ssim(src, edt)
        lpips_val = compute_lpips(src, edt, device)
        fid_val = calculate_fidelity_score(ssim_val, lpips_val)
        results.append((ssim_val, lpips_val, fid_val))
    return results

def estimate_memory_usage(batch_size: int, model_size_gb: float = 1.5) -> float:
    """
    Estimate memory usage in GB for a given batch size.
    Formula: RAM_est = model_size_gb * 1.2 + batch_size * image_size_mb
    where image_size_mb is the memory of a single resized 512x512 RGB float32 tensor.
    """
    # Calculate size of one image tensor: 512 * 512 * 3 * 4 bytes
    image_size_bytes = IMAGE_SIZE * IMAGE_SIZE * IMAGE_CHANNELS * FLOAT32_BYTES
    image_size_mb = image_size_bytes / (1024 * 1024)
    
    # Model overhead (1.2x factor for framework overhead)
    model_ram = model_size_gb * 1.2
    
    # Batch RAM
    batch_ram = batch_size * image_size_mb / (1024 * 1024)  # Convert bytes to GB
    
    total_ram = model_ram + batch_ram
    return total_ram

def dynamic_batch_adjustment(
    initial_batch_size: int,
    model_size_gb: float = 1.5,
    target_ram_gb: float = TARGET_RAM_GB
) -> int:
    """
    Dynamically adjust batch size to stay within memory limits.
    Reduces batch size if estimated RAM exceeds target.
    Returns the safe batch size.
    """
    batch_size = initial_batch_size
    
    while batch_size > 0:
        estimated_ram = estimate_memory_usage(batch_size, model_size_gb)
        if estimated_ram <= target_ram_gb:
            logger.info(f"Safe batch size determined: {batch_size} (estimated RAM: {estimated_ram:.2f} GB)")
            return batch_size
        batch_size -= 1
    
    # If even batch_size=1 is too large (unlikely with 6.5GB limit), return 1 and log warning
    logger.warning("Even batch size 1 exceeds memory limit. Proceeding with batch size 1.")
    return 1

def save_scores(scores: List[ScoreRecord], output_path: Path) -> None:
    """Save score records to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [
        {
            "instance_id": str(r.instance_id),
            "logic_score": r.logic_score,
            "fidelity_score": r.fidelity_score,
            "ssim": r.ssim,
            "lpips": r.lpips,
            "vllm_description": r.vllm_description,
            "p_value_logic": r.p_value_logic,
            "p_value_fidelity": r.p_value_fidelity,
            "beta_logic": r.beta_logic,
            "beta_fidelity": r.beta_fidelity
        }
        for r in scores
    ]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(scores)} score records to {output_path}")

def main() -> None:
    """
    Main entry point for the scoring pipeline.
    Implements batch processing with pre-flight memory estimation and dynamic batch-size adjustment.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute scores for filtered edit instances")
    parser.add_argument("--input", type=str, required=True, help="Path to filtered data JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output scores JSON")
    parser.add_argument("--batch-size", type=int, default=8, help="Initial batch size")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"], help="Device for inference")
    parser.add_argument("--model-size-gb", type=float, default=1.5, help="Estimated model size in GB")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    logger.info(f"Starting scoring pipeline with input: {args.input}")
    
    # Load filtered instances
    input_path = Path(args.input)
    instances = load_filtered_instances(input_path)
    logger.info(f"Loaded {len(instances)} instances")
    
    if not instances:
        logger.warning("No instances to process. Exiting.")
        return
    
    # Determine safe batch size using pre-flight memory estimation
    safe_batch_size = dynamic_batch_adjustment(
        initial_batch_size=args.batch_size,
        model_size_gb=args.model_size_gb,
        target_ram_gb=TARGET_RAM_GB
    )
    
    # Process instances in batches
    all_scores: List[ScoreRecord] = []
    total_batches = (len(instances) + safe_batch_size - 1) // safe_batch_size
    
    for batch_idx in range(0, len(instances), safe_batch_size):
        batch_instances = instances[batch_idx : batch_idx + safe_batch_size]
        batch_num = (batch_idx // safe_batch_size) + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} (size: {len(batch_instances)})")
        
        # Resize images
        source_images = []
        edited_images = []
        instructions = []
        descriptions = []
        
        for inst in batch_instances:
            src_path = Path(inst["source_image_path"])
            edt_path = Path(inst["edited_image_path"])
            
            try:
                src_img = resize_image(src_path)
                edt_img = resize_image(edt_path)
                source_images.append(src_img)
                edited_images.append(edt_img)
                instructions.append(inst["instruction"])
                descriptions.append(inst.get("vllm_description", ""))
            except Exception as e:
                logger.error(f"Failed to load images for instance {inst.get('id', 'unknown')}: {e}")
                # Skip this instance
                continue
        
        if not source_images:
            logger.warning(f"Batch {batch_num}: No valid images to process. Skipping.")
            continue
        
        # Compute logic scores (VLM descriptions vs instructions)
        logic_scores = calculate_logic_scores_batch(instructions, descriptions, device=args.device)
        
        # Compute fidelity scores (SSIM, LPIPS)
        fidelity_results = process_fidelity_batch(source_images, edited_images, device=args.device)
        
        # Combine results
        for i, (inst, logic_score, (ssim_val, lpips_val, fid_val)) in enumerate(zip(batch_instances, logic_scores, fidelity_results)):
            try:
                score_record = ScoreRecord(
                    instance_id=inst.get("id", f"unknown_{batch_idx + i}"),
                    logic_score=logic_score,
                    fidelity_score=fid_val,
                    ssim=ssim_val,
                    lpips=lpips_val,
                    vllm_description=inst.get("vllm_description", ""),
                    p_value_logic=None,  # To be computed in analysis phase
                    p_value_fidelity=None,
                    beta_logic=None,
                    beta_fidelity=None
                )
                all_scores.append(score_record)
            except Exception as e:
                logger.error(f"Failed to create score record for instance {inst.get('id', 'unknown')}: {e}")
                # Skip this instance
                continue
        
        logger.info(f"Batch {batch_num} complete. Processed {len(logic_scores)} instances.")
    
    # Save results
    output_path = Path(args.output)
    save_scores(all_scores, output_path)
    
    logger.info(f"Scoring pipeline complete. Total scores: {len(all_scores)}")

if __name__ == "__main__":
    main()
