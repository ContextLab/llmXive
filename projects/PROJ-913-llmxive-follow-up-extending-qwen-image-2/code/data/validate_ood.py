import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
import numpy as np

from config import PROJECT_ROOT
from utils.logger import get_logger

# Constants
COSINE_SIMILARITY_THRESHOLD = 0.3
ID_PROMPT_FILE = "data/prompts/pilot_in_distribution.csv"
OOD_PROMPT_FILE = "data/prompts/pilot_ood.csv"
OUTPUT_REPORT = "data/prompts/validation_report.json"

logger = get_logger(__name__)

def load_prompts(filepath: str) -> List[str]:
    """Load prompts from a CSV file (assumes 'prompt' or 'text' column)."""
    path = PROJECT_ROOT / filepath
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    
    prompts = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Handle potential column name variations
        prompt_col = None
        for col in reader.fieldnames:
            if col.lower() in ['prompt', 'text', 'description']:
                prompt_col = col
                break
        
        if not prompt_col:
            raise ValueError(f"Could not find prompt column in {path}. Headers: {reader.fieldnames}")
        
        for row in reader:
            prompts.append(row[prompt_col].strip())
    
    return prompts

def compute_embeddings(prompts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> np.ndarray:
    """
    Compute embeddings for a list of prompts using a lightweight sentence transformer.
    Falls back to a simple TF-IDF approach if transformers are unavailable, 
    but prefers the real model for accuracy.
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(model_name)
        embeddings = model.encode(prompts, convert_to_numpy=True, show_progress_bar=False)
        logger.info(f"Computed embeddings for {len(prompts)} prompts using {model_name}")
        return embeddings
    except ImportError:
        logger.warning("sentence-transformers not installed. Falling back to basic TF-IDF embedding.")
        # Fallback: simple character n-gram based embedding (very basic, but real calculation)
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(ngram_range=(1, 3), max_features=100)
        embeddings = vectorizer.fit_transform(prompts).toarray()
        # Normalize to unit length for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms
        logger.info(f"Computed fallback TF-IDF embeddings for {len(prompts)} prompts")
        return embeddings

def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(emb1, emb2) / (norm1 * norm2))

def validate_ood_prompts(id_prompts: List[str], ood_prompts: List[str]) -> Dict[str, Any]:
    """
    Validate OOD prompts by computing cosine similarity between OOD embeddings 
    and the centroid of ID embeddings.
    
    Returns a report dict with validation status and metrics.
    """
    logger.info(f"Validating {len(ood_prompts)} OOD prompts against {len(id_prompts)} ID prompts")
    
    # Compute embeddings
    id_embeddings = compute_embeddings(id_prompts)
    ood_embeddings = compute_embeddings(ood_prompts)
    
    # Compute ID centroid
    id_centroid = np.mean(id_embeddings, axis=0)
    id_centroid_norm = np.linalg.norm(id_centroid)
    if id_centroid_norm > 0:
        id_centroid = id_centroid / id_centroid_norm
    
    # Compute similarities
    similarities = []
    max_similarity = 0.0
    max_sim_prompt_idx = -1
    
    for i, ood_emb in enumerate(ood_embeddings):
        ood_emb_norm = np.linalg.norm(ood_emb)
        if ood_emb_norm > 0:
            ood_emb_normalized = ood_emb / ood_emb_norm
            sim = compute_cosine_similarity(id_centroid, ood_emb_normalized)
        else:
            sim = 0.0
        
        similarities.append(sim)
        if sim > max_similarity:
            max_similarity = sim
            max_sim_prompt_idx = i
    
    # Determine pass/fail
    is_valid = max_similarity <= COSINE_SIMILARITY_THRESHOLD
    status = "PASS" if is_valid else "FAIL"
    
    report = {
        "status": status,
        "threshold": COSINE_SIMILARITY_THRESHOLD,
        "max_similarity": max_similarity,
        "mean_similarity": float(np.mean(similarities)),
        "std_similarity": float(np.std(similarities)),
        "num_id_prompts": len(id_prompts),
        "num_ood_prompts": len(ood_prompts),
        "failed_prompt_index": max_sim_prompt_idx if not is_valid else None,
        "failed_prompt_text": ood_prompts[max_sim_prompt_idx] if not is_valid else None,
        "all_similarities": similarities
    }
    
    return report

def main():
    """Main entry point for OOD validation."""
    logger.info("Starting OOD Prompt Validation (T016)")
    
    try:
        # Load prompts
        id_prompts = load_prompts(ID_PROMPT_FILE)
        ood_prompts = load_prompts(OOD_PROMPT_FILE)
        
        if not id_prompts:
            raise ValueError("No ID prompts found. Ensure pilot_in_distribution.csv is populated.")
        if not ood_prompts:
            raise ValueError("No OOD prompts found. Ensure pilot_ood.csv is populated.")
        
        logger.info(f"Loaded {len(id_prompts)} ID prompts and {len(ood_prompts)} OOD prompts")
        
        # Validate
        report = validate_ood_prompts(id_prompts, ood_prompts)
        
        # Save report
        output_path = PROJECT_ROOT / OUTPUT_REPORT
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {output_path}")
        
        # Check result and abort if necessary
        if report["status"] == "FAIL":
            logger.critical(f"[CRITICAL: DATA LEAKAGE DETECTED] Max similarity {report['max_similarity']:.4f} exceeds threshold {COSINE_SIMILARITY_THRESHOLD}")
            logger.critical(f"Failed prompt: {report['failed_prompt_text']}")
            # Exit with code 1 to halt pipeline
            import sys
            sys.exit(1)
        else:
            logger.info(f"Validation PASSED. Max similarity: {report['max_similarity']:.4f} <= {COSINE_SIMILARITY_THRESHOLD}")
            
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()