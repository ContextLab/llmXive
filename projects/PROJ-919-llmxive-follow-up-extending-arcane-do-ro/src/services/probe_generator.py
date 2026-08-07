"""
Probe Generator Service for ArcANE.

Implements logic to generate 'Out-of-World' scenario prompts based on character axes.
Includes regeneration loops, semantic validation, and error handling for generation limits.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sentence_transformers import SentenceTransformer

# Import from local project structure
from src.lib.utils import get_logger
from src.lib.config import get_config
from src.services.axis_generator import load_sentence_model_cached
from src.cli.axis_input import calculate_semantic_similarity

# Configure logging
logger = get_logger(__name__)

# Constants
MIN_VALID_PROBES = 50
MAX_GENERATION_ATTEMPTS = 150
SEMANTIC_SIMILARITY_THRESHOLD = 0.3
SIMILARITY_MODEL_NAME = "all-MiniLM-L6-v2"

def generate_single_probe_prompt(character_name: str, coarse_axis: str, fine_axis: str, attempt: int) -> str:
    """
    Generates a single prompt for probe generation.
    In a real implementation, this would call an LLM API.
    For this implementation, we simulate the generation logic with a deterministic
    structure that can be replaced by an actual model call.
    """
    # Placeholder for actual LLM call logic
    # In production, this would be: response = llm_model.generate(prompt)
    prompt = (
        f"Character: {character_name}\n"
        f"Coarse Axis: {coarse_axis}\n"
        f"Fine Axis: {fine_axis}\n"
        f"Attempt: {attempt}\n"
        "Task: Generate an 'Out-of-World' scenario where this character faces a situation "
        "completely unrelated to their original narrative context. The scenario should "
        "test the psychological axes defined above."
    )
    return prompt

def validate_probe_against_source(probe_text: str, source_corpus: List[str]) -> bool:
    """
    Validates that a generated probe is semantically distant from the source text.
    Returns True if valid (similarity < threshold), False otherwise.
    """
    if not source_corpus:
        return True

    model = load_sentence_model_cached(SIMILARITY_MODEL_NAME)
    
    # Calculate average similarity against source corpus
    probe_embedding = model.encode([probe_text], convert_to_tensor=True)
    source_embeddings = model.encode(source_corpus, convert_to_tensor=True)
    
    similarities = []
    for src_emb in source_embeddings:
        sim = np.dot(probe_embedding[0].cpu().numpy(), src_emb.cpu().numpy()) / (
            np.linalg.norm(probe_embedding[0].cpu().numpy()) * np.linalg.norm(src_emb.cpu().numpy())
        )
        similarities.append(sim)
    
    avg_similarity = np.mean(similarities)
    is_valid = avg_similarity < SEMANTIC_SIMILARITY_THRESHOLD
    
    if not is_valid:
        logger.debug(f"Probe rejected: similarity {avg_similarity:.4f} >= {SEMANTIC_SIMILARITY_THRESHOLD}")
    
    return is_valid

def generate_probe_batch(
    character_name: str,
    coarse_axis: str,
    fine_axis: str,
    source_corpus: List[str],
    max_attempts: int = MAX_GENERATION_ATTEMPTS,
    min_valid: int = MIN_VALID_PROBES
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generates a batch of validated probes with regeneration logic.
    
    Args:
        character_name: Name of the character
        coarse_axis: Coarse psychological axis definition
        fine_axis: Fine psychological axis definition
        source_corpus: List of source text segments to avoid
        max_attempts: Maximum generation attempts before giving up
        min_valid: Minimum number of valid probes required
        
    Returns:
        Tuple of (list of valid probes, metadata dict)
    """
    valid_probes = []
    attempts = 0
    discarded_count = 0
    start_time = time.time()
    
    logger.info(f"Starting probe generation for '{character_name}' (min={min_valid}, max_attempts={max_attempts})")
    
    while len(valid_probes) < min_valid and attempts < max_attempts:
        attempts += 1
        try:
            # Generate candidate probe
            # In a real scenario, this would involve calling an LLM with temperature
            # For this implementation, we simulate a candidate
            candidate_text = f"Scenario for {character_name}: {coarse_axis} vs {fine_axis} in a {attempts}-dimensional space."
            
            # Validate against source text
            if validate_probe_against_source(candidate_text, source_corpus):
                probe_record = {
                    "character": character_name,
                    "coarse_axis": coarse_axis,
                    "fine_axis": fine_axis,
                    "probe_text": candidate_text,
                    "attempt_number": attempts,
                    "timestamp": time.time()
                }
                valid_probes.append(probe_record)
                logger.debug(f"Valid probe #{len(valid_probes)} generated on attempt {attempts}")
            else:
                discarded_count += 1
                logger.debug(f"Probe discarded on attempt {attempts} (semantic similarity too high)")
                
        except Exception as e:
            logger.error(f"Error generating probe on attempt {attempts}: {e}")
            discarded_count += 1
            continue
    
    elapsed_time = time.time() - start_time
    
    # Determine final status
    status = "success" if len(valid_probes) >= min_valid else "limit_exceeded"
    
    if len(valid_probes) < min_valid:
        logger.error(
            f"Generation Limit Exceeded for '{character_name}'. "
            f"Generated {len(valid_probes)} valid probes after {attempts} attempts. "
            f"Required: {min_valid}. Proceeding with available probes."
        )
        if attempts > MAX_GENERATION_ATTEMPTS:
            logger.warning(f"Character '{character_name}' marked as invalid due to exceeding {MAX_GENERATION_ATTEMPTS} attempts.")
            status = "invalid"
    
    metadata = {
        "character": character_name,
        "total_attempts": attempts,
        "valid_count": len(valid_probes),
        "discarded_count": discarded_count,
        "status": status,
        "elapsed_seconds": elapsed_time,
        "min_required": min_valid
    }
    
    return valid_probes, metadata

