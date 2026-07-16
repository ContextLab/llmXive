import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

# Constants for validation thresholds (FR-001)
LEXICAL_OVERLAP_THRESHOLD = 0.4
SEMANTIC_SIMILARITY_THRESHOLD = 0.3
SOURCE_TEXT_SIMILARITY_THRESHOLD = 0.5  # Fine axis must be distinct from source text

# Singleton model cache
_model_cache: Optional[SentenceTransformer] = None


def load_sentence_model() -> SentenceTransformer:
    """Load the sentence transformer model, caching it for reuse."""
    global _model_cache
    if _model_cache is None:
        # Using a lightweight model suitable for CPU execution
        _model_cache = SentenceTransformer("all-MiniLM-L6-v2")
    return _model_cache


def calculate_lexical_overlap(text1: str, text2: str) -> float:
    """
    Calculate the Jaccard index (lexical overlap) between two texts.
    Returns a value between 0.0 and 1.0.
    """
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union) if union else 0.0


def calculate_semantic_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """
    Calculate cosine similarity between two texts using embeddings.
    Returns a value between -1.0 and 1.0.
    """
    embeddings = model.encode([text1, text2], convert_to_tensor=True)
    # Normalize embeddings
    norm1 = embeddings[0] / torch.norm(embeddings[0])
    norm2 = embeddings[1] / torch.norm(embeddings[1])
    # Cosine similarity
    similarity = torch.dot(norm1, norm2).item()
    return similarity


def validate_coarse_fine_independence(coarse: str, fine: str) -> Tuple[bool, str, float, float]:
    """
    Validate that Fine axis is independent of Coarse axis.
    Checks:
    1. Lexical overlap < 0.4
    2. Semantic similarity < 0.3 (distance > 0.7)
    Returns (is_valid, message, overlap_score, similarity_score)
    """
    model = load_sentence_model()

    # 1. Check Lexical Overlap
    overlap = calculate_lexical_overlap(coarse, fine)
    overlap_valid = overlap < LEXICAL_OVERLAP_THRESHOLD

    # 2. Check Semantic Similarity
    # Note: Lower similarity means more independent (further apart)
    # We want semantic distance to be high, so similarity should be LOW
    similarity = calculate_semantic_similarity(coarse, fine, model)
    # If similarity is < 0.3, they are semantically distinct enough
    similarity_valid = similarity < SEMANTIC_SIMILARITY_THRESHOLD

    is_valid = overlap_valid and similarity_valid

    if not is_valid:
        reasons = []
        if not overlap_valid:
            reasons.append(f"Lexical overlap ({overlap:.2f}) exceeds threshold ({LEXICAL_OVERLAP_THRESHOLD})")
        if not similarity_valid:
            reasons.append(f"Semantic similarity ({similarity:.2f}) exceeds threshold ({SEMANTIC_SIMILARITY_THRESHOLD}) - axes too similar")
        return False, "; ".join(reasons), overlap, similarity

    return True, "Coarse and Fine axes are sufficiently independent.", overlap, similarity


def validate_fine_independence_from_source(fine: str, source_text: str) -> Tuple[bool, str, float]:
    """
    Validate that the Fine axis originates from independent narrative observations
    and is not a direct paraphrase of the source text segment provided.
    Per FR-001: Fine axes must be derived from independent observations, not just
    restating the source. We enforce a maximum similarity threshold to ensure
    the Fine axis adds new analytical value rather than echoing the source.

    Returns (is_valid, message, similarity_score)
    """
    if not source_text.strip():
        # If no source text provided, we cannot validate against it.
        # However, per FR-001, source text is required for validation.
        # We treat missing source as a validation failure to enforce the requirement.
        return False, "Source text segment is required to verify independence of Fine axis.", 0.0

    model = load_sentence_model()

    # Calculate semantic similarity between Fine axis and Source Text
    similarity = calculate_semantic_similarity(fine, source_text, model)

    # If similarity is too high (> threshold), the Fine axis is likely just
    # a restatement of the source, violating the "independent observation" requirement.
    # We require the Fine axis to be distinct (similarity < threshold).
    is_valid = similarity < SOURCE_TEXT_SIMILARITY_THRESHOLD

    if not is_valid:
        return (
            False,
            f"Fine axis is too similar to source text (similarity: {similarity:.2f} > {SOURCE_TEXT_SIMILARITY_THRESHOLD}). "
            "Please ensure the Fine axis represents an independent analytical observation, not a restatement of the source.",
            similarity
        )

    return True, f"Fine axis is independent of source text (similarity: {similarity:.2f}).", similarity


