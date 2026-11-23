"""
Probe Generator Service for ArcANE.

This module handles the generation of 'Out-of-World' scenario probes based on
character axes. It implements semantic distance checks to ensure probes are
distinct from the source text corpus.
"""

import json
import math
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from sentence_transformers import SentenceTransformer

# Import project configuration and utilities
from src.lib.config import get_config
from src.lib.utils import get_logger

# Constants
SIMILARITY_THRESHOLD = 0.3
MAX_GENERATION_ATTEMPTS = 150
MIN_VALID_PROBES = 50
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Global cache for the embedding model
_model_cache: Optional[SentenceTransformer] = None
_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    """Get or initialize the module logger."""
    global _logger
    if _logger is None:
        _logger = get_logger(__name__)
    return _logger


def load_sentence_model_cached() -> SentenceTransformer:
    """
    Load the sentence-transformer model, caching it in memory for subsequent calls.
    This prevents reloading the model for every probe generation batch.
    """
    global _model_cache
    if _model_cache is None:
        logger = _get_logger()
        logger.info(f"Loading sentence transformer model: {MODEL_NAME}")
        try:
            _model_cache = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
    return _model_cache


def calculate_lexical_overlap(text1: str, text2: str) -> float:
    """
    Calculate the Jaccard index of word sets between two texts.
    Returns a value between 0.0 (no overlap) and 1.0 (identical word sets).
    """
    if not text1 or not text2:
        return 0.0

    # Normalize and tokenize
    set1 = set(re.findall(r'\w+', text1.lower()))
    set2 = set(re.findall(r'\w+', text2.lower()))

    if not set1 or not set2:
        return 0.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0


