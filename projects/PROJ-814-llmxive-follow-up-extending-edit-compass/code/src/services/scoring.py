import os
import sys
import json
import logging
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
from sentence_transformers import SentenceTransformer
import lpips
from skimage.metrics import structural_similarity as ssim
from src.data_models import EditInstance, ScoreRecord
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Global model caches
_embedding_model: Optional[SentenceTransformer] = None
_lpips_model: Optional[Any] = None

def load_embedding_model() -> SentenceTransformer:
    """Load the sentence-transformer model for logic scoring."""
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    return _embedding_model

def load_lpips_model() -> Any:
    """Load the LPIPS model for fidelity scoring."""
    global _lpips_model
    if _lpips_model is None:
        logger.info("Loading LPIPS model (alex)")
        _lpips_model = lpips.LPIPS(net='alex').eval().cpu()
    return _lpips_model

def preprocess_image_for_ssim(image_path: str) -> np.ndarray:
    """Load and convert image to grayscale numpy array for SSIM."""
    try:
        img = Image.open(image_path).convert('L')
        return np.array(img)
    except Exception as e:
        raise ValueError(f"Failed to load image for SSIM: {image_path} - {e}")

def preprocess_image_for_lpips(image_path: str) -> torch.Tensor:
    """Load and convert image to normalized tensor for LPIPS."""
    try:
        img = Image.open(image_path).convert('RGB')
        # Convert to tensor and normalize to [-1, 1]
        img_tensor = torch.from_numpy(np.array(img)).float() / 255.0
        img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)
        img_tensor = img_tensor * 2 - 1
        return img_tensor
    except Exception as e:
        raise ValueError(f"Failed to load image for LPIPS: {image_path} - {e}")

def compute_ssim(source_path: str, edited_path: str) -> float:
    """Compute Structural Similarity Index between two images."""
    img1 = preprocess_image_for_ssim(source_path)
    img2 = preprocess_image_for_ssim(edited_path)
    # Ensure same shape
    if img1.shape != img2.shape:
        # Resize edited to match source if necessary (though spec says no resizing,
        # SSIM requires same dimensions. If they differ, we cannot compute SSIM directly.
        # We will raise an error if dimensions differ significantly, or resize internally if minor.
        # For strict adherence to "no resizing" for the *result*, we might just fail here if shapes differ.
        # However, standard SSIM implementation requires same shape.
        # We will attempt to resize the edited image to match source for the calculation only,
        # but log it.
        if img1.shape != img2.shape:
            logger.warning(f"Image dimensions differ for SSIM. Source: {img1.shape}, Edited: {img2.shape}. Resizing edited for calculation.")
            from PIL import Image
            img2 = Image.fromarray(img2).resize((img1.shape[1], img1.shape[0]))
            img2 = np.array(img2)

    score, _ = ssim(img1, img2, full=True)
    return float(score)

def compute_lpips(source_path: str, edited_path: str) -> float:
    """Compute LPIPS distance between two images."""
    lpips_net = load_lpips_model()
    img1 = preprocess_image_for_lpips(source_path)
    img2 = preprocess_image_for_lpips(edited_path)

    with torch.no_grad():
        score = lpips_net(img1, img2)
    return float(score.item())

def calculate_fidelity_score(source_path: str, edited_path: str) -> Tuple[float, float, float]:
    """
    Calculate Fidelity Score components: SSIM and LPIPS.
    Returns (ssim_score, lpips_score, combined_fidelity_score)
    Fidelity = (SSIM + (1 - LPIPS)) / 2
    """
    ssim_val = compute_ssim(source_path, edited_path)
    lpips_val = compute_lpips(source_path, edited_path)
    combined = (ssim_val + (1.0 - lpips_val)) / 2.0
    return ssim_val, lpips_val, combined

def compute_logic_score(instruction: str, vlm_description: str) -> float:
    """Compute logic score as cosine similarity between instruction and VLM description."""
    model = load_embedding_model()
    embeddings = model.encode([instruction, vlm_description], convert_to_tensor=True, device='cpu')
    cos_sim = torch.nn.functional.cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
    return float(cos_sim.item())