def read_input() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Read Coarse, Fine, and Source Text inputs from stdin or arguments.
    Returns (coarse, fine, source_text) or None if input is incomplete.
    """
    # Check for direct arguments first (for scripting)
    if len(sys.argv) >= 4:
        return sys.argv[1], sys.argv[2], sys.argv[3]

    # Interactive mode
    print("=== ArcANE Axis Input Validator ===")
    print("Please provide the following inputs. Press Enter on an empty line to skip (not recommended for Source).")

    print("\n--- Coarse Axis Definition ---")
    coarse_lines = []
    print("Enter Coarse axis definition (end with a single dot '.' on a new line):")
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if line.strip() == '.':
            break
        coarse_lines.append(line.rstrip('\n'))
    coarse = '\n'.join(coarse_lines).strip()

    if not coarse:
        print("Error: Coarse axis definition is required.")
        return None, None, None

    print("\n--- Fine Axis Definition ---")
    fine_lines = []
    print("Enter Fine axis definition (end with a single dot '.' on a new line):")
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if line.strip() == '.':
            break
        fine_lines.append(line.rstrip('\n'))
    fine = '\n'.join(fine_lines).strip()

    if not fine:
        print("Error: Fine axis definition is required.")
        return None, None, None

    print("\n--- Source Text Segment (for Independence Verification) ---")
    source_lines = []
    print("Enter the source narrative segment used to derive the Fine axis (end with a single dot '.' on a new line):")
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if line.strip() == '.':
            break
        source_lines.append(line.rstrip('\n'))
    source_text = '\n'.join(source_lines).strip()

    if not source_text:
        print("Warning: No source text provided. Independence from source cannot be verified.")

    return coarse, fine, source_text


def process_input(coarse: str, fine: str, source_text: Optional[str]) -> dict:
    """
    Process the input: validate Coarse vs Fine, and Fine vs Source.
    Returns a result dictionary with validation status and metrics.
    """
    # 1. Validate Coarse vs Fine Independence
    cf_valid, cf_msg, cf_overlap, cf_sim = validate_coarse_fine_independence(coarse, fine)

    # 2. Validate Fine vs Source Independence (FR-001)
    fs_valid = True
    fs_msg = "No source text provided for validation."
    fs_sim = 0.0
    if source_text:
        fs_valid, fs_msg, fs_sim = validate_fine_independence_from_source(fine, source_text)
    else:
        # If source is missing, we fail the FR-001 requirement strictly
        fs_valid = False
        fs_msg = "Source text segment is missing. FR-001 requires verification against source text."

    is_overall_valid = cf_valid and fs_valid

    return {
        "coarse": coarse,
        "fine": fine,
        "source_text": source_text,
        "validation": {
            "coarse_fine_independent": cf_valid,
            "coarse_fine_message": cf_msg,
            "coarse_fine_overlap": cf_overlap,
            "coarse_fine_similarity": cf_sim,
            "fine_source_independent": fs_valid,
            "fine_source_message": fs_msg,
            "fine_source_similarity": fs_sim,
            "overall_valid": is_overall_valid
        }
    }


def main():
    """Main entry point for CLI axis input and validation."""
    parser = argparse.ArgumentParser(description="ArcANE Axis Input & Validation (FR-001)")
    parser.add_argument("--coarse", type=str, help="Coarse axis definition")
    parser.add_argument("--fine", type=str, help="Fine axis definition")
    parser.add_argument("--source", type=str, help="Source text segment for independence check")
    parser.add_argument("--output", type=str, help="Output JSON file path (optional)")

    args = parser.parse_args()

    # Determine inputs
    if args.coarse and args.fine:
        coarse = args.coarse
        fine = args.fine
        source = args.source
    else:
        coarse, fine, source = read_input()
        if coarse is None:
            sys.exit(1)

    # Process and validate
    result = process_input(coarse, fine, source)

    # Output results
    output_str = json.dumps(result, indent=2)
    print("\n--- Validation Results ---")
    print(output_str)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(output_str)
        print(f"\nResults saved to {args.output}")

    # Exit with error code if validation failed
    if not result["validation"]["overall_valid"]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
