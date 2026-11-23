"""
Validate Out-of-Distribution (OOD) prompts against In-Distribution (ID) centroids.

This script computes cosine similarity between OOD prompt embeddings and ID centroids
using the `openai/clip-vit-large-patch14` model.

It enforces a strict threshold (0.3). If any OOD prompt exceeds this similarity,
the script aborts with exit code 101 and logs a critical error.

Output: data/prompts/validation_report.json
"""
import json
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from transformers import CLIPModel, CLIPProcessor
import torch

# Local imports based on API surface
from config import PROJECT_ROOT
from utils.logger import get_logger
from utils.seeding import set_global_seed

# Constants
SIMILARITY_THRESHOLD = 0.3
CLIP_MODEL_NAME = "clip-vit-large-patch14"

def load_prompts(file_path: Path) -> List[str]:
    """Load prompts from a CSV file (expects a 'prompt' column)."""
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    
    prompts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'prompt' not in reader.fieldnames:
            raise ValueError(f"CSV file {file_path} must contain a 'prompt' column.")
        for row in reader:
            prompts.append(row['prompt'])
    return prompts

def compute_embeddings(prompts: List[str], logger: logging.Logger) -> np.ndarray:
    """
    Compute CLIP embeddings for a list of prompts.
    Uses CLIP-ViT-Large-Patch14 as specified in T016.
    Returns a numpy array of shape (N, D).
    """
    logger.info(f"Loading CLIP model: {CLIP_MODEL_NAME}")
    try:
        model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
        processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        raise

    # Move to CPU (project is CPU-only)
    device = torch.device("cpu")
    model.to(device)
    model.eval()

    logger.info(f"Computing embeddings for {len(prompts)} prompts...")
    all_embeddings = []

    # Batch processing to manage memory, though CLIP is relatively lightweight
    batch_size = 32
    with torch.no_grad():
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i : i + batch_size]
            inputs = processor(
                text=batch_prompts, 
                return_tensors="pt", 
                padding=True, 
                truncation=True,
                max_length=77
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Get text embeddings
            outputs = model.get_text_features(**inputs)
            # Normalize embeddings (CLIP embeddings are usually normalized, but explicit is good)
            embeddings = outputs / outputs.norm(dim=-1, keepdim=True)
            all_embeddings.append(embeddings.cpu().numpy())

    embeddings_np = np.vstack(all_embeddings)
    logger.info(f"Embeddings computed. Shape: {embeddings_np.shape}")
    return embeddings_np

def compute_cosine_similarity(ood_embeddings: np.ndarray, id_centroid: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between OOD embeddings and the ID centroid.
    id_centroid is expected to be a 1D array (D,).
    Returns a 1D array of similarities.
    """
    # Ensure centroid is 2D for broadcasting if necessary, though dot product handles 1D
    # Normalize centroid just in case
    id_centroid_norm = id_centroid / (np.linalg.norm(id_centroid) + 1e-8)
    
    # Normalize OOD embeddings (should already be normalized from CLIP, but safe to do)
    ood_norms = np.linalg.norm(ood_embeddings, axis=1, keepdims=True)
    ood_normalized = ood_embeddings / (ood_norms + 1e-8)

    # Cosine similarity is dot product of normalized vectors
    similarities = np.dot(ood_normalized, id_centroid_norm)
    return similarities

def validate_ood_prompts(
    id_prompts_path: Path, 
    ood_prompts_path: Path, 
    output_path: Path, 
    logger: logging.Logger
) -> bool:
    """
    Main validation logic.
    1. Load ID and OOD prompts.
    2. Compute ID centroid.
    3. Compute OOD embeddings.
    4. Compute cosine similarities.
    5. Check threshold.
    6. Save report.
    7. Return True if valid, False if leakage detected.
    """
    # 1. Load Prompts
    logger.info(f"Loading ID prompts from {id_prompts_path}")
    id_prompts = load_prompts(id_prompts_path)
    logger.info(f"Loading OOD prompts from {ood_prompts_path}")
    ood_prompts = load_prompts(ood_prompts_path)

    if not id_prompts:
        raise ValueError("ID prompt list is empty. Cannot compute centroid.")
    if not ood_prompts:
        logger.warning("OOD prompt list is empty. Validation passed trivially.")
        # Write empty report
        report = {
            "status": "PASS",
            "message": "No OOD prompts to validate.",
            "max_similarity": 0.0,
            "threshold": SIMILARITY_THRESHOLD,
            "failed_prompts": []
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return True

    # 2. Compute Embeddings
    id_embeddings = compute_embeddings(id_prompts, logger)
    ood_embeddings = compute_embeddings(ood_prompts, logger)

    # 3. Compute ID Centroid (Mean of ID embeddings)
    id_centroid = np.mean(id_embeddings, axis=0)
    logger.info(f"ID Centroid computed. Shape: {id_centroid.shape}")

    # 4. Compute Similarities
    similarities = compute_cosine_similarity(ood_embeddings, id_centroid)
    max_sim = float(np.max(similarities))
    failed_indices = np.where(similarities > SIMILARITY_THRESHOLD)[0]

    # 5. Check Threshold
    report = {
        "status": "PASS",
        "message": "All OOD prompts are sufficiently distinct from ID centroid.",
        "threshold": SIMILARITY_THRESHOLD,
        "max_similarity": max_sim,
        "mean_similarity": float(np.mean(similarities)),
        "num_id_prompts": len(id_prompts),
        "num_ood_prompts": len(ood_prompts),
        "failed_prompts": []
    }

    if len(failed_indices) > 0:
        report["status"] = "FAIL"
        report["message"] = f"DATA LEAKAGE DETECTED: {len(failed_indices)} OOD prompts exceed similarity threshold."
        logger.error(f"[CRITICAL: DATA LEAKAGE DETECTED] {len(failed_indices)} prompts exceeded threshold {SIMILARITY_THRESHOLD}")
        
        # Collect details of failed prompts
        failed_details = []
        for idx in failed_indices:
            failed_details.append({
                "index": int(idx),
                "prompt": ood_prompts[idx],
                "similarity": float(similarities[idx])
            })
        report["failed_prompts"] = failed_details
        
        # Save report before aborting
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return False
    
    # 6. Save Report (Pass)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation passed. Max similarity: {max_sim:.4f} < {SIMILARITY_THRESHOLD}")
    return True

def main():
    """Entry point for the validation script."""
    logger = get_logger("validate_ood")
    logger.info("Starting OOD Validation...")

    # Define paths based on T015a output and T016 requirement
    # T015a outputs: data/prompts/pilot_in_distribution.csv, data/prompts/pilot_ood.csv
    id_prompts_path = PROJECT_ROOT / "data" / "prompts" / "pilot_in_distribution.csv"
    ood_prompts_path = PROJECT_ROOT / "data" / "prompts" / "pilot_ood.csv"
    output_path = PROJECT_ROOT / "data" / "prompts" / "validation_report.json"

    try:
        is_valid = validate_ood_prompts(id_prompts_path, ood_prompts_path, output_path, logger)
        
        if not is_valid:
            logger.critical("[CRITICAL: DATA LEAKAGE DETECTED] Exiting with code 1.")
            sys.exit(1)
        
        logger.info("Validation completed successfully.")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
