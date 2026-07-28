import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import numpy as np

# Local imports from existing API surface
# Note: load_sentence_model_cached is defined in axis_generator, we reuse it here
# to ensure we use the same model instance logic.
from src.services.axis_generator import load_sentence_model_cached
from src.lib.utils import get_logger

logger = get_logger(__name__)

# --- Configuration Constants ---
# FR-001: Semantic similarity threshold to prove independence from source text
# If similarity > THRESHOLD, the Fine axis is considered too close to the source
# and fails the "independent narrative observation" check.
SEMANTIC_INDEPENDENCE_THRESHOLD = 0.45

# Lexical overlap threshold for Coarse vs Fine (from T012 logic, reused here)
LEXICAL_OVERLAP_THRESHOLD = 0.4

def load_sentence_model():
    """Wrapper to load the sentence model using the cached loader from axis_generator."""
    return load_sentence_model_cached()

def calculate_lexical_overlap(text1: str, text2: str) -> float:
    """
    Calculate the Jaccard index (lexical overlap) between two texts.
    Returns a value between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize: lowercase and split on non-alphanumeric
    tokens1 = set(re.split(r'\W+', text1.lower()))
    tokens2 = set(re.split(r'\W+', text2.lower()))
    
    # Remove empty strings
    tokens1.discard('')
    tokens2.discard('')
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return float(len(intersection) / len(union)) if union else 0.0

def calculate_semantic_similarity(text1: str, text2: str, model) -> float:
    """
    Calculate cosine similarity between embeddings of two texts.
    Uses the provided sentence-transformers model.
    """
    if not text1 or not text2:
        return 0.0
    
    try:
        embeddings = model.encode([text1, text2], convert_to_numpy=True)
        emb1, emb2 = embeddings[0], embeddings[1]
        
        # Normalize
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = np.dot(emb1, emb2) / (norm1 * norm2)
        return float(cosine_sim)
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {e}")
        raise

def validate_coarse_fine_independence(coarse: str, fine: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates that Coarse and Fine axes are distinct.
    Checks:
    1. Lexical overlap < LEXICAL_OVERLAP_THRESHOLD
    2. Semantic similarity < 0.3 (as per T012 spec)
    """
    model = load_sentence_model()
    
    lex_overlap = calculate_lexical_overlap(coarse, fine)
    sem_sim = calculate_semantic_similarity(coarse, fine, model)
    
    is_valid = True
    reasons = []
    
    if lex_overlap > LEXICAL_OVERLAP_THRESHOLD:
        is_valid = False
        reasons.append(f"Lexical overlap ({lex_overlap:.2f}) exceeds threshold ({LEXICAL_OVERLAP_THRESHOLD})")
    
    if sem_sim > 0.3:
        is_valid = False
        reasons.append(f"Semantic similarity ({sem_sim:.2f}) exceeds threshold (0.3)")
    
    return is_valid, {
        "lexical_overlap": lex_overlap,
        "semantic_similarity": sem_sim,
        "is_valid": is_valid,
        "reasons": reasons
    }

