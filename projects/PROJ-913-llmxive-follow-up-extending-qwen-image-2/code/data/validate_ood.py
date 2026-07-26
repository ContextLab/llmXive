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
from typing import Dict, List, Any, Tuple
import numpy as np

# Import project utilities and config
from config import PROJECT_ROOT
from utils.logger import get_logger
from utils.seeding import set_global_seed

# CLIP imports
try:
    import torch
    from transformers import CLIPModel, CLIPProcessor
except ImportError as e:
    print(f"CRITICAL: Required libraries for CLIP not found. Run: pip install transformers torch")
    sys.exit(1)

# Configuration constants
CLIP_MODEL_ID = "openai/clip-vit-large-patch14"
SIMILARITY_THRESHOLD = 0.3
OUTPUT_REPORT_PATH = PROJECT_ROOT / "data" / "prompts" / "validation_report.json"
ID_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "pilot_in_distribution.csv"
OOD_PROMPTS_PATH = PROJECT_ROOT / "data" / "prompts" / "pilot_ood.csv"

# Initialize logger
logger = get_logger(__name__)

def load_prompts(file_path: Path) -> List[str]:
    """
    Load prompts from a CSV file. Expects a 'prompt' column.
    """
    if not file_path.exists():
        logger.error(f"Prompt file not found: {file_path}")
        sys.exit(1)
    
    prompts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'prompt' not in reader.fieldnames:
                logger.error(f"CSV file {file_path} missing 'prompt' column. Headers: {reader.fieldnames}")
                sys.exit(1)
            for row in reader:
                text = row['prompt'].strip()
                if text:
                    prompts.append(text)
    except Exception as e:
        logger.error(f"Failed to load prompts from {file_path}: {e}")
        sys.exit(1)
    
    if not prompts:
        logger.error(f"No valid prompts found in {file_path}")
        sys.exit(1)
        
    logger.info(f"Loaded {len(prompts)} prompts from {file_path}")
    return prompts

def compute_embeddings(prompts: List[str], processor: CLIPProcessor, model: CLIPModel, device: str) -> np.ndarray:
    """
    Compute CLIP embeddings for a list of text prompts.
    Returns a numpy array of shape (N, D).
    """
    logger.info("Computing embeddings with CLIP...")
    inputs = processor(text=prompts, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        text_outputs = model.get_text_features(**inputs)
        # Normalize embeddings for cosine similarity
        text_outputs = text_outputs / text_outputs.norm(p=2, dim=-1, keepdim=True)
    
    embeddings = text_outputs.cpu().numpy()
    logger.info(f"Computed embeddings with shape: {embeddings.shape}")
    return embeddings

def compute_cosine_similarity(id_embeddings: np.ndarray, ood_embeddings: np.ndarray) -> Tuple[float, int]:
    """
    Compute the maximum cosine similarity between any OOD embedding and any ID centroid.
    Returns (max_similarity, index_of_max).
    """
    # Compute centroids for ID set (mean of all ID embeddings)
    # The task asks for similarity to "ID centroids" (plural). 
    # Standard practice for "similarity to ID" is similarity to the ID cluster centroid.
    # If multiple centroids were intended (e.g., per class), the data structure would differ.
    # We assume a single centroid for the ID set.
    id_centroid = np.mean(id_embeddings, axis=0, keepdims=True)
    
    # Normalize centroid
    id_centroid = id_centroid / (np.linalg.norm(id_centroid, axis=1, keepdims=True) + 1e-9)
    
    # Compute cosine similarities (dot product since vectors are normalized)
    similarities = np.dot(ood_embeddings, id_centroid.T).flatten()
    
    max_sim = float(np.max(similarities))
    max_idx = int(np.argmax(similarities))
    
    return max_sim, max_idx

def validate_ood_prompts() -> Dict[str, Any]:
    """
    Main validation logic.
    """
    set_global_seed() # Ensure reproducibility if needed for any internal ops
    
    # Check input files exist
    if not ID_PROMPTS_PATH.exists():
        logger.error(f"ID Prompts file not found: {ID_PROMPTS_PATH}. Ensure T015a-1 has run.")
        sys.exit(1)
    if not OOD_PROMPTS_PATH.exists():
        logger.error(f"OOD Prompts file not found: {OOD_PROMPTS_PATH}. Ensure T015a has run.")
        sys.exit(1)

    # Load data
    id_prompts = load_prompts(ID_PROMPTS_PATH)
    ood_prompts = load_prompts(OOD_PROMPTS_PATH)

    # Setup CLIP
    device = "cpu" # Force CPU as per project constraints
    logger.info(f"Loading CLIP model {CLIP_MODEL_ID} on {device}...")
    
    try:
        processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
        model = CLIPModel.from_pretrained(CLIP_MODEL_ID)
        model.to(device)
        model.eval()
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        sys.exit(1)

    # Compute embeddings
    id_embeddings = compute_embeddings(id_prompts, processor, model, device)
    ood_embeddings = compute_embeddings(ood_prompts, processor, model, device)

    # Compute similarity
    max_sim, max_idx = compute_cosine_similarity(id_embeddings, ood_embeddings)
    
    logger.info(f"Max Cosine Similarity: {max_sim:.4f} (Threshold: {SIMILARITY_THRESHOLD})")
    logger.info(f"Most similar OOD prompt index: {max_idx}")

    # Determine status
    status = "pass" if max_sim <= SIMILARITY_THRESHOLD else "fail"
    
    report = {
        "status": status,
        "max_similarity": float(max_sim),
        "threshold": float(SIMILARITY_THRESHOLD),
        "id_prompt_count": len(id_prompts),
        "ood_prompt_count": len(ood_prompts),
        "most_similar_ood_index": max_idx,
        "most_similar_ood_prompt": ood_prompts[max_idx] if max_idx < len(ood_prompts) else None
    }

    # Write report
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {OUTPUT_REPORT_PATH}")

    # Abort Mechanism
    if status == "fail":
        logger.critical("[CRITICAL: DATA LEAKAGE DETECTED]")
        logger.critical(f"OOD prompts are too similar to ID prompts (max sim: {max_sim:.4f} > {SIMILARITY_THRESHOLD}).")
        sys.exit(101)
    
    return report

def main():
    """
    Entry point.
    """
    try:
        result = validate_ood_prompts()
        print(f"Validation Successful: {result['status']}")
        sys.exit(0)
    except SystemExit as e:
        # Re-raise system exits to allow correct exit codes
        raise
    except Exception as e:
        logger.critical(f"Validation failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()