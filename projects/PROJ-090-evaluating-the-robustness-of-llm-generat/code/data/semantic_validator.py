import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import torch
from sentence_transformers import SentenceTransformer

from config import ensure_directories, get_semantic_threshold
from utils.logging import init_logging, get_perturbation_logger

# Constants
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RAW_INPUT_PATH = "data/processed/perturbation_candidates_raw.json"
VALIDATED_OUTPUT_PATH = "data/processed/perturbation_candidates_validated.json"
HALT_REPORT_PATH = "data/logs/halt_report.json"
THRESHOLD = 0.95

def get_model() -> SentenceTransformer:
    """Load the sentence transformer model."""
    logger = logging.getLogger("semantic_validator")
    logger.info(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    model.eval()
    return model

def compute_similarity(
    model: SentenceTransformer, text_a: str, text_b: str
) -> float:
    """Compute cosine similarity between two texts."""
    embeddings = model.encode([text_a, text_b], convert_to_tensor=True)
    cosine_sim = torch.nn.functional.cosine_similarity(
        embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0)
    )
    return float(cosine_sim.item())

def validate_perturbation(
    model: SentenceTransformer, original: str, candidate: str, threshold: float
) -> Tuple[float, bool]:
    """
    Validate a single perturbation candidate.
    Returns (similarity_score, is_valid).
    """
    score = compute_similarity(model, original, candidate)
    is_valid = score > threshold
    return score, is_valid

def load_raw_candidates() -> List[Dict[str, Any]]:
    """Load the raw candidates from the previous step."""
    path = Path(RAW_INPUT_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Raw candidates file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_validated_candidates(candidates: List[Dict[str, Any]]) -> None:
    """Save the validated candidates to disk."""
    ensure_directories([Path(VALIDATED_OUTPUT_PATH).parent])
    with open(VALIDATED_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)

def save_halt_report(reason: str) -> None:
    """Save a halt report if yield is zero."""
    ensure_directories([Path(HALT_REPORT_PATH).parent])
    report = {"reason": reason}
    with open(HALT_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def validate_perturbation_batch(
    candidates: List[Dict[str, Any]], model: SentenceTransformer
) -> List[Dict[str, Any]]:
    """
    Validate all candidates in the batch.
    Updates 'is_valid' and 'raw_score' fields in-place.
    """
    logger = logging.getLogger("semantic_validator")
    validated_count = 0

    for item in candidates:
        original_text = item.get("original_text", "")
        candidate_text = item.get("candidate_text", "")

        if not original_text or not candidate_text:
            logger.warning(
                f"Skipping item {item.get('task_id')} due to missing text."
            )
            continue

        score, is_valid = validate_perturbation(
            model, original_text, candidate_text, THRESHOLD
        )

        # Update the item
        item["raw_score"] = score
        item["is_valid"] = is_valid

        if is_valid:
            validated_count += 1

        # Log raw score for every candidate
        logger.debug(
            f"Task {item['task_id']} ({item['perturbation_type']}): "
            f"Score={score:.4f}, Valid={is_valid}"
        )

    return candidates

def evaluate_feasibility(candidates: List[Dict[str, Any]]) -> bool:
    """
    Check if the dataset has any valid candidates.
    Returns True if valid yield > 0, False otherwise.
    """
    return any(c.get("is_valid", False) for c in candidates)

def main() -> None:
    """Main entry point for semantic validation."""
    # Setup logging
    init_logging()
    logger = get_perturbation_logger()
    logger.info("Starting Semantic Validation (T016)")

    # Pre-check: Verify raw file exists
    if not Path(RAW_INPUT_PATH).exists():
        logger.error(
            f"Pre-check failed: {RAW_INPUT_PATH} does not exist. "
            "Please run T017 first."
        )
        # We log error but proceed to exit gracefully as per "fail loudly"
        # However, task spec says: "if not, log error and exit"
        sys.exit(1)

    try:
        # Load raw candidates
        logger.info(f"Loading raw candidates from {RAW_INPUT_PATH}")
        candidates = load_raw_candidates()
        logger.info(f"Loaded {len(candidates)} candidates.")

        if not candidates:
            logger.warning("Raw candidates list is empty.")
            save_halt_report("ZERO_YIELD")
            # Proceed with available data (empty list)
            save_validated_candidates([])
            return

        # Load model
        model = get_model()

        # Validate batch
        logger.info("Validating perturbations...")
        validated_candidates = validate_perturbation_batch(candidates, model)

        # Check yield
        valid_count = sum(1 for c in validated_candidates if c.get("is_valid"))
        logger.info(f"Validation complete. Valid count: {valid_count}/{len(validated_candidates)}")

        if valid_count == 0:
            logger.warning(
                "ZERO_YIELD: No candidates passed the semantic threshold (>0.95). "
                "Saving halt report and proceeding with available data (empty)."
            )
            save_halt_report("ZERO_YIELD")

        # Save results
        save_validated_candidates(validated_candidates)
        logger.info(f"Saved validated candidates to {VALIDATED_OUTPUT_PATH}")

    except Exception as e:
        logger.exception(f"Critical error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()