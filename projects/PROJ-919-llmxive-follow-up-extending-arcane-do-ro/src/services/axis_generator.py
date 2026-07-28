"""
Axis Generator Service for llmXive.

Implements logic to generate and validate Character Axes (Coarse/Fine)
ensuring semantic independence based on lexical overlap and embedding distance.
"""
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

# Cached sentence transformer model to avoid reloading on every call
_sentence_model = None

def load_sentence_model_cached():
    """
    Lazy-load the sentence-transformer model for semantic similarity calculations.
    Uses a lightweight model suitable for CPU execution.
    """
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Using 'all-MiniLM-L6-v2' as it is fast, small, and effective for general semantic similarity
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError as e:
            raise ImportError(
                "The 'sentence-transformers' library is required for semantic validation. "
                "Please install it via: pip install sentence-transformers"
            ) from e
    return _sentence_model

def calculate_lexical_overlap(text_a: str, text_b: str) -> float:
    """
    Calculates the Jaccard similarity (lexical overlap) between two texts.
    
    Args:
        text_a: First text string.
        text_b: Second text string.
        
    Returns:
        Float between 0.0 and 1.0 representing the ratio of shared unique words.
    """
    if not text_a or not text_b:
        return 0.0
        
    # Normalize: lowercase and remove punctuation
    def normalize(text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return set(text.split())
        
    set_a = normalize(text_a)
    set_b = normalize(text_b)
    
    if not set_a or not set_b:
        return 0.0
        
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    
    return len(intersection) / len(union) if union else 0.0

def calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Calculates the cosine similarity between two texts using sentence embeddings.
    
    Args:
        text_a: First text string.
        text_b: Second text string.
        
    Returns:
        Float between -1.0 and 1.0 representing cosine similarity.
    """
    model = load_sentence_model_cached()
    embeddings = model.encode([text_a, text_b], convert_to_numpy=True)
    
    vec_a = embeddings[0]
    vec_b = embeddings[1]
    
    # Normalize vectors
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    # Cosine similarity
    return np.dot(vec_a, vec_b) / (norm_a * norm_b)

def validate_axes_semantic_overlap(
    coarse_axis: str,
    fine_axis: str,
    lexical_threshold: float = 0.4,
    cosine_threshold: float = 0.3
) -> Tuple[bool, Dict[str, float]]:
    """
    Validates that Coarse and Fine axes are semantically distinct.
    
    Requirements (FR-001):
    1. Lexical overlap (Jaccard) must be <= 0.4.
    2. Cosine similarity of embeddings must be < 0.3.
    
    Args:
        coarse_axis: The Coarse axis definition text.
        fine_axis: The Fine axis definition text.
        lexical_threshold: Maximum allowed lexical overlap.
        cosine_threshold: Maximum allowed cosine similarity.
        
    Returns:
        Tuple of (is_valid, metrics_dict).
        metrics_dict contains 'lexical_overlap' and 'cosine_similarity'.
        
    Raises:
        ValueError: If validation fails.
    """
    if not coarse_axis or not fine_axis:
        raise ValueError("Coarse and Fine axis texts cannot be empty.")
        
    # Calculate metrics
    lex_overlap = calculate_lexical_overlap(coarse_axis, fine_axis)
    cos_sim = calculate_semantic_similarity(coarse_axis, fine_axis)
    
    metrics = {
        "lexical_overlap": float(lex_overlap),
        "cosine_similarity": float(cos_sim)
    }
    
    is_valid = True
    reasons = []
    
    if lex_overlap > lexical_threshold:
        is_valid = False
        reasons.append(f"Lexical overlap ({lex_overlap:.4f}) exceeds threshold ({lexical_threshold}).")
        
    if cos_sim >= cosine_threshold:
        is_valid = False
        reasons.append(f"Cosine similarity ({cos_sim:.4f}) exceeds threshold ({cosine_threshold}).")
        
    if not is_valid:
        error_msg = "Semantic validation failed:\n" + "\n".join(reasons)
        raise ValueError(error_msg)
        
    return True, metrics

def generate_axes_from_input(
    character_name: str,
    coarse_input: str,
    fine_input: str
) -> Dict[str, Any]:
    """
    Generates a validated CharacterAxis object from raw inputs.
    
    Args:
        character_name: Name of the character.
        coarse_input: Raw text for Coarse axis.
        fine_input: Raw text for Fine axis.
        
    Returns:
        Dictionary representing the validated axis object.
    """
    # Validate semantic overlap first
    is_valid, metrics = validate_axes_semantic_overlap(coarse_input, fine_input)
    
    # Construct the result object
    axis_obj = {
        "character": character_name,
        "coarse": {
            "definition": coarse_input,
            "type": "coarse"
        },
        "fine": {
            "definition": fine_input,
            "type": "fine"
        },
        "validation": {
            "passed": True,
            "metrics": metrics
        }
    }
    
    return axis_obj

def serialize_axes_to_jsonl(axes: List[Dict[str, Any]], output_path: str) -> None:
    """
    Serializes a list of axis dictionaries to a JSONL file.
    
    Args:
        axes: List of axis dictionaries.
        output_path: Path to the output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        for axis in axes:
            f.write(json.dumps(axis, ensure_ascii=False) + '\n')

def run_validation_demo():
    """
    Demonstrates the semantic validation logic with sample data.
    Intended for manual verification of the service logic.
    """
    print("Running Axis Semantic Validation Demo...")
    
    # Sample data: Distinct axes
    coarse_text = "A character's fundamental moral alignment and their relationship with authority."
    fine_text = "Specific instances of hesitation before speaking in high-pressure social situations."
    
    try:
        is_valid, metrics = validate_axes_semantic_overlap(coarse_text, fine_text)
        print(f"Validation Passed: {is_valid}")
        print(f"Metrics: {metrics}")
        
        axis_obj = generate_axes_from_input("DemoCharacter", coarse_text, fine_text)
        print(f"Generated Axis: {json.dumps(axis_obj, indent=2)}")
        
    except ValueError as e:
        print(f"Validation Failed: {e}")

if __name__ == "__main__":
    run_validation_demo()