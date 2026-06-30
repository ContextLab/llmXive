"""
Reference Validator Agent for llmXive.

Implements:
1. Title-token-overlap >= 0.7 check before contributing review points.
2. Blocking gate for Constitution II compliance.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

# Constants
MIN_TOKEN_OVERLAP = 0.7
CONSTITUTION_II_KEY = "constitution_ii_compliant"
REVIEW_POINTS_KEY = "review_points"

logger = get_logger(__name__)


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title into a set of normalized tokens.
    Converts to lowercase, removes punctuation, and splits on whitespace.
    """
    if not title:
        return []
    # Lowercase and remove non-alphanumeric characters except spaces
    normalized = re.sub(r'[^a-z0-9\s]', '', title.lower())
    return normalized.split()


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
    reference_titles: List[str],
    threshold: float = MIN_TOKEN_OVERLAP
) -> Tuple[bool, float, Optional[str]]:
    """
    Validate if a candidate title has sufficient token overlap with any reference title.

    Args:
        candidate_title: The title to validate.
        reference_titles: List of allowed reference titles.
        threshold: Minimum overlap required (default 0.7).

    Returns:
        Tuple of (is_valid, max_overlap, matched_reference_title).
    """
    if not reference_titles:
        logger.warning("No reference titles provided for validation.")
        return False, 0.0, None

    max_overlap = 0.0
    best_match = None

    for ref_title in reference_titles:
        overlap = compute_title_token_overlap(candidate_title, ref_title)
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = ref_title

    is_valid = max_overlap >= threshold
    return is_valid, max_overlap, best_match


def check_constitution_ii_compliance(
    metadata: Dict[str, Any],
    required_fields: Optional[List[str]] = None
) -> bool:
    """
    Check if the provided metadata satisfies Constitution II requirements.

    Constitution II Compliance Rules:
    1. Must have a valid 'source' field.
    2. Must have a valid 'timestamp' field.
    3. Must not be marked as 'fabricated' or 'simulated'.
    4. Must have 'review_points' if applicable.

    Args:
        metadata: Dictionary containing metadata to check.
        required_fields: Optional list of additional required fields.

    Returns:
        True if compliant, False otherwise.
    """
    if required_fields is None:
        required_fields = []

    # Core Constitution II checks
    checks = [
        ("source", metadata.get("source") is not None and metadata.get("source") != ""),
        ("timestamp", metadata.get("timestamp") is not None),
        ("not_fabricated", metadata.get("is_fabricated") is False),
        ("not_simulated", metadata.get("is_simulated") is False),
    ]

    # Add custom required fields
    for field in required_fields:
        checks.append((field, field in metadata and metadata[field] is not None))

    # Check review points if present
    if REVIEW_POINTS_KEY in metadata:
        points = metadata[REVIEW_POINTS_KEY]
        if not isinstance(points, (int, float)) or points < 0:
            checks.append(("valid_review_points", False))
        else:
            checks.append(("valid_review_points", True))

    all_passed = all(passed for _, passed in checks)

    if not all_passed:
        failed_checks = [name for name, passed in checks if not passed]
        logger.warning(f"Constitution II compliance failed: {failed_checks}")

    return all_passed


class ReferenceValidatorAgent:
    """
    Agent responsible for validating references before they contribute to the benchmark.

    This agent enforces:
    1. Title-token-overlap >= 0.7 check.
    2. Constitution II compliance blocking gate.
    """

    def __init__(self, reference_titles: List[str]):
        """
        Initialize the agent with a list of allowed reference titles.

        Args:
            reference_titles: List of titles that are considered valid references.
        """
        self.reference_titles = reference_titles
        self.logger = get_logger(__name__)

    def validate_and_approve(
        self,
        candidate_title: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a candidate reference and return approval status.

        This method performs two checks:
        1. Title token overlap with known references.
        2. Constitution II compliance of the metadata.

        If either check fails, the candidate is rejected and no review points are added.

        Args:
            candidate_title: The title of the candidate reference.
            metadata: Metadata associated with the candidate.

        Returns:
            Dictionary with validation results:
            {
                "approved": bool,
                "reason": str,
                "overlap_score": float,
                "constitution_compliant": bool,
                "review_points_contributed": float
            }
        """
        result = {
            "approved": False,
            "reason": "",
            "overlap_score": 0.0,
            "constitution_compliant": False,
            "review_points_contributed": 0.0
        }

        # Check 1: Title Token Overlap
        is_valid_overlap, overlap_score, matched_title = validate_reference_title_overlap(
            candidate_title,
            self.reference_titles
        )

        result["overlap_score"] = overlap_score

        if not is_valid_overlap:
            result["reason"] = (
                f"Title token overlap {overlap_score:.2f} < {MIN_TOKEN_OVERLAP}. "
                f"Matched: {matched_title}"
            )
            self.logger.warning(f"Validation failed for '{candidate_title}': {result['reason']}")
            return result

        # Check 2: Constitution II Compliance
        is_compliant = check_constitution_ii_compliance(metadata)
        result["constitution_compliant"] = is_compliant

        if not is_compliant:
            result["reason"] = "Constitution II compliance check failed."
            self.logger.warning(f"Validation failed for '{candidate_title}': {result['reason']}")
            return result

        # Both checks passed
        result["approved"] = True
        result["reason"] = "Validation passed."

        # Calculate review points (example logic: 10 points per valid reference)
        points = 10.0
        result["review_points_contributed"] = points

        self.logger.info(
            f"Reference '{candidate_title}' approved. "
            f"Overlap: {overlap_score:.2f}, Points: {points}"
        )

        return result


def main():
    """
    Main entry point for testing the Reference Validator Agent.
    """
    # Example usage
    allowed_titles = [
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "Time-Series Analysis with Transformers",
        "Tabular Data Processing with TabPFN"
    ]

    agent = ReferenceValidatorAgent(allowed_titles)

    # Test Case 1: Valid reference
    test_metadata_1 = {
        "source": "arxiv.org",
        "timestamp": "2024-01-01T00:00:00Z",
        "is_fabricated": False,
        "is_simulated": False
    }

    result_1 = agent.validate_and_approve(
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        test_metadata_1
    )
    print(f"Test 1 (Valid): {result_1}")

    # Test Case 2: Invalid overlap
    result_2 = agent.validate_and_approve(
        "Completely Unrelated Topic",
        test_metadata_1
    )
    print(f"Test 2 (Invalid Overlap): {result_2}")

    # Test Case 3: Constitution II failure
    test_metadata_3 = {
        "source": "",  # Empty source
        "timestamp": "2024-01-01T00:00:00Z",
        "is_fabricated": False,
        "is_simulated": False
    }
    result_3 = agent.validate_and_approve(
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        test_metadata_3
    )
    print(f"Test 3 (Constitution Fail): {result_3}")


if __name__ == "__main__":
    main()