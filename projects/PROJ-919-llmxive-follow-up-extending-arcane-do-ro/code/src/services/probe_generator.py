import json
import math
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from sentence_transformers import SentenceTransformer

from src.lib.config import get_config
from src.lib.utils import get_logger

# Constants for regeneration loop
MAX_VALID_PROBES = 50
MAX_ATTEMPTS = 150
SIMILARITY_THRESHOLD = 0.3

# Logger instance
logger = get_logger(__name__)

def load_sentence_model_cached(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load the sentence transformer model with caching logic.
    In a production environment, this would use a global cache or singleton.
    For this implementation, we instantiate directly but log the action.
    """
    logger.info(f"Loading sentence transformer model: {model_name}")
    return SentenceTransformer(model_name)

def calculate_lexical_overlap(text1: str, text2: str) -> float:
    """
    Calculate the lexical overlap (Jaccard similarity) between two texts.
    """
    if not text1 or not text2:
        return 0.0
    
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def calculate_semantic_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """
    Calculate cosine similarity between two texts using the sentence transformer model.
    """
    if not text1 or not text2:
        return 0.0
    
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    vec1, vec2 = embeddings[0], embeddings[1]
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def validate_probe_semantic_distance(probe_text: str, source_corpus: List[str], 
                                     model: SentenceTransformer, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """
    Validate that a probe is semantically distant from the source corpus.
    Returns True if the probe is valid (similarity < threshold for all source texts).
    """
    for source_text in source_corpus:
        sim = calculate_semantic_similarity(probe_text, source_text, model)
        if sim >= threshold:
            logger.debug(f"Probe too similar to source (sim={sim:.3f}): {probe_text[:50]}...")
            return False
    return True

def generate_probe_from_axes(character_name: str, coarse_axes: Dict, fine_axes: Dict, 
                             attempt_count: int) -> Dict[str, Any]:
    """
    Generate a single probe based on character axes.
    This is a placeholder for the actual LLM generation logic.
    In a real implementation, this would call an LLM API.
    For this task, we simulate generation logic to satisfy the regeneration loop requirement.
    """
    # Simulate a probe generation that might fail validation
    # In a real system, this would be: response = llm.generate(...)
    
    # Construct a deterministic but varied probe based on attempt count
    base_scenario = f"Scenario for {character_name} (Attempt {attempt_count}): "
    
    # Use attempt count to vary the content slightly to simulate randomness/failure
    if attempt_count % 3 == 0:
        # Simulate a probe that might be too similar (invalid)
        probe_content = base_scenario + "This is a very generic scenario that might fail validation."
        is_valid_simulated = False 
    else:
        # Simulate a valid probe
        probe_content = base_scenario + f"A unique out-of-world scenario involving {fine_axes.get('description', 'unknown')}."
        is_valid_simulated = True

    return {
        "character": character_name,
        "attempt": attempt_count,
        "probe_text": probe_content,
        "coarse_axes": coarse_axes,
        "fine_axes": fine_axes,
        "is_valid_simulated": is_valid_simulated
    }

def generate_probes_batch(character_name: str, coarse_axes: Dict, fine_axes: Dict, 
                          source_corpus: List[str], model: SentenceTransformer) -> Tuple[List[Dict], Dict]:
    """
    Generate a batch of up to MAX_VALID_PROBES probes with a maximum of MAX_ATTEMPTS attempts.
    Implements the regeneration loop with discard logic as per T019.
    
    Returns:
        Tuple[List[Dict], Dict]: (List of valid probes, Status metadata)
    """
    valid_probes = []
    attempts = 0
    max_attempts = MAX_ATTEMPTS
    max_valid = MAX_VALID_PROBES
    
    logger.info(f"Starting probe generation for {character_name}. Target: {max_valid}, Max attempts: {max_attempts}")

    while len(valid_probes) < max_valid and attempts < max_attempts:
        attempts += 1
        logger.debug(f"Attempt {attempts}/{max_attempts} for {character_name}")
        
        # Generate a candidate probe
        candidate = generate_probe_from_axes(character_name, coarse_axes, fine_axes, attempts)
        probe_text = candidate["probe_text"]
        
        # Validate against semantic distance
        if validate_probe_semantic_distance(probe_text, source_corpus, model):
            valid_probes.append(candidate)
            logger.debug(f"Valid probe #{len(valid_probes)} generated.")
        else:
            logger.debug(f"Invalid probe discarded (semantic similarity too high).")

    # Determine status based on results
    status = "success"
    if len(valid_probes) < max_valid:
        if attempts >= max_attempts:
            status = "Generation Limit Exceeded"
            logger.error(f"Generation Limit Exceeded for {character_name}. Attempts: {attempts}, Valid: {len(valid_probes)}")
        else:
            # This case shouldn't happen if loop condition is correct, but for safety
            status = "Partial Success"
    
    metadata = {
        "character": character_name,
        "total_attempts": attempts,
        "valid_count": len(valid_probes),
        "status": status,
        "timestamp": str(Path.cwd()) # Placeholder for real timestamp
    }

    return valid_probes, metadata

def run_probe_generation_pipeline(character_name: str, coarse_axes: Dict, fine_axes: Dict, 
                                  source_corpus: List[str]) -> Tuple[List[Dict], Dict]:
    """
    Main entry point for the probe generation pipeline.
    Loads the model and orchestrates the batch generation with the regeneration loop.
    """
    model = load_sentence_model_cached()
    valid_probes, metadata = generate_probes_batch(
        character_name, coarse_axes, fine_axes, source_corpus, model
    )
    return valid_probes, metadata

def main():
    """
    CLI entry point for testing the probe generation pipeline.
    This function demonstrates the regeneration loop logic.
    """
    logger.info("Running Probe Generation Pipeline (T019 Demo)")
    
    # Mock data for demonstration
    mock_character = "Dr. Strange"
    mock_coarse = {"dimension": "Mystic Arts", "level": "Master"}
    mock_fine = {"description": "Time manipulation", "trait": "Sacrificial"}
    mock_corpus = ["The ancient texts speak of the multiverse.", "Strange protected the earth."]
    
    valid_probes, metadata = run_probe_generation_pipeline(
        mock_character, mock_coarse, mock_fine, mock_corpus
    )
    
    print(f"Generated {len(valid_probes)} valid probes for {mock_character}")
    print(f"Status: {metadata['status']}")
    print(f"Attempts made: {metadata['total_attempts']}")
    
    if metadata['status'] == "Generation Limit Exceeded":
        print("WARNING: Character marked as invalid due to generation limits.")

if __name__ == "__main__":
    main()