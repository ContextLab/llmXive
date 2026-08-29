"""
Axis Generator Service for User Story 1.

Implements manual input interface for defining character axes (Coarse and Fine)
with two modes:
1. Interactive CLI prompt for local dev
2. Non-interactive config file loading for CI/CD

Includes serialization logic to produce data/derived/axes.jsonl.
"""
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

# Import from local project structure
from src.lib.config import get_config
from src.lib.utils import get_logger
from src.services.axes_writer import write_axes_to_jsonl, ensure_derived_directory

logger = get_logger(__name__)

# Cache for sentence transformer model to avoid reloading
_model_cache = None

def load_sentence_model_cached():
    """Lazy load sentence-transformers model with caching."""
    global _model_cache
    if _model_cache is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers/all-MiniLM-L6-v2...")
            _model_cache = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
    return _model_cache

def calculate_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

def validate_axes_semantic_overlap(
    coarse_text: str,
    fine_text: str,
    threshold_overlap: float = 0.4,
    threshold_similarity: float = 0.3
) -> Tuple[bool, Dict]:
    """
    Validate that Coarse and Fine axes are semantically independent.
    
    Returns:
        Tuple of (is_valid, details_dict)
    """
    model = load_sentence_model_cached()
    
    # Calculate embeddings
    embeddings = model.encode([coarse_text, fine_text], convert_to_numpy=True)
    emb_coarse, emb_fine = embeddings[0], embeddings[1]
    
    # Calculate lexical overlap (Jaccard similarity on words)
    words_coarse = set(re.findall(r'\w+', coarse_text.lower()))
    words_fine = set(re.findall(r'\w+', fine_text.lower()))
    
    if not words_coarse or not words_fine:
        return False, {"error": "Empty text provided"}
    
    intersection = words_coarse & words_fine
    union = words_coarse | words_fine
    lexical_overlap = len(intersection) / len(union) if union else 0.0
    
    # Calculate cosine similarity
    cosine_sim = calculate_cosine_similarity(emb_coarse, emb_fine)
    
    # Validation logic
    is_valid = True
    issues = []
    
    if lexical_overlap > threshold_overlap:
        is_valid = False
        issues.append(f"Lexical overlap ({lexical_overlap:.3f}) exceeds threshold ({threshold_overlap})")
    
    if cosine_sim > threshold_similarity:
        is_valid = False
        issues.append(f"Cosine similarity ({cosine_sim:.3f}) exceeds threshold ({threshold_similarity})")
    
    return is_valid, {
        "lexical_overlap": lexical_overlap,
        "cosine_similarity": cosine_sim,
        "is_valid": is_valid,
        "issues": issues
    }

def generate_axes_from_input(
    character: str,
    coarse_input: str,
    fine_input: str
) -> Tuple[Optional[Dict], Optional[Dict], Dict]:
    """
    Generate and validate axis definitions from input text.
    
    Returns:
        Tuple of (coarse_axis_dict, fine_axis_dict, validation_details)
    """
    # Validate semantic independence
    is_valid, validation_details = validate_axes_semantic_overlap(coarse_input, fine_input)
    
    if not is_valid:
        logger.error(f"Axis validation failed: {validation_details['issues']}")
        return None, None, validation_details
    
    # Construct Coarse Axis object
    coarse_axis = {
        "character": character,
        "axis_name": "Coarse",
        "description": coarse_input.strip(),
        "type": "coarse"
    }
    
    # Construct Fine Axis object
    fine_axis = {
        "character": character,
        "axis_name": "Fine",
        "description": fine_input.strip(),
        "source_observation": "Manual input",
        "type": "fine"
    }
    
    logger.info(f"Successfully generated axes for character: {character}")
    return coarse_axis, fine_axis, validation_details

