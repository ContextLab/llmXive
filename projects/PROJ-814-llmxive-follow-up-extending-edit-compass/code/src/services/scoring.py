import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import numpy as np
from PIL import Image
from sentence_transformers import SentenceTransformer
from skimage.metrics import structural_similarity as ssim
import lpips
from tqdm import tqdm

from src.data_models import EditInstance, ScoreRecord
from src.utils.logging import get_logger

# Constants
RAM_LIMIT_GB = 7.0
SAFETY_BUFFER_GB = 0.5
MAX_SAFE_RAM_GB = RAM_LIMIT_GB - SAFETY_BUFFER_GB  # 6.5 GB
IMAGE_SIZE_MB = 512 * 512 * 3 * 4 / (1024 * 1024)  # 512x512 RGB float32 tensor in MB
MODEL_SIZE_GB = 2.0  # Approximate size for Phi-3-mini-4k-instruct-GGUF (4-bit) + SentenceTransformer + LPIPS

logger = get_logger(__name__)

def load_embedding_model() -> SentenceTransformer:
    """Load the SentenceTransformer model for logic score embeddings."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model.eval()
    return model

def load_lpips_model() -> lpips.LPIPS:
    """Load the LPIPS model for fidelity scoring."""
    model = lpips.LPIPS(net='alex')
    model.eval()
    return model

def load_filtered_instances(path: Path) -> List[EditInstance]:
    """Load filtered instances from a JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    return [EditInstance(**item) for item in data]

def resize_image(image_path: Path, size: Tuple[int, int] = (512, 512)) -> np.ndarray:
    """Resize an image to the specified size and return as numpy array."""
    img = Image.open(image_path).convert('RGB')
    img = img.resize(size, Image.Resampling.LANCZOS)
    return np.array(img)

def preprocess_image_for_lpips(image: np.ndarray) -> torch.Tensor:
    """Preprocess image for LPIPS (normalize to [-1, 1])."""
    img_tensor = torch.from_numpy(image).permute(2, 0, 1).float() / 127.5 - 1.0
    return img_tensor.unsqueeze(0)

def preprocess_image_for_ssim(image: np.ndarray) -> np.ndarray:
    """Preprocess image for SSIM (convert to grayscale if needed, ensure float64)."""
    if image.ndim == 3 and image.shape[2] == 3:
        # Convert to grayscale
        image = np.dot(image[..., :3], [0.2989, 0.5870, 0.1140])
    return image.astype(np.float64)

def compute_ssim(image1: np.ndarray, image2: np.ndarray) -> float:
    """Compute SSIM between two images."""
    score, _ = ssim(image1, image2, full=True)
    return float(score)

def compute_lpips(image1: torch.Tensor, image2: torch.Tensor, lpips_model: lpips.LPIPS) -> float:
    """Compute LPIPS between two images."""
    with torch.no_grad():
        score = lpips_model(image1, image2)
    return float(score.item())

def calculate_fidelity_score(source_image: np.ndarray, edited_image: np.ndarray, lpips_model: lpips.LPIPS) -> float:
    """Calculate the weighted combination of SSIM and (1-LPIPS)."""
    ssim_score = compute_ssim(
        preprocess_image_for_ssim(source_image),
        preprocess_image_for_ssim(edited_image)
    )
    lpips_score = compute_lpips(
        preprocess_image_for_lpips(source_image),
        preprocess_image_for_lpips(edited_image),
        lpips_model
    )
    # Weighted combination: 0.5 * SSIM + 0.5 * (1 - LPIPS)
    return 0.5 * ssim_score + 0.5 * (1 - lpips_score)

def calculate_logic_score(instruction: str, vlm_description: str, embedding_model: SentenceTransformer) -> float:
    """Calculate logic score as cosine similarity between instruction and VLM description embeddings."""
    if not instruction or not vlm_description:
        return 0.0
    embeddings = embedding_model.encode([instruction, vlm_description], convert_to_tensor=True)
    cosine_sim = torch.nn.functional.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    return float(cosine_sim.item())

def compute_logic_score(instruction: str, vlm_description: str, embedding_model: SentenceTransformer) -> float:
    """Wrapper for calculate_logic_score to ensure consistent API."""
    return calculate_logic_score(instruction, vlm_description, embedding_model)

