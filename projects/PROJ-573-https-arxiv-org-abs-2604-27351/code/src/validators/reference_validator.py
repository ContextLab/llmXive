"""
Reference Validator Agent for llmXive scientific pipeline.

Implements:
1. Title-token-overlap check (≥ 0.7) before contributing review points.
2. Blocking gate for Constitution II compliance.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

# Threshold for title-token-overlap
TITLE_OVERLAP_THRESHOLD = 0.7
# Constitution II compliance requirement
CONSTITUTION_II_REQUIRED = True

logger = get_logger(__name__)


def tokenize_title(title: str) -> Set[str]:
    """
    Tokenize a paper title into a set of lowercase alphanumeric tokens.

    Args:
        title: The paper title string.

    Returns:
        Set of normalized tokens.
    """
    if not title:
        return set()
    # Lowercase and split on non-alphanumeric characters
    tokens = re.findall(r'[a-z0-9]+', title.lower())
    return set(tokens)


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Formula: |tokens(A) ∩ tokens(B)| / |tokens(A) ∪ tokens(B)|

    Args:
        title_a: First title.
        title_b: Second title.

    Returns:
        Float between 0.0 and 1.0 representing overlap ratio.
    """
    tokens_a = tokenize_title(title_a)
    tokens_b = tokenize_title(title_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def validate_reference_title_overlap(
    candidate_title: str,
    reference_titles: List[str],
    threshold: float = TITLE_OVERLAP_THRESHOLD
) -> Tuple[bool, float, Optional[str]]:
    """
    Validate if a candidate title has sufficient overlap with any reference title.

    Args:
        candidate_title: The title to validate.
        reference_titles: List of reference titles to compare against.
        threshold: Minimum overlap required (default 0.7).

    Returns:
        Tuple of (is_valid, max_overlap, best_match_title).
        is_valid is True if max_overlap >= threshold.
    """
    if not reference_titles:
        logger.warning("No reference titles provided for overlap check.")
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
    review_data: Dict[str, Any],
    constitution_rules: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Check if review data complies with Constitution II requirements.

    Constitution II Requirements (based on project context):
    1. Must have valid source attribution.
    2. Must not contain fabricated metrics (no random/simulated values).
    3. Must have real execution evidence.

    Args:
        review_data: Dictionary containing review metadata and results.
        constitution_rules: Optional custom rules override.

    Returns:
        Tuple of (is_compliant, list_of_violations).
    """
    violations = []

    # Rule 1: Source attribution
    if not review_data.get("source_url") and not review_data.get("source_dataset"):
        violations.append("Missing source attribution (URL or dataset name)")

    # Rule 2: Check for fabricated metrics
    results = review_data.get("results", {})
    if results:
        for key, value in results.items():
            if isinstance(value, dict):
                # Check for flags indicating fabrication
                if value.get("fabricated") or value.get("simulated"):
                    violations.append(f"Fabricated metric detected: {key}")
                # Check for placeholder values
                if value.get("value") in ["N/A", "placeholder", "TODO", "simulated"]:
                    violations.append(f"Placeholder value detected: {key}")

    # Rule 3: Execution evidence
    if not review_data.get("execution_log"):
        violations.append("Missing execution log evidence")
    
    # Check for specific error patterns in logs if available
    execution_log = review_data.get("execution_log", "")
    if "FABRICATED" in execution_log.upper() or "SIMULATED" in execution_log.upper():
        violations.append("Execution log contains fabrication indicators")

    is_compliant = len(violations) == 0
    return is_compliant, violations


class ReferenceValidatorAgent:
    """
    Agent that validates research references and review contributions.

    Responsibilities:
    1. Verify title-token-overlap ≥ 0.7 before allowing review points.
    2. Enforce Constitution II compliance as a blocking gate.
    """

    def __init__(
        self,
        reference_titles: List[str],
        constitution_rules: Optional[Dict[str, Any]] = None,
        overlap_threshold: float = TITLE_OVERLAP_THRESHOLD
    ):
        """
        Initialize the Reference Validator Agent.

        Args:
            reference_titles: List of valid reference titles for overlap checking.
            constitution_rules: Optional custom Constitution II rules.
            overlap_threshold: Minimum title overlap required (default 0.7).
        """
        self.reference_titles = reference_titles
        self.constitution_rules = constitution_rules or {}
        self.overlap_threshold = overlap_threshold
        self.logger = get_logger(self.__class__.__name__)

    def validate_contribution(
        self,
        candidate_title: str,
        review_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a review contribution against all gates.

        Args:
            candidate_title: The title of the paper being reviewed.
            review_data: The review data to validate.

        Returns:
            Dictionary with validation results:
            {
                "allowed": bool,
                "overlap_valid": bool,
                "overlap_score": float,
                "constitution_valid": bool,
                "violations": List[str],
                "message": str
            }
        """
        result = {
            "allowed": False,
            "overlap_valid": False,
            "overlap_score": 0.0,
            "constitution_valid": False,
            "violations": [],
            "message": ""
        }

        # Gate 1: Title-token-overlap check
        overlap_valid, overlap_score, best_match = validate_reference_title_overlap(
            candidate_title,
            self.reference_titles,
            self.overlap_threshold
        )
        result["overlap_valid"] = overlap_valid
        result["overlap_score"] = overlap_score

        if not overlap_valid:
            result["violations"].append(
                f"Title overlap {overlap_score:.2f} < {self.overlap_threshold} "
                f"(best match: {best_match})"
            )

        # Gate 2: Constitution II compliance
        constitution_valid, violations = check_constitution_ii_compliance(
            review_data,
            self.constitution_rules
        )
        result["constitution_valid"] = constitution_valid
        result["violations"].extend(violations)

        # Final decision
        if overlap_valid and constitution_valid:
            result["allowed"] = True
            result["message"] = "Contribution validated successfully."
            self.logger.info(f"Contribution validated for title: {candidate_title}")
        else:
            result["message"] = (
                f"Validation failed. Overlap: {overlap_valid}, "
                f"Constitution: {constitution_valid}. "
                f"Issues: {', '.join(result['violations'])}"
            )
            self.logger.warning(f"Contribution blocked for title: {candidate_title}")

        return result

    def get_reference_titles(self) -> List[str]:
        """Return the list of reference titles."""
        return self.reference_titles


def main():
    """
    Main entry point for the Reference Validator Agent.
    Demonstrates usage with sample data.
    """
    # Sample reference titles (in real use, these would come from a database)
    reference_titles = [
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "Time Series Analysis with Transformer Models",
        "Tabular Data Processing using TabPFN",
        "Unified Text Translation for Multi-Modal Learning"
    ]

    # Initialize agent
    agent = ReferenceValidatorAgent(
        reference_titles=reference_titles,
        overlap_threshold=0.7
    )

    # Test Case 1: Valid contribution
    print("--- Test Case 1: Valid Contribution ---")
    valid_review = {
        "source_url": "https://arxiv.org/abs/2604.27351",
        "results": {"accuracy": 0.85},
        "execution_log": "Ran benchmark successfully. All metrics real."
    }
    result1 = agent.validate_contribution(
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        valid_review
    )
    print(f"Allowed: {result1['allowed']}")
    print(f"Overlap: {result1['overlap_score']:.2f}")
    print(f"Message: {result1['message']}")

    # Test Case 2: Low overlap
    print("\n--- Test Case 2: Low Overlap ---")
    result2 = agent.validate_contribution(
        "Random Unrelated Paper Title",
        valid_review
    )
    print(f"Allowed: {result2['allowed']}")
    print(f"Overlap: {result2['overlap_score']:.2f}")
    print(f"Message: {result2['message']}")

    # Test Case 3: Constitution II violation (fabricated data)
    print("\n--- Test Case 3: Constitution II Violation ---")
    invalid_review = {
        "source_url": "https://example.com",
        "results": {"accuracy": {"value": "simulated", "fabricated": True}},
        "execution_log": "Simulation complete."
    }
    result3 = agent.validate_contribution(
        "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        invalid_review
    )
    print(f"Allowed: {result3['allowed']}")
    print(f"Violations: {result3['violations']}")
    print(f"Message: {result3['message']}")


if __name__ == "__main__":
    main()