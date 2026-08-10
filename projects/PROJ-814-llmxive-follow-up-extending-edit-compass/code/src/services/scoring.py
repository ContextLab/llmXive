import os
import sys
import json
import logging
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from skimage.metrics import structural_similarity as ssim
import lpips
from src.utils.logging import get_logger
from src.data_models import ScoreRecord
from src.models.vlm import VLMWrapper, create_vlm_wrapper

logger = get_logger(__name__)

# Constants for memory estimation
MAX_RAM_GB = 6.5
SAFETY_BUFFER_GB = 1.0  # Buffer for system overhead and unexpected load
TARGET_RAM_GB = MAX_RAM_GB - SAFETY_BUFFER_GB
MODEL_SIZE_GB = 2.0  # Approximate size of Phi-3-mini-4k-instruct-GGUF (4-bit)
SCALING_FACTOR = 1.5  # Overhead factor for model loading and processing
BYTE_TO_GB = 1024 ** 3

def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Load the sentence transformer model for logic score calculation."""
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name, device="cpu")
    return model

def compute_logic_score(instruction: str, description: str, embedding_model: SentenceTransformer) -> float:
    """Compute cosine similarity between instruction and VLM description embeddings."""
    if not instruction or not description:
        return 0.0
    
    embeddings = embedding_model.encode([instruction, description], convert_to_tensor=True, device="cpu")
    emb1, emb2 = embeddings[0], embeddings[1]
    cosine_sim = torch.nn.functional.cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0), dim=1).item()
    return float(cosine_sim)

def calculate_logic_scores_batch(instances: List[Dict], vlm_wrapper: VLMWrapper, embedding_model: SentenceTransformer) -> List[Dict]:
    """Calculate logic scores for a batch of instances."""
    results = []
    for inst in instances:
        try:
            desc = vlm_wrapper.generate_description(inst["source_image_path"])
            score = compute_logic_score(inst["instruction"], desc, embedding_model)
            results.append({
                "instance_id": inst.get("id", "unknown"),
                "logic_score": score,
                "vlm_description": desc
            })
        except Exception as e:
            logger.error(f"Failed to compute logic score for {inst.get('id', 'unknown')}: {e}")
            results.append({
                "instance_id": inst.get("id", "unknown"),
                "logic_score": None,
                "vlm_description": None,
                "error": str(e)
            })
    return results

def load_filtered_instances(path: Path) -> List[Dict]:
    """Load filtered instances from JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def save_scores(scores: List[Dict], output_path: Path):
    """Save scores to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scores, f, indent=2)
    logger.info(f"Scores saved to {output_path}")

def estimate_memory_usage(batch_size: int, image_size_mb: float) -> float:
    """
    Estimate memory usage for a batch.
    Formula: RAM_est = model_size_gb * scaling_factor + batch_size * image_size_mb
    """
    ram_est_gb = (MODEL_SIZE_GB * SCALING_FACTOR) + (batch_size * image_size_mb / (1024 ** 2))
    return ram_est_gb

def dynamic_batch_adjustment(initial_batch_size: int, image_size_mb: float) -> int:
    """
    Adjust batch size dynamically to stay within memory limits.
    Reduces batch size if estimated RAM exceeds TARGET_RAM_GB.
    """
    batch_size = initial_batch_size
    while batch_size > 0:
        ram_est = estimate_memory_usage(batch_size, image_size_mb)
        if ram_est <= TARGET_RAM_GB:
            return batch_size
        batch_size -= 1
    
    logger.warning("Could not find a valid batch size within memory limits. Using batch size 1.")
    return 1

def resize_image(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """Resize image to specified size."""
    return image.resize(size, Image.Resampling.LANCZOS)

def preprocess_image_for_lpips(image: Image.Image) -> torch.Tensor:
    """Preprocess image for LPIPS calculation."""
    # LPIPS expects images in [-1, 1] range
    image_tensor = F.to_tensor(image) * 2 - 1
    return image_tensor.unsqueeze(0)

def preprocess_image_for_ssim(image: Image.Image, mode: str = 'L') -> np.ndarray:
    """Preprocess image for SSIM calculation."""
    img_array = np.array(image.convert(mode))
    return img_array.astype(np.float32) / 255.0

def compute_ssim(image1: Image.Image, image2: Image.Image) -> float:
    """Compute SSIM between two images."""
    # Convert to grayscale for SSIM
    img1 = preprocess_image_for_ssim(image1, 'L')
    img2 = preprocess_image_for_ssim(image2, 'L')
    
    # Ensure same dimensions
    if img1.shape != img2.shape:
        raise ValueError(f"Image dimensions do not match: {img1.shape} vs {img2.shape}")
    
    score, _ = ssim(img1, img2, full=True)
    return float(score)

def compute_lpips(image1: Image.Image, image2: Image.Image, loss_fn: lpips.LPIPS) -> float:
    """Compute LPIPS between two images."""
    img1_tensor = preprocess_image_for_lpips(image1)
    img2_tensor = preprocess_image_for_lpips(image2)
    
    # LPIPS expects 4D tensors (batch, channels, height, width)
    with torch.no_grad():
        loss = loss_fn(img1_tensor, img2_tensor)
    return float(loss.item())

def load_lpips_model(net: str = 'alex') -> lpips.LPIPS:
    """Load LPIPS model."""
    logger.info("Loading LPIPS model")
    return lpips.LPIPS(net=net)

def calculate_fidelity_score(image1_path: str, image2_path: str, ssim_score: float, lpips_score: float, ssim_weight: float = 0.5) -> float:
    """
    Calculate fidelity score as a weighted combination of SSIM and (1 - LPIPS).
    Fidelity = SSIM_weight * SSIM + (1 - SSIM_weight) * (1 - LPIPS)
    """
    return ssim_weight * ssim_score + (1 - ssim_weight) * (1 - lpips_score)

class ImageDataset(torch.utils.data.Dataset):
    """Dataset for loading image pairs."""
    def __init__(self, instances: List[Dict]):
        self.instances = instances

    def __len__(self):
        return len(self.instances)

    def __getitem__(self, idx):
        inst = self.instances[idx]
        source = Image.open(inst["source_image_path"]).convert("RGB")
        edited = Image.open(inst["edited_image_path"]).convert("RGB")
        return {
            "id": inst.get("id", "unknown"),
            "source": source,
            "edited": edited,
            "instruction": inst["instruction"]
        }

def process_fidelity_batch(batch: List[Dict], loss_fn: lpips.LPIPS) -> List[Dict]:
    """Process a batch of images for fidelity scores."""
    results = []
    for item in batch:
        try:
            ssim_val = compute_ssim(item["source"], item["edited"])
            lpips_val = compute_lpips(item["source"], item["edited"], loss_fn)
            fid_score = calculate_fidelity_score("", "", ssim_val, lpips_val)
            results.append({
                "instance_id": item["id"],
                "ssim": ssim_val,
                "lpips": lpips_val,
                "fidelity_score": fid_score
            })
        except Exception as e:
            logger.error(f"Failed to compute fidelity for {item['id']}: {e}")
            results.append({
                "instance_id": item["id"],
                "ssim": None,
                "lpips": None,
                "fidelity_score": None,
                "error": str(e)
            })
    return results

def main():
    """Main entry point for scoring pipeline with dynamic batch adjustment."""
    logger.info("Starting scoring pipeline with dynamic batch adjustment")
    
    # Paths
    filtered_path = Path("data/filtered/filtered_dataset.json")
    scores_output = Path("data/scores/scoring_results.json")
    
    if not filtered_path.exists():
        logger.error(f"Filtered dataset not found at {filtered_path}")
        sys.exit(1)
    
    # Load data
    instances = load_filtered_instances(filtered_path)
    if not instances:
        logger.error("No instances found in filtered dataset")
        sys.exit(1)
    
    logger.info(f"Loaded {len(instances)} instances")
    
    # Initialize models
    embedding_model = load_embedding_model()
    vlm_wrapper = create_vlm_wrapper()
    lpips_model = load_lpips_model()
    
    # Estimate image size
    # Load first image to estimate memory usage (original size, NO resize)
    first_inst = instances[0]
    try:
        sample_img = Image.open(first_inst["source_image_path"])
        # Estimate size in bytes: width * height * channels * bytes_per_pixel
        # Assuming RGB (3 channels) and float32 (4 bytes) for tensor storage
        img_size_bytes = sample_img.width * sample_img.height * 3 * 4
        image_size_mb = img_size_bytes / (1024 ** 2)
        logger.info(f"Estimated single image memory usage: {image_size_mb:.2f} MB")
    except Exception as e:
        logger.error(f"Failed to estimate image size: {e}")
        sys.exit(1)
    
    # Dynamic batch size adjustment
    initial_batch_size = 8
    batch_size = dynamic_batch_adjustment(initial_batch_size, image_size_mb)
    logger.info(f"Using batch size: {batch_size} (estimated RAM: {estimate_memory_usage(batch_size, image_size_mb):.2f} GB)")
    
    # Process logic scores
    logger.info("Computing logic scores...")
    logic_results = calculate_logic_scores_batch(instances, vlm_wrapper, embedding_model)
    
    # Process fidelity scores in batches
    logger.info("Computing fidelity scores...")
    dataset = ImageDataset(instances)
    all_fidelity_results = []
    
    for i in range(0, len(dataset), batch_size):
        batch = [dataset[j] for j in range(i, min(i + batch_size, len(dataset)))]
        batch_results = process_fidelity_batch(batch, lpips_model)
        all_fidelity_results.extend(batch_results)
        logger.info(f"Processed batch {i // batch_size + 1} ({len(batch)} items)")
    
    # Merge results
    final_scores = []
    for logic_res, fid_res in zip(logic_results, all_fidelity_results):
        record = {
            "instance_id": logic_res["instance_id"],
            "logic_score": logic_res["logic_score"],
            "vlm_description": logic_res["vlm_description"],
            "ssim": fid_res["ssim"],
            "lpips": fid_res["lpips"],
            "fidelity_score": fid_res["fidelity_score"]
        }
        if "error" in logic_res:
            record["logic_error"] = logic_res["error"]
        if "error" in fid_res:
            record["fidelity_error"] = fid_res["error"]
        final_scores.append(record)
    
    # Save results
    save_scores(final_scores, scores_output)
    
    # Summary
    valid_logic = sum(1 for r in final_scores if r["logic_score"] is not None)
    valid_fid = sum(1 for r in final_scores if r["fidelity_score"] is not None)
    logger.info(f"Scoring complete. Valid logic: {valid_logic}/{len(final_scores)}, Valid fidelity: {valid_fid}/{len(final_scores)}")

if __name__ == "__main__":
    main()