def serialize_axes_to_jsonl(
    character: str,
    coarse_axis: Dict,
    fine_axis: Dict,
    output_path: Optional[str] = None
) -> Path:
    """
    Serialize validated axes to JSONL file.
    
    Args:
        character: Character name
        coarse_axis: Coarse axis dictionary
        fine_axis: Fine axis dictionary
        output_path: Optional custom output path. Defaults to config.
    
    Returns:
        Path to the created file
    """
    if output_path is None:
        config = get_config()
        output_path = config.get("paths", {}).get("axes_jsonl", "data/derived/axes.jsonl")
    
    output_path = Path(output_path)
    ensure_derived_directory(output_path)
    
    # Prepare records
    records = [coarse_axis, fine_axis]
    
    # Write to JSONL
    write_axes_to_jsonl(records, str(output_path))
    logger.info(f"Axes written to {output_path}")
    
    return output_path

def run_validation_demo():
    """
    Demo function to test axis validation logic.
    Not intended for production use.
    """
    logger.info("Running axis validation demo...")
    
    # Test case 1: Valid independent axes
    coarse_valid = "A character defined by their moral integrity and sense of duty."
    fine_valid = "Specific instances where the character prioritized personal sacrifice over self-preservation."
    
    is_valid, details = validate_axes_semantic_overlap(coarse_valid, fine_valid)
    print(f"Valid Case: {is_valid} - {details}")
    
    # Test case 2: Invalid (high overlap)
    coarse_invalid = "A character who is brave and courageous."
    fine_invalid = "Brave actions and courageous decisions in battle."
    
    is_valid, details = validate_axes_semantic_overlap(coarse_invalid, fine_invalid)
    print(f"Invalid Case: {is_valid} - {details}")

def main():
    """
    Main entry point for interactive or config-based axis generation.
    
    Modes:
    1. --config <path>: Load from JSON config file (CI/CD mode)
    2. Default: Interactive CLI prompt (Dev mode)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and validate character axes")
    parser.add_argument("--config", type=str, help="Path to JSON config file (CI/CD mode)")
    parser.add_argument("--character", type=str, help="Character name (interactive mode)")
    parser.add_argument("--coarse", type=str, help="Coarse axis text (interactive mode)")
    parser.add_argument("--fine", type=str, help="Fine axis text (interactive mode)")
    parser.add_argument("--output", type=str, help="Output JSONL path")
    args = parser.parse_args()
    
    if args.config:
        # CI/CD Mode: Load from config file
        logger.info(f"Loading config from {args.config}")
        try:
            with open(args.config, 'r') as f:
                config_data = json.load(f)
            
            character = config_data.get("character")
            coarse_input = config_data.get("coarse_axis")
            fine_input = config_data.get("fine_axis")
            
            if not all([character, coarse_input, fine_input]):
                raise ValueError("Config must contain 'character', 'coarse_axis', and 'fine_axis'")
            
            logger.info(f"Running in CI/CD mode for character: {character}")
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {args.config}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config: {e}")
            raise
    
    else:
        # Interactive Mode
        if args.character and args.coarse and args.fine:
            # Non-interactive flags provided
            character = args.character
            coarse_input = args.coarse
            fine_input = args.fine
        else:
            logger.info("Running in interactive mode. Please provide inputs.")
            character = input("Enter character name: ").strip()
            print("\nEnter Coarse Axis (general traits):")
            coarse_input = input("> ").strip()
            print("\nEnter Fine Axis (specific observations):")
            fine_input = input("> ").strip()
    
    # Generate and validate
    coarse_axis, fine_axis, validation = generate_axes_from_input(
        character, coarse_input, fine_input
    )
    
    if not coarse_axis or not fine_axis:
        logger.error("Axis generation failed due to validation errors.")
        print("\nValidation Details:")
        for key, val in validation.items():
            print(f"  {key}: {val}")
        return 1
    
    # Serialize to JSONL
    output_path = serialize_axes_to_jsonl(
        character, coarse_axis, fine_axis, args.output
    )
    
    # Display output
    print(f"\nSuccess! Axes generated and saved to: {output_path}")
    print("\nCoarse Axis:")
    print(json.dumps(coarse_axis, indent=2))
    print("\nFine Axis:")
    print(json.dumps(fine_axis, indent=2))
    
    return 0

if __name__ == "__main__":
    exit(main())
