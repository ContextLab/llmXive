import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import os

from utils.config import get_model_config, set_seed
from utils.logging_config import get_logger, log_model_switch, log_memory_error, log_fallback_success, log_fallback_failure

logger = get_logger("pattern_mapping")

# Global model cache to avoid reloading
_model_cache: Optional[SentenceTransformer] = None

def get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Loads the sentence-transformer model. Handles fallback logic if the primary model
    fails to load due to memory constraints.
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    config = get_model_config()
    primary_model = model_name
    fallback_model = config.get("fallback_model", "paraphrase-MiniLM-L3-v2")
    
    try:
        logger.info(f"Attempting to load primary model: {primary_model}")
        model = SentenceTransformer(primary_model)
        _model_cache = model
        return model
    except (OSError, RuntimeError) as e:
        if "CUDA" in str(e) or "Memory" in str(e) or "out of memory" in str(e).lower():
            log_memory_error(logger, str(e))
            logger.warning(f"Primary model {primary_model} failed. Switching to fallback: {fallback_model}")
            try:
                model = SentenceTransformer(fallback_model)
                log_model_switch(logger, primary_model, fallback_model, "Memory constraint")
                log_fallback_success(logger, fallback_model)
                _model_cache = model
                return model
            except Exception as fallback_e:
                log_fallback_failure(logger, str(fallback_e))
                raise RuntimeError(f"Failed to load both primary and fallback models: {fallback_e}") from fallback_e
        else:
            # Re-raise if it's not a memory/CUDA issue
            raise

def encode_text(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    """
    Encodes a list of texts into embeddings.
    """
    if not texts:
        return np.array([])
    # Use batch processing for efficiency
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings

def cosine_similarity_matrix(queries: np.ndarray, patterns: np.ndarray) -> np.ndarray:
    """
    Computes cosine similarity between query embeddings and pattern embeddings.
    """
    if queries.size == 0 or patterns.size == 0:
        return np.array([])
    
    # Normalize vectors
    q_norm = np.linalg.norm(queries, axis=1, keepdims=True)
    p_norm = np.linalg.norm(patterns, axis=1, keepdims=True)
    
    # Avoid division by zero
    q_norm = np.where(q_norm == 0, 1, q_norm)
    p_norm = np.where(p_norm == 0, 1, p_norm)
    
    queries_norm = queries / q_norm
    patterns_norm = patterns / p_norm
    
    # Compute dot product
    similarities = np.dot(queries_norm, patterns_norm.T)
    return similarities

def retrieve_top_k_patterns(
    problem_statements: List[str],
    pattern_cards: List[Dict[str, Any]],
    k: int = 3,
    threshold: Optional[float] = None,
    model_name: str = "all-MiniLM-L6-v2"
) -> List[Dict[str, Any]]:
    """
    Retrieves the top-k patterns for each problem statement based on cosine similarity.
    
    Args:
        problem_statements: List of text strings representing problem statements.
        pattern_cards: List of dictionaries containing pattern data (must have 'id' and 'description').
        k: Number of top patterns to return per problem statement.
        threshold: Minimum cosine similarity threshold. Patterns below this are excluded.
        model_name: Name of the sentence-transformer model to use.
    
    Returns:
        A list of dictionaries. Each dictionary corresponds to a problem statement and contains:
        {
            "problem_statement": str,
            "matched_patterns": [
                {"pattern_id": str, "similarity": float},
                ...
            ]
        }
    """
    set_seed(42) # Deterministic behavior for retrieval
    
    if not problem_statements or not pattern_cards:
        logger.warning("Empty input for pattern retrieval.")
        return []

    # Load model
    model = get_model(model_name)

    # Extract pattern descriptions and IDs
    pattern_descriptions = [card.get("description", "") for card in pattern_cards]
    pattern_ids = [card.get("id", f"unknown_{i}") for i, card in enumerate(pattern_cards)]
    
    # Encode all patterns at once
    pattern_embeddings = encode_text(model, pattern_descriptions)
    
    results = []
    
    for i, statement in enumerate(problem_statements):
        # Encode the single statement
        statement_embedding = encode_text(model, [statement])
        
        # Calculate similarities
        similarities = cosine_similarity_matrix(statement_embedding, pattern_embeddings)[0]
        
        # Get indices of top-k similarities
        # Use argpartition for efficiency if k is small compared to N, but for simplicity and correctness:
        top_k_indices = np.argsort(similarities)[::-1][:k]
        
        matched = []
        for idx in top_k_indices:
            sim = float(similarities[idx])
            if threshold is None or sim >= threshold:
                matched.append({
                    "pattern_id": pattern_ids[idx],
                    "similarity": sim
                })
        
        results.append({
            "problem_statement": statement,
            "matched_patterns": matched
        })
        
        # Progress logging for long lists
        if (i + 1) % 10 == 0:
            logger.debug(f"Processed {i+1}/{len(problem_statements)} problem statements.")

    return results

def main():
    """
    Main entry point for testing pattern mapping.
    This function loads the processed corpus and pattern cards,
    runs the retrieval, and saves the results to a JSON file.
    """
    logger.info("Starting Pattern Mapping Pipeline")
    
    # Paths
    corpus_path = Path("data/processed/corpus.jsonl")
    pattern_path = Path("data/processed/pattern_cards.jsonl")
    output_path = Path("data/results/pattern_mapping_results.json")
    
    # Load Config
    config = get_model_config()
    threshold = config.get("similarity_threshold", 0.5)
    k = config.get("top_k_patterns", 3)
    
    # Load Data
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus not found at {corpus_path}. Run data acquisition first.")
    if not pattern_path.exists():
        raise FileNotFoundError(f"Pattern cards not found at {pattern_path}. Run pattern generation first.")
    
    problem_statements = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            # Assuming 'abstract' or 'problem_statement' is the key
            text = data.get("abstract") or data.get("problem_statement")
            if text:
                problem_statements.append(text)
    
    pattern_cards = []
    with open(pattern_path, 'r', encoding='utf-8') as f:
        for line in f:
            pattern_cards.append(json.loads(line))
    
    logger.info(f"Loaded {len(problem_statements)} problem statements and {len(pattern_cards)} pattern cards.")
    
    # Run Retrieval
    results = retrieve_top_k_patterns(
        problem_statements=problem_statements,
        pattern_cards=pattern_cards,
        k=k,
        threshold=threshold
    )
    
    # Save Results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pattern mapping results saved to {output_path}")
    print(f"Successfully wrote {output_path}")

if __name__ == "__main__":
    main()
