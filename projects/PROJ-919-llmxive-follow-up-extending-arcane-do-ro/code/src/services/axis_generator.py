"""
Axis Generator Service for ArcANE.

Implements semantic validation logic for character axes:
- Lexical overlap constraint (> 0.4 threshold triggers failure)
- Embedding cosine distance constraint (< 0.3 threshold triggers failure)
"""
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Import shared utilities and config
from src.lib.config import get_config
from src.lib.utils import get_logger
from src.cli.axis_input import load_sentence_model, calculate_lexical_overlap, calculate_semantic_similarity

logger = get_logger(__name__)

# Constants
LEXICAL_OVERLAP_THRESHOLD = 0.4
COSINE_DISTANCE_THRESHOLD = 0.3  # Cosine distance < 0.3 means similarity > 0.7
# Note: calculate_semantic_similarity returns cosine similarity (0 to 1).
# Distance = 1 - Similarity.
# Constraint: Distance < 0.3  =>  1 - Similarity < 0.3  =>  Similarity > 0.7
# However, the task description says "cosine distance < 0.3".
# If similarity is high (close to 1), distance is low (close to 0).
# If axes are too similar, we want to FAIL.
# So if distance < 0.3 (meaning similarity > 0.7), it's a violation.
# Wait, let's re-read the task: "embedding cosine distance < 0.3"
# Usually, we want axes to be DISTINCT.
# If distance is SMALL (< 0.3), they are similar -> FAIL.
# If distance is LARGE (> 0.3), they are distinct -> PASS.
# So the validation should check: IF distance < 0.3 THEN raise error.

def load_sentence_model_cached():
    """Load the sentence model once and cache it."""
    return load_sentence_model()

def validate_axes_semantic_overlap(
    coarse_text: str,
    fine_text: str,
    model_name: str = "all-MiniLM-L6-v2"
) -> Tuple[bool, Dict[str, float], Optional[str]]:
    """
    Validates that Coarse and Fine axes meet semantic distinctness criteria.

    Criteria:
    1. Lexical Overlap: Must be <= 0.4 (if > 0.4, they are too similar).
    2. Embedding Cosine Distance: Must be >= 0.3 (if < 0.3, they are too similar).

    Args:
        coarse_text: The Coarse axis definition.
        fine_text: The Fine axis definition.
        model_name: Sentence transformer model name.

    Returns:
        Tuple of (is_valid, metrics_dict, error_message)
        is_valid: True if both constraints pass.
        metrics_dict: Contains 'lexical_overlap' and 'cosine_distance'.
        error_message: String describing failure if any, None otherwise.
    """
    if not coarse_text or not fine_text:
        return False, {}, "One or both axis texts are empty."

    # 1. Lexical Overlap Check
    lexical_overlap = calculate_lexical_overlap(coarse_text, fine_text)
    logger.debug(f"Calculated lexical overlap: {lexical_overlap:.4f}")

    if lexical_overlap > LEXICAL_OVERLAP_THRESHOLD:
        error_msg = (
            f"Lexical overlap ({lexical_overlap:.4f}) exceeds threshold "
            f"({LEXICAL_OVERLAP_THRESHOLD}). Coarse and Fine axes are too similar lexically."
        )
        logger.warning(error_msg)
        return False, {"lexical_overlap": lexical_overlap}, error_msg

    # 2. Embedding Cosine Distance Check
    try:
        model = load_sentence_model_cached()
        # Calculate cosine similarity first
        similarity = calculate_semantic_similarity(
            model, coarse_text, fine_text
        )
        # Convert to distance: Distance = 1 - Similarity
        cosine_distance = 1.0 - similarity
        logger.debug(f"Calculated cosine similarity: {similarity:.4f}, distance: {cosine_distance:.4f}")

        if cosine_distance < COSINE_DISTANCE_THRESHOLD:
            error_msg = (
                f"Cosine distance ({cosine_distance:.4f}) is below threshold "
                f"({COSINE_DISTANCE_THRESHOLD}). Coarse and Fine axes are too semantically similar."
            )
            logger.warning(error_msg)
            return False, {
                "lexical_overlap": lexical_overlap,
                "cosine_similarity": similarity,
                "cosine_distance": cosine_distance
            }, error_msg

    except Exception as e:
        logger.error(f"Failed to compute embeddings: {e}", exc_info=True)
        return False, {"lexical_overlap": lexical_overlap}, f"Embedding computation failed: {str(e)}"

    return True, {
        "lexical_overlap": lexical_overlap,
        "cosine_similarity": 1.0 - cosine_distance,
        "cosine_distance": cosine_distance
    }, None

def generate_axes_from_input(
    coarse_input: str,
    fine_input: str,
    character_name: str = "Unknown"
) -> Optional[Dict]:
    """
    Main entry point to validate and generate axis objects.

    Performs all semantic checks. If valid, returns a structured dictionary
    representing the CharacterAxis. If invalid, raises ValueError with details.

    Args:
        coarse_input: Raw text for Coarse axis.
        fine_input: Raw text for Fine axis.
        character_name: Name of the character.

    Returns:
        Dict containing 'coarse', 'fine', 'metrics', and 'status'.
    """
    is_valid, metrics, error_msg = validate_axes_semantic_overlap(
        coarse_input, fine_input
    )

    if not is_valid:
        raise ValueError(f"Axis validation failed for {character_name}: {error_msg}")

    # Construct the axis object
    axis_data = {
        "character": character_name,
        "coarse": coarse_input,
        "fine": fine_input,
        "metrics": metrics,
        "status": "validated",
        "validation_timestamp": None # Will be set by caller or state tracker
    }

    logger.info(f"Successfully validated axes for character: {character_name}")
    return axis_data

def serialize_axes_to_jsonl(axes_list: List[Dict], output_path: str) -> None:
    """
    Writes a list of validated axis dictionaries to a JSONL file.

    Args:
        axes_list: List of axis dictionaries.
        output_path: Path to the output .jsonl file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'a', encoding='utf-8') as f:
        for axis in axes_list:
            f.write(json.dumps(axis) + '\n')

    logger.info(f"Serialized {len(axes_list)} axes to {output_path}")

def run_validation_demo():
    """
    Demo function to run validation on sample inputs.
    This is for testing the logic locally if needed, but the main flow
    is driven by the CLI or experiment runner.
    """
    # Sample inputs for demonstration
    coarse_sample = "The character is defined by their moral compass and ethical decisions."
    fine_sample = "The character is defined by their moral compass and ethical decisions." # Intentionally similar

    try:
        result = generate_axes_from_input(coarse_sample, fine_sample, "DemoChar")
        print("Validation Passed:", result)
    except ValueError as e:
        print("Validation Failed:", str(e))

if __name__ == "__main__":
    run_validation_demo()