def run_probe_generation_workflow(
    character_data: Dict[str, Any],
    source_corpus: List[str]
) -> List[Dict[str, Any]]:
    """
    Main workflow to generate probes for a character.
    Handles the full lifecycle including logging and error handling.
    """
    character_name = character_data.get("character", "Unknown")
    coarse_axis = character_data.get("coarse_axis", "")
    fine_axis = character_data.get("fine_axis", "")
    
    if not coarse_axis or not fine_axis:
        logger.error(f"Missing axis definitions for character '{character_name}'")
        return []
    
    valid_probes, metadata = generate_probe_batch(
        character_name=character_name,
        coarse_axis=coarse_axis,
        fine_axis=fine_axis,
        source_corpus=source_corpus
    )
    
    # Log final status
    if metadata["status"] == "limit_exceeded":
        logger.warning(
            f"PROBE GENERATION WARNING: '{character_name}' - "
            f"Generation Limit Exceeded. Proceeding with {metadata['valid_count']} valid probes."
        )
    elif metadata["status"] == "invalid":
        logger.error(
            f"PROBE GENERATION ERROR: '{character_name}' - "
            f"Marked as invalid. Attempts exceeded {MAX_GENERATION_ATTEMPTS}."
        )
    
    return valid_probes

def main():
    """
    Entry point for testing the probe generation logic.
    """
    # Sample data for demonstration
    sample_character = {
        "character": "TestHero",
        "coarse_axis": "Optimism vs Pessimism",
        "fine_axis": "Specific behavioral response to failure"
    }
    
    sample_corpus = [
        "The hero faced the dragon with courage.",
        "The village celebrated the victory.",
        "The dark forces gathered at the edge of the forest."
    ]
    
    logger.info("Running probe generation workflow demo...")
    results = run_probe_generation_workflow(sample_character, sample_corpus)
    
    logger.info(f"Generated {len(results)} valid probes.")
    for i, probe in enumerate(results[:3]):  # Show first 3
        logger.info(f"Probe {i+1}: {probe['probe_text'][:100]}...")
    
    if results:
        logger.info("Probe generation completed successfully.")
    else:
        logger.warning("No valid probes generated.")

if __name__ == "__main__":
    main()