def calculate_logic_scores_batch(instructions: List[str], descriptions: List[str], embedding_model: SentenceTransformer) -> List[float]:
    """Calculate logic scores for a batch of instructions and descriptions."""
    if not instructions or not descriptions:
        return []
    embeddings = embedding_model.encode(instructions + descriptions, convert_to_tensor=True)
    scores = []
    for i in range(len(instructions)):
        instr_emb = embeddings[i]
        desc_emb = embeddings[len(instructions) + i]
        cosine_sim = torch.nn.functional.cosine_similarity(instr_emb.unsqueeze(0), desc_emb.unsqueeze(0))
        scores.append(float(cosine_sim.item()))
    return scores

def save_scores(scores: List[ScoreRecord], output_path: Path):
    """Save scores to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([s.model_dump() for s in scores], f, indent=2)

def process_fidelity_batch(batch: List[EditInstance], lpips_model: lpips.LPIPS) -> List[float]:
    """Process a batch of instances for fidelity scores."""
    scores = []
    for instance in batch:
        try:
            source = resize_image(Path(instance.source_image_path))
            edited = resize_image(Path(instance.edited_image_path))
            score = calculate_fidelity_score(source, edited, lpips_model)
            scores.append(score)
        except Exception as e:
            logger.error(f"Error processing fidelity for {instance.instance_id}: {e}")
            scores.append(None)
    return scores

def estimate_memory_usage(batch_size: int) -> float:
    """Estimate memory usage in GB for a given batch size."""
    ram_est_gb = MODEL_SIZE_GB * 1.2 + batch_size * IMAGE_SIZE_MB / 1024.0
    return ram_est_gb

def dynamic_batch_adjustment(initial_batch_size: int = 8) -> int:
    """Dynamically adjust batch size to stay within memory limits."""
    batch_size = initial_batch_size
    while estimate_memory_usage(batch_size) > MAX_SAFE_RAM_GB and batch_size > 1:
        batch_size -= 1
    if estimate_memory_usage(batch_size) > MAX_SAFE_RAM_GB:
        logger.warning(f"Even batch size 1 exceeds memory limit. Using batch size 1 with risk of OOM.")
        batch_size = 1
    return batch_size

def main():
    """Main entry point for scoring with dynamic batch adjustment."""
    import argparse
    parser = argparse.ArgumentParser(description="Score filtered instances with dynamic batch adjustment.")
    parser.add_argument("--input", type=str, required=True, help="Path to filtered instances JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output scores JSON")
    parser.add_argument("--batch-size", type=int, default=8, help="Initial batch size for scoring")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Load models
    embedding_model = load_embedding_model()
    lpips_model = load_lpips_model()

    # Load instances
    instances = load_filtered_instances(input_path)
    logger.info(f"Loaded {len(instances)} instances.")

    # Determine optimal batch size
    batch_size = dynamic_batch_adjustment(args.batch_size)
    logger.info(f"Using dynamic batch size: {batch_size}")

    scores = []
    total = len(instances)
    
    # Process in batches
    for i in tqdm(range(0, total, batch_size)):
        batch = instances[i:i+batch_size]
        
        # Process Fidelity Scores (can be parallelized if needed, but keeping simple for now)
        fidelity_scores = process_fidelity_batch(batch, lpips_model)
        
        # Process Logic Scores (requires VLM descriptions - assuming they are pre-generated or generated here)
        # For this implementation, we assume VLM descriptions are already available or generated in a previous step.
        # If not, we would need to integrate VLM generation here.
        # Placeholder: Assuming descriptions are part of the instance or generated elsewhere.
        # In a real scenario, we would call the VLM wrapper here.
        logic_scores = []
        for j, instance in enumerate(batch):
            # Placeholder: Replace with actual VLM description generation if needed
            # For now, assuming description is available or set to empty string if not
            desc = getattr(instance, 'vlm_description', '') 
            if not desc:
                # If description is missing, we cannot compute logic score
                # In a full pipeline, this would trigger VLM generation
                desc = ""
            logic_score = calculate_logic_score(instance.instruction, desc, embedding_model)
            logic_scores.append(logic_score)
        
        # Create ScoreRecords
        for j, instance in enumerate(batch):
            score_record = ScoreRecord(
                instance_id=instance.instance_id,
                logic_score=logic_scores[j],
                fidelity_score=fidelity_scores[j],
                ssim=0.0,  # Placeholder, should be computed if needed
                lpips=0.0, # Placeholder, should be computed if needed
                vllm_description=getattr(instance, 'vlm_description', ''),
                p_value_logic=0.0, # Placeholder
                p_value_fidelity=0.0, # Placeholder
                beta_logic=0.0, # Placeholder
                beta_fidelity=0.0 # Placeholder
            )
            scores.append(score_record)

    # Save results
    save_scores(scores, output_path)
    logger.info(f"Scores saved to {output_path}")

if __name__ == "__main__":
    main()
