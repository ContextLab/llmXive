import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import lpips
from torchvision import transforms
from torch.utils.data import DataLoader, Dataset

from src.utils.logging import get_logger
from src.data_models import EditInstance, ScoreRecord

# Constants
RAM_LIMIT_GB = 7.0
SAFETY_BUFFER_GB = 0.5
MAX_RAM_EST_GB = RAM_LIMIT_GB - SAFETY_BUFFER_GB
IMAGE_SIZE = 512
BATCH_SIZE_INITIAL = 8
BATCH_SIZE_MIN = 1

logger = get_logger(__name__)

# Helper: Estimate memory usage
def estimate_memory_usage(model_size_gb: float, batch_size: int, image_size_mb: float) -> float:
    """
    Estimate total RAM usage in GB.
    Formula: RAM_est = model_size_gb * 1.2 + batch_size * image_size_mb
    """
    return model_size_gb * 1.2 + batch_size * image_size_mb

def dynamic_batch_adjustment(
    model_size_gb: float,
    initial_batch_size: int,
    image_size_mb: float
) -> int:
    """
    Adjust batch size down if estimated memory exceeds MAX_RAM_EST_GB.
    Returns the safe batch size.
    """
    batch_size = initial_batch_size
    while batch_size >= BATCH_SIZE_MIN:
        est_ram = estimate_memory_usage(model_size_gb, batch_size, image_size_mb)
        if est_ram <= MAX_RAM_EST_GB:
            return batch_size
        batch_size -= 1
    
    # Even at minimum batch size, if it exceeds limit, return 1 (will likely fail but we tried)
    logger.warning(f"Even batch size {BATCH_SIZE_MIN} exceeds memory limit. Proceeding with 1.")
    return BATCH_SIZE_MIN

# Image Processing
def resize_image(image_path: Path, size: int = IMAGE_SIZE) -> Image.Image:
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    img = Image.open(image_path).convert("RGB")
    return img.resize((size, size), Image.Resampling.LANCZOS)

def preprocess_image_for_lpips(image: Image.Image) -> torch.Tensor:
    """Convert PIL Image to [0,1] tensor for LPIPS."""
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    return transform(image)

def preprocess_image_for_ssim(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to numpy array for SSIM."""
    return np.array(image)

def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Compute Structural Similarity Index."""
    # Ensure both are same shape and type
    if img1.shape != img2.shape:
        raise ValueError(f"Shape mismatch: {img1.shape} vs {img2.shape}")
    score, _ = ssim(img1, img2, channel_axis=2, full=True)
    return float(score)

def compute_lpips(
    img1_tensor: torch.Tensor,
    img2_tensor: torch.Tensor,
    lpips_model: lpips.LPIPS
) -> float:
    """Compute Learned Perceptual Image Patch Similarity."""
    # LPIPS expects inputs in [-1, 1]
    transform_neg = transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    t1 = transform_neg(img1_tensor).unsqueeze(0)
    t2 = transform_neg(img2_tensor).unsqueeze(0)
    
    with torch.no_grad():
        loss = lpips_model(t1, t2)
    return float(loss.item())

# Model Loading
def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    logger.info(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name, device="cpu")

def load_lpips_model(net: str = "alex") -> lpips.LPIPS:
    logger.info(f"Loading LPIPS model: {net}")
    return lpips.LPIPS(net=net)

def load_filtered_instances(filtered_dir: Path) -> List[EditInstance]:
    """Load all JSON/CSV files from filtered directory."""
    instances = []
    filtered_path = Path(filtered_dir)
    if not filtered_path.exists():
        raise FileNotFoundError(f"Filtered directory not found: {filtered_path}")
    
    for file_path in filtered_path.glob("*"):
        if file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    instances.extend([EditInstance(**item) for item in data])
                else:
                    instances.append(EditInstance(**data))
        elif file_path.suffix == ".jsonl":
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        instances.append(EditInstance(**json.loads(line)))
    logger.info(f"Loaded {len(instances)} instances from {filtered_dir}")
    return instances

# Scoring Logic
def calculate_fidelity_score(ssim_val: float, lpips_val: float) -> float:
    """
    Weighted combination: 0.5 * SSIM + 0.5 * (1 - LPIPS)
    Both SSIM and LPIPS are in [0, 1].
    """
    return 0.5 * ssim_val + 0.5 * (1.0 - lpips_val)

def compute_logic_score(
    instruction: str,
    description: str,
    embedder: SentenceTransformer
) -> float:
    """
    Compute cosine similarity between instruction and VLM description embeddings.
    Returns value in [-1, 1].
    """
    if not instruction or not description:
        return 0.0
    emb1 = embedder.encode(instruction, convert_to_numpy=True)
    emb2 = embedder.encode(description, convert_to_numpy=True)
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(emb1, emb2) / (norm1 * norm2))

# Batch Processing with Memory Estimation
class ImageDataset(Dataset):
    def __init__(self, instances: List[EditInstance], resize_size: int = IMAGE_SIZE):
        self.instances = instances
        self.resize_size = resize_size

    def __len__(self):
        return len(self.instances)

    def __getitem__(self, idx):
        inst = self.instances[idx]
        try:
            img_source = resize_image(Path(inst.source_image_path), self.resize_size)
            img_edited = resize_image(Path(inst.edited_image_path), self.resize_size)
            return {
                "source": img_source,
                "edited": img_edited,
                "instance": inst,
                "idx": idx
            }
        except Exception as e:
            logger.error(f"Error loading image for instance {inst.instance_id}: {e}")
            return None

