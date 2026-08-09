import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np
from sentence_transformers import SentenceTransformer
from src.lib.utils import get_logger
from src.lib.config import get_config

# Initialize logger
logger = get_logger(__name__)

# Constants for semantic thresholds (from T012 implementation context)
LEXICAL_OVERLAP_THRESHOLD = 0.4
SEMANTIC_SIMILARITY_THRESHOLD = 0.3

def load_sentence_model_cached() -> SentenceTransformer:
    """Load the sentence transformer model with caching logic."""
    model_name = "all-MiniLM-L6-v2"
    logger.info(f"Loading sentence transformer model: {model_name}")
    model = SentenceTransformer(model_name)
    logger.info("Model loaded successfully")
    return model

def calculate_lexical_overlap(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between token sets of two texts."""
    if not text1 or not text2:
        return 0.0
    
    # Simple tokenization: lowercase and split on whitespace/punctuation
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    return intersection / union if union > 0 else 0.0

def calculate_semantic_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """Calculate cosine similarity between sentence embeddings."""
    if not text1 or not text2:
        return 0.0
    
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)

def validate_coarse_fine_independence(coarse: str, fine: str, model: SentenceTransformer) -> Tuple[bool, dict]:
    """
    Validate that Coarse and Fine axes are semantically distinct.
    Returns (is_valid, details_dict).
    """
    details = {
        "coarse_length": len(coarse),
        "fine_length": len(fine),
        "lexical_overlap": 0.0,
        "semantic_similarity": 0.0,
        "lexical_valid": True,
        "semantic_valid": True,
        "errors": []
    }

    # Lexical overlap check
    overlap = calculate_lexical_overlap(coarse, fine)
    details["lexical_overlap"] = overlap
    if overlap > LEXICAL_OVERLAP_THRESHOLD:
        details["lexical_valid"] = False
        details["errors"].append(f"Lexical overlap {overlap:.2f} exceeds threshold {LEXICAL_OVERLAP_THRESHOLD}")

    # Semantic similarity check
    similarity = calculate_semantic_similarity(coarse, fine, model)
    details["semantic_similarity"] = similarity
    if similarity > SEMANTIC_SIMILARITY_THRESHOLD:
        details["semantic_valid"] = False
        details["errors"].append(f"Semantic similarity {similarity:.2f} exceeds threshold {SEMANTIC_SIMILARITY_THRESHOLD}")

    is_valid = details["lexical_valid"] and details["semantic_valid"]
    return is_valid, details

def validate_fine_independence_from_source(fine: str, source_text: str, model: SentenceTransformer) -> Tuple[bool, dict]:
    """
    Validate that Fine axes originate from independent narrative observations.
    This is a heuristic check to ensure the Fine axis isn't just a copy of the source.
    """
    details = {
        "source_length": len(source_text),
        "fine_length": len(fine),
        "lexical_overlap": 0.0,
        "semantic_similarity": 0.0,
        "is_independent": True,
        "errors": []
    }

    if not source_text:
        details["errors"].append("No source text provided for comparison")
        return False, details

    overlap = calculate_lexical_overlap(fine, source_text)
    details["lexical_overlap"] = overlap
    
    similarity = calculate_semantic_similarity(fine, source_text, model)
    details["semantic_similarity"] = similarity

    # If fine axis is too similar to source, it might not be an independent observation
    # We use a stricter threshold for source comparison to ensure independence
    if similarity > 0.8 or overlap > 0.6:
        details["is_independent"] = False
        details["errors"].append("Fine axis appears too similar to source text; may not be independent")

    return details["is_independent"], details

def read_input(prompt: str) -> str:
    """Read input from user with a prompt."""
    try:
        return input(prompt).strip()
    except EOFError:
        logger.error("EOF encountered during input")
        return ""

def process_input(coarse_text: str, fine_text: str, source_text: Optional[str] = None) -> Tuple[bool, dict]:
    """
    Process and validate axis inputs.
    Returns (is_valid, validation_details).
    """
    model = load_sentence_model_cached()
    
    validation_result = {
        "coarse_fine_validation": {},
        "source_independence_validation": {},
        "overall_valid": True,
        "errors": []
    }

    # Validate Coarse vs Fine independence
    is_coarse_fine_valid, coarse_fine_details = validate_coarse_fine_independence(
        coarse_text, fine_text, model
    )
    validation_result["coarse_fine_validation"] = coarse_fine_details
    
    if not is_coarse_fine_valid:
        validation_result["overall_valid"] = False
        validation_result["errors"].extend(coarse_fine_details["errors"])

    # Validate Fine independence from source if source is provided
    if source_text:
        is_source_valid, source_details = validate_fine_independence_from_source(
            fine_text, source_text, model
        )
        validation_result["source_independence_validation"] = source_details
        
        if not is_source_valid:
            validation_result["overall_valid"] = False
            validation_result["errors"].extend(source_details["errors"])

    return validation_result["overall_valid"], validation_result

def verify_manual_independence_confirmation() -> bool:
    """
    Verify that the researcher has manually confirmed the independence of input data.
    This implements FR-001 by requiring explicit human confirmation.
    """
    print("\n" + "="*70)
    print("INDEPENDENCE VERIFICATION REQUIRED (FR-001)")
    print("="*70)
    print("To ensure the validity of your experiment:")
    print("1. The Coarse axis must be derived from high-level character traits.")
    print("2. The Fine axis must be derived from specific, independent narrative observations.")
    print("3. The Fine axis must NOT be a direct copy or trivial paraphrase of the Coarse axis.")
    print("4. The Fine axis must NOT be a direct copy of the source text.")
    print("-"*70)
    
    confirmation = read_input(
        "Have you manually confirmed that the Fine axis originates from independent "
        "narrative observations and is not derived from the Coarse axis or source text? "
        "Type 'yes' to confirm: "
    ).lower()
    
    if confirmation == 'yes':
        logger.info("Researcher manually confirmed independence of inputs")
        return True
    else:
        logger.warning("Researcher did not confirm independence of inputs")
        return False

def main():
    """
    Main entry point for axis input validation and verification.
    Implements T012a: Manual researcher confirmation for independence.
    """
    parser = argparse.ArgumentParser(
        description="Input and validate character axes with independence verification"
    )
    parser.add_argument("--character", type=str, required=True, help="Character name")
    parser.add_argument("--coarse", type=str, required=True, help="Coarse axis definition")
    parser.add_argument("--fine", type=str, required=True, help="Fine axis definition")
    parser.add_argument("--source", type=str, required=False, help="Source text for comparison")
    parser.add_argument("--output", type=str, required=False, help="Output file path for validation results")
    
    args = parser.parse_args()
    
    logger.info(f"Processing axis input for character: {args.character}")
    
    # Step 1: Manual independence confirmation (T012a core requirement)
    if not verify_manual_independence_confirmation():
        print("\n❌ Independence confirmation failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Automated validation checks
    is_valid, details = process_input(args.coarse, args.fine, args.source)
    
    if not is_valid:
        print("\n❌ Automated validation failed:")
        for error in details["errors"]:
            print(f"   - {error}")
        sys.exit(1)
    
    # Step 3: Success output
    print("\n✅ Validation successful!")
    print(f"   Character: {args.character}")
    print(f"   Coarse axis length: {details['coarse_fine_validation']['coarse_length']}")
    print(f"   Fine axis length: {details['coarse_fine_validation']['fine_length']}")
    print(f"   Lexical overlap: {details['coarse_fine_validation']['lexical_overlap']:.4f}")
    print(f"   Semantic similarity: {details['coarse_fine_validation']['semantic_similarity']:.4f}")
    
    if args.source:
        print(f"   Source independence: {details['source_independence_validation']['is_independent']}")
    
    # Write results to output file if specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                "character": args.character,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "validation_passed": True,
                "details": details
            }, f, indent=2)
        logger.info(f"Validation results written to {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())