def calculate_semantic_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """
    Calculate cosine similarity between two text embeddings.
    Returns a value between -1.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0

    try:
        embeddings = model.encode([text1, text2], convert_to_numpy=True, show_progress_bar=False)
        vec1, vec2 = embeddings[0], embeddings[1]

        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(cosine_sim)
    except Exception as e:
        _get_logger().error(f"Error calculating semantic similarity: {e}")
        return 0.0


def validate_probe_semantic_distance(
    probe_text: str,
    source_corpus: List[str],
    model: SentenceTransformer,
    threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[bool, float]:
    """
    Validate that a probe is semantically distant from the source text corpus.

    Args:
        probe_text: The generated probe scenario text.
        source_corpus: A list of text segments from the source material (e.g., character arcs, context).
        model: The loaded sentence-transformer model.
        threshold: Maximum allowed cosine similarity (default 0.3).

    Returns:
        Tuple of (is_valid, max_similarity_found).
        is_valid is True if the probe's similarity to ALL source segments is < threshold.
    """
    if not source_corpus:
        # If no source corpus is provided, we cannot validate distance.
        # We assume valid to allow generation in isolation, but log a warning.
        _get_logger().warning("Source corpus is empty. Skipping semantic distance validation.")
        return True, 0.0

    max_sim = 0.0
    for source_segment in source_corpus:
        if not source_segment.strip():
            continue

        sim = calculate_semantic_similarity(probe_text, source_segment, model)
        if sim > max_sim:
            max_sim = sim

        if max_sim >= threshold:
            _get_logger().debug(f"Probe rejected. Similarity {max_sim:.4f} >= {threshold} to source segment.")
            return False, max_sim

    _get_logger().debug(f"Probe accepted. Max similarity {max_sim:.4f} < {threshold}.")
    return True, max_sim


def generate_probe_from_axes(
    character_name: str,
    coarse_axes: Dict[str, Any],
    fine_axes: Dict[str, Any],
    model_context: Optional[str] = None
) -> str:
    """
    Generates a single probe text based on character axes.
    In a real implementation, this would call an LLM.
    For this task, we simulate the generation logic structure.
    """
    # Placeholder logic to construct a prompt for an LLM
    # In the full pipeline, this would be: response = llm.generate(prompt)
    # Since we are implementing the validation logic (T018), we return a string
    # that represents what the LLM *would* generate.
    
    coarse_desc = coarse_axes.get("description", "")
    fine_desc = fine_axes.get("description", "")
    
    # Construct a deterministic "generated" probe for validation testing
    # In a real run, this string would come from the LLM response.
    # We include the character name and axis details to ensure it has semantic content.
    probe_text = (
        f"Scenario for {character_name}: "
        f"Given the coarse trait '{coarse_desc}' and the fine nuance '{fine_desc}', "
        f"imagine a situation completely outside their known narrative context. "
        f"The character is placed in a neutral, out-of-world setting where they must make a decision."
    )
    
    return probe_text


def generate_probes_batch(
    character_name: str,
    coarse_axes: Dict[str, Any],
    fine_axes: Dict[str, Any],
    source_corpus: List[str],
    target_count: int = MIN_VALID_PROBES,
    max_attempts: int = MAX_GENERATION_ATTEMPTS
) -> List[Dict[str, Any]]:
    """
    Generates a batch of validated probes.
    
    Implements the regeneration loop: attempts to generate probes until `target_count`
    valid ones are found or `max_attempts` is reached.
    """
    logger = _get_logger()
    model = load_sentence_model_cached()
    valid_probes = []
    attempts = 0

    logger.info(f"Starting probe generation for {character_name}. Target: {target_count}, Max Attempts: {max_attempts}")

    while len(valid_probes) < target_count and attempts < max_attempts:
        attempts += 1
        
        # In a real system, this would call the LLM. 
        # Here we simulate the generation step.
        probe_text = generate_probe_from_axes(character_name, coarse_axes, fine_axes)
        
        # Add some variation to simulate real LLM output for testing validation
        # (In real code, the LLM provides natural variation)
        probe_text = f"{probe_text} (Attempt {attempts})"

        # Validate against source corpus (T018 core logic)
        is_valid, similarity = validate_probe_semantic_distance(probe_text, source_corpus, model)

        if is_valid:
            valid_probes.append({
                "character": character_name,
                "probe_id": f"{character_name}_{len(valid_probes)+1}",
                "text": probe_text,
                "source_similarity": similarity,
                "status": "valid"
            })
        else:
            logger.debug(f"Probe {attempts} rejected due to similarity {similarity:.4f}.")

    if len(valid_probes) < target_count:
        logger.warning(f"Generation Limit Exceeded for {character_name}. "
                     f"Generated {len(valid_probes)} valid probes out of {max_attempts} attempts.")
    
    return valid_probes


def run_probe_generation_pipeline(
    axes_file_path: str,
    source_corpus_path: str,
    output_path: str
) -> None:
    """
    Main entry point to run the probe generation pipeline.
    Reads axes, loads source corpus, generates probes, and writes results.
    """
    logger = _get_logger()
    logger.info("Starting Probe Generation Pipeline")

    # Load Axes
    axes_path = Path(axes_file_path)
    if not axes_path.exists():
        raise FileNotFoundError(f"Axes file not found: {axes_file_path}")
    
    with open(axes_path, 'r', encoding='utf-8') as f:
        axes_data = [json.loads(line) for line in f]

    # Load Source Corpus (Simulated: reading from a text file or list of strings)
    # In a real scenario, this might be the raw narrative text.
    source_corpus = []
    source_path = Path(source_corpus_path)
    if source_path.exists():
        with open(source_path, 'r', encoding='utf-8') as f:
            source_corpus = [line.strip() for line in f if line.strip()]
    else:
        # Fallback to empty corpus if not found (validation will pass, but with warning)
        logger.warning(f"Source corpus file not found: {source_corpus_path}. Proceeding without semantic filtering.")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    all_probes = []

    for axes_entry in axes_data:
        char_name = axes_entry.get("character", "Unknown")
        coarse = axes_entry.get("coarse", {})
        fine = axes_entry.get("fine", {})
        
        probes = generate_probes_batch(
            character_name=char_name,
            coarse_axes=coarse,
            fine_axes=fine,
            source_corpus=source_corpus
        )
        all_probes.extend(probes)

    # Write results
    with open(output_file, 'w', encoding='utf-8') as f:
        for probe in all_probes:
            f.write(json.dumps(probe) + '\n')

    logger.info(f"Pipeline complete. Wrote {len(all_probes)} probes to {output_path}")


def main():
    """CLI entry point for testing the probe generator."""
    # Default paths for local testing
    args = {
        "axes": "data/derived/axes.jsonl",
        "source": "data/raw/source_corpus.txt",
        "output": "data/derived/probes.jsonl"
    }
    
    try:
        run_probe_generation_pipeline(
            args["axes"],
            args["source"],
            args["output"]
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure data/derived/axes.jsonl exists. Source corpus is optional for this demo.")
    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()