def process_fidelity_batch(
    batch: List[Dict[str, Any]],
    lpips_model: lpips.LPIPS
) -> List[Tuple[EditInstance, float, float, float]]:
    """
    Process a batch of images for fidelity scores.
    Returns list of (instance, ssim, lpips, fidelity_score).
    """
    results = []
    for item in batch:
        if item is None:
            continue
        inst = item["instance"]
        img_s = item["source"]
        img_e = item["edited"]
        
        try:
            arr_s = preprocess_image_for_ssim(img_s)
            arr_e = preprocess_image_for_ssim(img_e)
            ssim_val = compute_ssim(arr_s, arr_e)
            
            t_s = preprocess_image_for_lpips(img_s)
            t_e = preprocess_image_for_lpips(img_e)
            lpips_val = compute_lpips(t_s, t_e, lpips_model)
            
            fid_score = calculate_fidelity_score(ssim_val, lpips_val)
            results.append((inst, ssim_val, lpips_val, fid_score))
        except Exception as e:
            logger.error(f"Fidelity computation failed for {inst.instance_id}: {e}")
            results.append((inst, 0.0, 0.0, 0.0))
    return results

def save_scores(
    scores: List[ScoreRecord],
    output_dir: Path
) -> None:
    """Save scores to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "scores.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump([s.model_dump() for s in scores], f, indent=2)
    logger.info(f"Saved {len(scores)} scores to {out_file}")

def main(
    filtered_dir: str,
    output_dir: str,
    vlm_wrapper: Any,
    embedder: SentenceTransformer,
    lpips_model: lpips.LPIPS,
    initial_batch_size: int = BATCH_SIZE_INITIAL
) -> List[ScoreRecord]:
    """
    Main batch processing loop with memory estimation and dynamic batch size adjustment.
    
    Args:
        filtered_dir: Path to filtered instances
        output_dir: Path to save scores
        vlm_wrapper: VLMWrapper instance for generating descriptions
        embedder: SentenceTransformer instance
        lpips_model: LPIPS model instance
        initial_batch_size: Starting batch size
    
    Returns:
        List of ScoreRecord objects
    """
    logger.info("Starting batch processing with memory estimation...")
    
    # Load instances
    instances = load_filtered_instances(Path(filtered_dir))
    if not instances:
        logger.warning("No instances found. Exiting.")
        return []

    # Estimate memory parameters
    # Approximate model sizes (in GB) - these are conservative estimates
    vlm_model_size = 2.0  # 4-bit Phi-3-mini is ~2GB
    embedder_model_size = 0.1
    lpips_model_size = 0.05
    total_model_size = vlm_model_size + embedder_model_size + lpips_model_size

    # Estimate single image tensor size (512x512x3 float32)
    # 512 * 512 * 3 * 4 bytes = 3,145,728 bytes ≈ 3MB
    image_size_mb = (IMAGE_SIZE * IMAGE_SIZE * 3 * 4) / (1024 * 1024)
    
    # Determine safe batch size
    safe_batch_size = dynamic_batch_adjustment(total_model_size, initial_batch_size, image_size_mb)
    logger.info(f"Adjusted batch size to {safe_batch_size} to stay within {MAX_RAM_EST_GB}GB limit.")

    # Prepare dataset
    dataset = ImageDataset(instances)
    loader = DataLoader(dataset, batch_size=safe_batch_size, shuffle=False, num_workers=0)

    all_scores = []
    total = len(instances)
    processed = 0

    for batch_idx, batch in enumerate(loader):
        # Filter out None items (failed loads)
        valid_batch = [b for b in batch if b is not None]
        if not valid_batch:
            continue

        # 1. VLM Descriptions (Logic Score)
        try:
            instructions = [b["instance"].instruction for b in valid_batch]
            source_images = [b["source"] for b in valid_batch]
            
            # Generate descriptions in batch
            descriptions = vlm_wrapper.generate_batch(instructions, source_images)
        except Exception as e:
            logger.error(f"VLM generation failed for batch {batch_idx}: {e}")
            descriptions = [""] * len(valid_batch)

        # 2. Compute Logic Scores
        logic_scores = [
            compute_logic_score(b["instance"].instruction, desc, embedder)
            for b, desc in zip(valid_batch, descriptions)
        ]

        # 3. Compute Fidelity Scores
        fidelity_results = process_fidelity_batch(valid_batch, lpips_model)

        # 4. Aggregate and Save
        for i, b in enumerate(valid_batch):
            inst = b["instance"]
            logic_score = logic_scores[i]
            ssim_val = fidelity_results[i][1]
            lpips_val = fidelity_results[i][2]
            fid_score = fidelity_results[i][3]
            
            # Create ScoreRecord
            # Note: p-values and betas are set to 0 here; they will be computed in analysis phase
            record = ScoreRecord(
                instance_id=inst.instance_id,
                logic_score=logic_score,
                fidelity_score=fid_score,
                ssim=ssim_val,
                lpips=lpips_val,
                vllm_description=descriptions[i],
                p_value_logic=0.0,
                p_value_fidelity=0.0,
                beta_logic=0.0,
                beta_fidelity=0.0
            )
            all_scores.append(record)
        
        processed += len(valid_batch)
        logger.info(f"Processed {processed}/{total} instances (Batch {batch_idx + 1})")

    # Save results
    save_scores(all_scores, Path(output_dir))
    return all_scores

if __name__ == "__main__":
    # Example usage for testing
    logging.basicConfig(level=logging.INFO)
    logger.info("Scoring module loaded.")