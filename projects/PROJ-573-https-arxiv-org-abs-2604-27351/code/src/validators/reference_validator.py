"""
Reference Validator Agent for llmXive automated science pipeline.

Implements:
1. Title-token-overlap check (>= 0.7) before contributing review points.
2. Blocking gate for Constitution II compliance.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration constants
TOKEN_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_KEY = "constitution_ii_compliant"


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a reference title into a set of normalized tokens.
    Lowercases, removes punctuation, and splits on whitespace.
    """
    if not title:
        return []
    # Normalize: lowercase and remove non-alphanumeric chars except spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', title.lower())
    tokens = normalized.split()
    return [t for t in tokens if len(t) > 1]  # Filter very short tokens


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.
    Returns a float between 0.0 and 1.0.
    """
    tokens_a = set(tokenize_title(title_a))
    tokens_b = set(tokenize_title(title_b))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    return len(intersection) / len(union) if union else 0.0


def validate_reference_title_overlap(
    candidate_title: str,
    reference_titles: List[str]
) -> Tuple[bool, float, Optional[str]]:
    """
    Validate that the candidate title has sufficient token overlap (>= 0.7)
    with at least one reference title.

    Returns:
        (is_valid, max_overlap, closest_match_title)
    """
    if not reference_titles:
        logger.warning("No reference titles provided for validation.")
        return False, 0.0, None

    max_overlap = 0.0
    closest_match = None

    for ref_title in reference_titles:
        overlap = compute_title_token_overlap(candidate_title, ref_title)
        if overlap > max_overlap:
            max_overlap = overlap
            closest_match = ref_title

    is_valid = max_overlap >= TOKEN_OVERLAP_THRESHOLD

    if not is_valid:
        logger.warning(
            f"Title overlap check failed. Candidate: '{candidate_title}', "
            f"Max overlap: {max_overlap:.2f} (threshold: {TOKEN_OVERLAP_THRESHOLD})"
        )
    else:
        logger.info(
            f"Title overlap check passed. Candidate: '{candidate_title}', "
            f"Overlap: {max_overlap:.2f} with '{closest_match}'"
        )

    return is_valid, max_overlap, closest_match


def check_constitution_ii_compliance(context: Dict[str, Any]) -> bool:
    """
    Check if the current context satisfies Constitution II compliance.
    Constitution II requires that the reference validation gate is passed
    before contributing review points.

    Args:
        context: Dictionary containing at least:
            - 'title': The candidate reference title
            - 'reference_titles': List of allowed reference titles
            - 'review_points': Points to be contributed

    Returns:
        True if compliant, False otherwise.
    """
    title = context.get("title")
    reference_titles = context.get("reference_titles", [])
    review_points = context.get("review_points", 0)

    if review_points <= 0:
        logger.debug("No review points to contribute; skipping compliance check.")
        return True

    if not title:
        logger.error("Constitution II check failed: Missing candidate title.")
        return False

    is_valid, _, _ = validate_reference_title_overlap(title, reference_titles)

    if not is_valid:
        logger.error(
            f"Constitution II BLOCK: Title '{title}' does not meet overlap threshold. "
            f"Review points contribution blocked."
        )
        return False

    logger.info("Constitution II compliance check passed.")
    return True


class ReferenceValidatorAgent:
    """
    Agent responsible for validating references before they contribute to the benchmark.
    Enforces the title-token-overlap gate and Constitution II compliance.
    """

    def __init__(self, reference_titles: List[str]):
        """
        Initialize the agent with the set of allowed reference titles.

        Args:
            reference_titles: List of canonical reference titles to compare against.
        """
        self.reference_titles = reference_titles
        self.logger = get_logger(__name__)

    def validate_and_contribute(
        self,
        candidate_title: str,
        review_points: int,
        context_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Attempt to contribute review points for a candidate reference.
        Blocks contribution if Constitution II compliance fails.

        Args:
            candidate_title: The title of the reference being reviewed.
            review_points: The number of points to contribute.
            context_metadata: Optional extra context for logging.

        Returns:
            Dict with keys:
                - 'allowed': bool (True if points were contributed)
                - 'points_contributed': int (0 if blocked, review_points if allowed)
                - 'overlap_score': float
                - 'reason': str
        """
        if review_points <= 0:
            return {
                "allowed": True,
                "points_contributed": 0,
                "overlap_score": 0.0,
                "reason": "No points to contribute"
            }

        # Perform overlap check
        is_valid, overlap, closest = validate_reference_title_overlap(
            candidate_title, self.reference_titles
        )

        # Check Constitution II
        context = {
            "title": candidate_title,
            "reference_titles": self.reference_titles,
            "review_points": review_points
        }
        if context_metadata:
            context.update(context_metadata)

        is_compliant = check_constitution_ii_compliance(context)

        if not is_compliant or not is_valid:
            return {
                "allowed": False,
                "points_contributed": 0,
                "overlap_score": overlap,
                "reason": f"Constitution II blocked: overlap {overlap:.2f} < {TOKEN_OVERLAP_THRESHOLD}"
            }

        return {
            "allowed": True,
            "points_contributed": review_points,
            "overlap_score": overlap,
            "reason": "Constitution II compliant"
        }

    def get_reference_titles(self) -> List[str]:
        """Return the list of reference titles used for validation."""
        return self.reference_titles


def main():
    """
    Entry point for standalone testing of the Reference Validator Agent.
    """
    # Example usage
    allowed_titles = [
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "Time-Series Classification with Transformer Models",
        "Tabular Data Analysis using TabPFN"
    ]

    agent = ReferenceValidatorAgent(allowed_titles)

    # Test Case 1: Valid match
    result1 = agent.validate_and_contribute(
        candidate_title="Heterogeneous Scientific Foundation Model Benchmark",
        review_points=5
    )
    print(f"Test 1 (Valid): {result1}")

    # Test Case 2: Invalid match (low overlap)
    result2 = agent.validate_and_contribute(
        candidate_title="Completely Different Topic Title",
        review_points=5
    )
    print(f"Test 2 (Invalid): {result2}")

    # Test Case 3: Zero points
    result3 = agent.validate_and_contribute(
        candidate_title="Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        review_points=0
    )
    print(f"Test 3 (Zero points): {result3}")


if __name__ == "__main__":
    main()