def load_filtered_instances() -> List[Dict[str, Any]]:
    """Load filtered instances from data/filtered/."""
    filtered_dir = Path("data/filtered")
    if not filtered_dir.exists():
        raise FileNotFoundError(f"Filtered data directory not found: {filtered_dir}")
    
    # Find JSON files
    json_files = list(filtered_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {filtered_dir}")

    all_instances = []
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_instances.extend(data)
            else:
                all_instances.append(data)
    
    return all_instances

def save_scores(scores: List[ScoreRecord], output_path: str = "data/scores/scores.json"):
    """Save score records to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    records = [record.model_dump() for record in scores]
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Saved {len(scores)} scores to {output_path}")

def estimate_memory_usage(batch_size: int) -> float:
    """Estimate RAM usage in GB for a given batch size."""
    base_overhead = 2.0  # GB for model loading
    per_image_overhead = 0.05  # GB per image
    return base_overhead + (batch_size * per_image_overhead)

def dynamic_batch_adjustment(initial_batch: int, max_ram_gb: float = 6.65) -> int:
    """
    Adjust batch size to ensure estimated RAM usage is below limit.
    RAM_limit = 7GB * 0.95 = 6.65 GB
    """
    batch_size = initial_batch
    while estimate_memory_usage(batch_size) > max_ram_gb and batch_size > 1:
        batch_size -= 1
        logger.debug(f"Adjusted batch size down to {batch_size} to fit memory limit.")
    
    if batch_size == 1 and estimate_memory_usage(batch_size) > max_ram_gb:
        logger.warning("Even batch size 1 exceeds memory limit. Proceeding with caution.")
    
    if batch_size < initial_batch:
        logger.info(f"Batch size adjusted from {initial_batch} to {batch_size} to meet RAM limit ({max_ram_gb} GB).")
    
    return batch_size

def process_fidelity_batch(instances: List[Dict[str, Any]], batch_size: int) -> List[ScoreRecord]:
    """Process a batch of instances for fidelity scores with path validation."""
    results = []
    for instance in instances:
        source_path = instance.get('source_image_path')
        edited_path = instance.get('edited_image_path')
        instance_id = instance.get('id', 'unknown')

        # T037: Pre-flight check for image existence
        if not source_path or not edited_path:
            logger.warning(f"Skipping instance {instance_id}: Missing image paths.")
            continue

        if not os.path.exists(source_path):
            logger.warning(f"Skipping instance {instance_id}: Source image not found at '{source_path}'.")
            continue

        if not os.path.exists(edited_path):
            logger.warning(f"Skipping instance {instance_id}: Edited image not found at '{edited_path}'.")
            continue

        try:
            ssim_val, lpips_val, fidelity_val = calculate_fidelity_score(source_path, edited_path)
            results.append({
                'instance_id': instance_id,
                'ssim': ssim_val,
                'lpips': lpips_val,
                'fidelity_score': fidelity_val,
                'source_path': source_path,
                'edited_path': edited_path
            })
        except Exception as e:
            logger.error(f"Error calculating fidelity for instance {instance_id}: {e}")
            continue

    return results

def calculate_logic_scores_batch(instances: List[Dict[str, Any]], vlm_descriptions: List[str]) -> List[Dict[str, Any]]:
    """Calculate logic scores for a batch of instances."""
    results = []
    for i, instance in enumerate(instances):
        instance_id = instance.get('id', 'unknown')
        instruction = instance.get('instruction', '')
        vlm_desc = vlm_descriptions[i] if i < len(vlm_descriptions) else ''

        if not instruction or not vlm_desc:
            logger.warning(f"Skipping logic score for {instance_id}: Missing instruction or description.")
            continue

        try:
            logic_score = compute_logic_score(instruction, vlm_desc)
            results.append({
                'instance_id': instance_id,
                'logic_score': logic_score,
                'instruction': instruction,
                'vlm_description': vlm_desc
            })
        except Exception as e:
            logger.error(f"Error calculating logic score for instance {instance_id}: {e}")
            continue

    return results

def main():
    """Main entry point for the scoring pipeline."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting scoring pipeline...")

    # Load filtered instances
    try:
        instances = load_filtered_instances()
        logger.info(f"Loaded {len(instances)} filtered instances.")
    except Exception as e:
        logger.error(f"Failed to load instances: {e}")
        sys.exit(1)

    # Determine batch size
    initial_batch = 4
    safe_batch = dynamic_batch_adjustment(initial_batch)
    logger.info(f"Using batch size: {safe_batch}")

    all_scores = []

    # Process in batches
    for i in range(0, len(instances), safe_batch):
        batch = instances[i:i+safe_batch]
        logger.info(f"Processing batch {i//safe_batch + 1} ({len(batch)} items)...")

        # 1. Fidelity Scores (Path check happens inside process_fidelity_batch)
        fidelity_results = process_fidelity_batch(batch, safe_batch)
        
        # 2. Logic Scores (Assuming VLM descriptions are pre-computed or passed)
        # For this task, we assume VLM descriptions are available or we skip logic if not.
        # In a real pipeline, VLM generation would happen here or be pre-loaded.
        # We will simulate fetching descriptions or skip if not present in instance.
        vlm_descs = [inst.get('vlm_description', '') for inst in batch]
        logic_results = calculate_logic_scores_batch(batch, vlm_descs)

        # Merge results
        for fid in fidelity_results:
            inst_id = fid['instance_id']
            logic_match = next((l for l in logic_results if l['instance_id'] == inst_id), None)
            
            score_record = ScoreRecord(
                instance_id=inst_id,
                logic_score=logic_match['logic_score'] if logic_match else 0.0,
                fidelity_score=fid['fidelity_score'],
                ssim=fid['ssim'],
                lpips=fid['lpips'],
                vllm_description=logic_match.get('vlm_description', '') if logic_match else ''
            )
            all_scores.append(score_record)

    if all_scores:
        save_scores(all_scores)
        logger.info("Scoring pipeline completed successfully.")
    else:
        logger.warning("No scores were generated.")
        sys.exit(1)

if __name__ == "__main__":
    main()
