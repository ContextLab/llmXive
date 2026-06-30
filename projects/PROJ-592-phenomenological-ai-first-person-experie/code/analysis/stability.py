"""
Stability Analysis Module for Phenomenological AI Project.

Computes Semantic Stability metrics by calculating cosine similarity between
embeddings of repeated generations for the same prompt/strategy condition.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Project-relative imports based on provided API surface
from utils.logging import get_logger, setup_logging
from utils.io import safe_write_csv, load_json, ensure_dir

# Configure logger
logger = get_logger(__name__)

# Constants
DEFAULT_MODEL = "all-MiniLM-L6-v2"  # CPU-safe, small embedding model
SIMILARITY_THRESHOLD = 0.0  # Minimum similarity to be considered valid (no lower bound)
MIN_PAIRS_REQUIRED = 1  # Minimum number of pairs needed to compute a score

class StabilityError(Exception):
    """Custom exception for stability analysis failures."""
    pass

def load_embedding_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """
    Load the sentence embedding model.
    
    Args:
        model_name: HuggingFace model ID for sentence transformers.
        
    Returns:
        Loaded SentenceTransformer model.
    """
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model {model_name}: {e}")
        raise StabilityError(f"Failed to load embedding model: {e}")

def compute_embeddings(
    model: SentenceTransformer, 
    texts: List[str], 
    batch_size: int = 32
) -> np.ndarray:
    """
    Compute embeddings for a list of texts.
    
    Args:
        model: Loaded SentenceTransformer model.
        texts: List of text strings to embed.
        batch_size: Number of texts to process in parallel.
        
    Returns:
        Numpy array of embeddings (shape: [num_texts, embedding_dim]).
    """
    if not texts:
        return np.array([])
    
    logger.debug(f"Computing embeddings for {len(texts)} texts.")
    try:
        embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return embeddings
    except Exception as e:
        logger.error(f"Failed to compute embeddings: {e}")
        raise StabilityError(f"Embedding computation failed: {e}")

def compute_cosine_similarity(
    vec_a: np.ndarray, 
    vec_b: np.ndarray
) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec_a: First vector.
        vec_b: Second vector.
        
    Returns:
        Cosine similarity score (float between -1 and 1).
    """
    if vec_a.size == 0 or vec_b.size == 0:
        return 0.0
    
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

def group_generations_by_condition(
    samples: List[Dict[str, Any]]
) -> Dict[Tuple[str, str], List[str]]:
    """
    Group generation samples by (prompt_id, strategy) to identify repeated generations.
    
    Args:
        samples: List of generation sample dictionaries.
        
    Returns:
        Dictionary mapping (prompt_id, strategy) to list of text contents.
    """
    groups = {}
    for sample in samples:
        # Expecting standard fields from runner.py
        prompt_id = sample.get("prompt_id") or sample.get("prompt")
        strategy = sample.get("strategy")
        
        if not prompt_id or not strategy:
            logger.warning(f"Skipping sample missing prompt_id or strategy: {sample.get('id', 'unknown')}")
            continue
        
        key = (str(prompt_id), str(strategy))
        text = sample.get("text") or sample.get("content")
        
        if not text:
            logger.warning(f"Skipping sample with no text content: {sample.get('id', 'unknown')}")
            continue
        
        if key not in groups:
            groups[key] = []
        groups[key].append(text)
        
    return groups

def compute_stability_scores(
    groups: Dict[Tuple[str, str], List[str]],
    model: SentenceTransformer
) -> List[Dict[str, Any]]:
    """
    Compute pairwise cosine similarity for repeated generations within each condition.
    
    Args:
        groups: Dictionary of grouped texts by condition.
        model: Loaded embedding model.
        
    Returns:
        List of dictionaries containing stability metrics per condition.
    """
    results = []
    
    for (prompt_id, strategy), texts in groups.items():
        if len(texts) < 2:
            logger.debug(f"Skipping condition ({prompt_id}, {strategy}): only {len(texts)} sample(s).")
            continue
        
        # Compute embeddings for all texts in this group
        embeddings = compute_embeddings(model, texts)
        
        if embeddings.shape[0] != len(texts):
            logger.error(f"Embedding mismatch for condition ({prompt_id}, {strategy}).")
            continue
        
        # Compute pairwise similarities (upper triangle only to avoid duplicates and self)
        similarities = []
        n = len(texts)
        for i in range(n):
            for j in range(i + 1, n):
                sim = compute_cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        if not similarities:
            logger.warning(f"No pairs computed for condition ({prompt_id}, {strategy}).")
            continue
        
        # Aggregate metrics
        mean_sim = float(np.mean(similarities))
        std_sim = float(np.std(similarities))
        min_sim = float(np.min(similarities))
        max_sim = float(np.max(similarities))
        
        results.append({
            "prompt_id": prompt_id,
            "strategy": strategy,
            "num_samples": n,
            "num_pairs": len(similarities),
            "stability_mean": mean_sim,
            "stability_std": std_sim,
            "stability_min": min_sim,
            "stability_max": max_sim
        })
        
        logger.debug(f"Condition ({prompt_id}, {strategy}): Mean Stability = {mean_sim:.4f}")
        
    return results

def run_stability_analysis(
    input_path: str,
    output_path: str,
    model_name: str = DEFAULT_MODEL
) -> List[Dict[str, Any]]:
    """
    Main entry point for running stability analysis on generated reports.
    
    Args:
        input_path: Path to JSON file containing generation samples.
        output_path: Path to save the stability scores CSV.
        model_name: Name of the sentence transformer model to use.
        
    Returns:
        List of stability score dictionaries.
    """
    # Load input data
    logger.info(f"Loading generation samples from {input_path}")
    try:
        samples = load_json(input_path)
        if not isinstance(samples, list):
            samples = [samples]
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        raise StabilityError(f"Input loading failed: {e}")
    
    if not samples:
        logger.warning("Input file is empty. No stability analysis performed.")
        return []
    
    # Load model
    model = load_embedding_model(model_name)
    
    # Group by condition
    groups = group_generations_by_condition(samples)
    logger.info(f"Identified {len(groups)} unique conditions for stability analysis.")
    
    # Compute scores
    scores = compute_stability_scores(groups, model)
    
    # Ensure output directory exists
    ensure_dir(output_path)
    
    # Save results
    if scores:
        logger.info(f"Saving {len(scores)} stability scores to {output_path}")
        safe_write_csv(scores, output_path)
    else:
        logger.warning("No stability scores computed. Creating empty output file.")
        # Create empty file with headers if possible, or just touch it
        Path(output_path).touch()
        
    return scores

def main():
    """CLI entry point for stability analysis."""
    import argparse
    
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Compute semantic stability scores for generated reports.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/raw/generation_corpus.json",
        help="Path to input JSON file containing generation samples."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/stability_scores.csv",
        help="Path to output CSV file for stability scores."
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default=DEFAULT_MODEL,
        help=f"HuggingFace model name for embeddings (default: {DEFAULT_MODEL})."
    )
    
    args = parser.parse_args()
    
    try:
        scores = run_stability_analysis(args.input, args.output, args.model)
        logger.info(f"Stability analysis complete. {len(scores)} conditions analyzed.")
    except StabilityError as e:
        logger.error(f"Stability analysis failed: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during stability analysis: {e}")
        exit(1)

if __name__ == "__main__":
    main()