def validate_fine_independence_from_source(fine: str, source_text: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates that the Fine axis originates from an independent narrative observation
    as per FR-001.
    
    Logic:
    - Compare 'Fine' axis text against the provided 'Source Text Segment'.
    - If semantic similarity is too HIGH (> SEMANTIC_INDEPENDENCE_THRESHOLD),
      it implies the Fine axis is just a copy of the source, not an independent observation.
    - We expect a moderate similarity (it's about the character) but not near-perfect identity.
    - However, the prompt implies "prevents copy-paste" and "independent observations".
      If the user pastes the source text as the Fine axis, that's a failure.
      If the user writes a summary, it might be similar.
      The constraint "independent narrative observations" usually means the Fine axis
      should be a derived insight, not the raw text.
      
      We interpret FR-001 as: The Fine axis must NOT be a direct extract or near-duplicate
      of the source text segment provided.
      
      Threshold: If similarity > 0.8 (very high), it's likely a copy-paste.
      If similarity is moderate, it might be a valid summary.
      
      RE-READING FR-001: "validates that Fine axes originate from independent narrative observations...
      compare the 'Fine' axis text against a provided 'Source Text Segment' ... using a semantic similarity threshold to prove independence."
      
      Interpretation: High similarity = NOT independent (it's the source).
      Low/Moderate similarity = Independent (it's a derived insight).
      
      We set a HIGH threshold (e.g., 0.85) to catch copy-pastes. If the user writes
      a valid independent observation, the similarity to the raw source text should
      be lower than a direct copy.
    """
    model = load_sentence_model()
    
    sem_sim = calculate_semantic_similarity(fine, source_text, model)
    
    # Threshold for "Copy-Paste" detection. If sim > 0.85, it's likely the source text itself.
    # If sim is lower, it suggests the user has processed the text into a new form (observation).
    # However, the prompt says "prove independence". If the similarity is TOO low, maybe it's unrelated?
    # But the context is "independent narrative observations" of the SAME character.
    # The primary risk is copy-pasting the source as the axis definition.
    
    COPY_PASTE_THRESHOLD = 0.85
    
    is_valid = True
    reasons = []
    
    if sem_sim > COPY_PASTE_THRESHOLD:
        is_valid = False
        reasons.append(f"Semantic similarity ({sem_sim:.2f}) to source text is too high (>{COPY_PASTE_THRESHOLD}). "
                       "This suggests the Fine axis is a direct copy of the source text, not an independent observation.")
    
    # Optional: Check if it's too low (unrelated)? No, we assume user intent is valid unless it's a copy.
    
    return is_valid, {
        "semantic_similarity_to_source": sem_sim,
        "is_valid": is_valid,
        "reasons": reasons
    }

def read_input() -> Dict[str, str]:
    """
    Reads input from stdin or arguments.
    Expects a JSON structure or interactive prompts for:
    - character_name
    - coarse_axis (text)
    - fine_axis (text)
    - source_text_segment (text) - required for FR-001 validation
    """
    # Check if input is piped (JSON) or interactive
    if not sys.stdin.isatty():
        try:
            input_data = json.load(sys.stdin)
            # Validate required fields
            required = ['character_name', 'coarse_axis', 'fine_axis', 'source_text_segment']
            for field in required:
                if field not in input_data:
                    raise ValueError(f"Missing required field: {field}")
            return input_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from stdin: {e}")
            sys.exit(1)
    
    # Interactive mode
    print("=== Character Axis Input (FR-001 Independent Observation Validation) ===")
    character_name = input("Enter Character Name: ").strip()
    
    print("\n--- Coarse Axis Definition ---")
    print("Enter the Coarse axis description (e.g., 'Heroic vs Villainous'):")
    coarse_axis = input("> ").strip()
    
    print("\n--- Fine Axis Definition (Independent Observation) ---")
    print("Enter the Fine axis description (derived from narrative, NOT copied):")
    fine_axis = input("> ").strip()
    
    print("\n--- Source Text Segment (for Independence Validation) ---")
    print("Paste the specific source text segment this Fine axis is derived from:")
    print("(Enter the text, then press Enter twice on an empty line to finish)")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    source_text = "\n".join(lines).strip()
    
    if not source_text:
        logger.error("Source text segment is required for FR-001 validation.")
        sys.exit(1)
    
    return {
        "character_name": character_name,
        "coarse_axis": coarse_axis,
        "fine_axis": fine_axis,
        "source_text_segment": source_text
    }

def process_input(data: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Executes the full validation pipeline for T012a.
    1. Validate Coarse vs Fine independence (T012 logic).
    2. Validate Fine vs Source Text independence (FR-001 logic).
    """
    coarse = data['coarse_axis']
    fine = data['fine_axis']
    source = data['source_text_segment']
    
    # 1. Coarse vs Fine
    valid_cf, details_cf = validate_coarse_fine_independence(coarse, fine)
    
    # 2. Fine vs Source (FR-001)
    valid_fs, details_fs = validate_fine_independence_from_source(fine, source)
    
    overall_valid = valid_cf and valid_fs
    
    result = {
        "character_name": data['character_name'],
        "coarse_axis": coarse,
        "fine_axis": fine,
        "source_text_segment": source,
        "overall_valid": overall_valid,
        "checks": {
            "coarse_fine_independence": details_cf,
            "fine_source_independence": details_fs
        }
    }
    
    return overall_valid, result

def main():
    """
    Main entry point for the CLI.
    Reads input, validates, and prints results.
    """
    try:
        input_data = read_input()
    except Exception as e:
        logger.error(f"Input error: {e}")
        sys.exit(1)
    
    overall_valid, result = process_input(input_data)
    
    # Output formatted JSON
    print("\n--- Validation Results ---")
    print(json.dumps(result, indent=2))
    
    if not overall_valid:
        print("\n[ERROR] Validation Failed. Please adjust your inputs.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Axes validated successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
