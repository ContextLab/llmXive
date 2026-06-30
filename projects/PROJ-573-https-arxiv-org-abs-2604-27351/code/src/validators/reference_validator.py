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

logger = get_logger(__name__)

# Constants for thresholds
TITLE_TOKEN_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_REQUIRED_CLAIMS = {"claim:c_5cb9c0de", "claim:c_55db4237", "claim:c_101df1fb"}


def tokenize_title(title: str) -> Set[str]:
    """
    Tokenize a title into a set of lowercase alphanumeric tokens.
    Removes punctuation and splits on whitespace.

    Args:
        title: The title string to tokenize.

    Returns:
        A set of unique lowercase tokens.
    """
    if not title:
        return set()
    # Convert to lowercase and extract alphanumeric words
    tokens = re.findall(r'\b[a-z0-9]+\b', title.lower())
    return set(tokens)


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Formula: |Tokens(A) ∩ Tokens(B)| / |Tokens(A) ∪ Tokens(B)|

    Args:
        title_a: First title string.
        title_b: Second title string.

    Returns:
        Float between 0.0 and 1.0 representing the overlap ratio.
        Returns 0.0 if both sets are empty to avoid division by zero.
    """
    tokens_a = tokenize_title(title_a)
    tokens_b = tokenize_title(title_b)

    if not tokens_a and not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    return len(intersection) / len(union)


def validate_reference_title_overlap(candidate_title: str, reference_title: str) -> Tuple[bool, float]:
    """
    Validate that the candidate title has sufficient token overlap with the reference.

    Args:
        candidate_title: The title proposed by the agent/review.
        reference_title: The ground-truth reference title from the paper.

    Returns:
        Tuple of (is_valid, overlap_score).
        is_valid is True if overlap_score >= TITLE_TOKEN_OVERLAP_THRESHOLD.
    """
    score = compute_title_token_overlap(candidate_title, reference_title)
    is_valid = score >= TITLE_TOKEN_OVERLAP_THRESHOLD
    logger.debug(f"Title overlap check: '{candidate_title[:20]}...' vs '{reference_title[:20]}...' -> {score:.3f}")
    return is_valid, score


def check_constitution_ii_compliance(research_metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if the research metadata satisfies Constitution II requirements.
    Specifically, verifies that required claims are present and valid.

    Constitution II Requirements (Plan Gap):
    - Must cite specific foundational claims (e.g., c_5cb9c0de, c_55db4237).

    Args:
        research_metadata: Dictionary containing 'cited_claims' (list of strings)
                           and optionally 'methodology_notes'.

    Returns:
        Tuple of (is_compliant, missing_claims).
        is_compliant is True if all required claims are present.
    """
    cited_claims = set(research_metadata.get("cited_claims", []))
    missing_claims = list(CONSTITUTION_II_REQUIRED_CLAIMS - cited_claims)

    is_compliant = len(missing_claims) == 0

    if not is_compliant:
        logger.warning(f"Constitution II compliance failed. Missing claims: {missing_claims}")
    else:
        logger.info("Constitution II compliance check passed.")

    return is_compliant, missing_claims


class ReferenceValidatorAgent:
    """
    Agent responsible for validating references before they contribute to review points.

    This agent enforces:
    1. Title Token Overlap Check (>= 0.7)
    2. Constitution II Compliance Gate
    """

    def __init__(self, reference_titles_map: Optional[Dict[str, str]] = None):
        """
        Initialize the validator.

        Args:
            reference_titles_map: A mapping from task_id or claim_id to the expected reference title.
                                  If None, an empty map is used.
        """
        self.reference_titles_map = reference_titles_map or {}
        self._review_points_accumulated = 0
        self._validation_log: List[Dict[str, Any]] = []

    def validate_and_approve(self, task_id: str, candidate_title: str, research_metadata: Dict[str, Any]) -> bool:
        """
        Perform the full validation pipeline for a review contribution.

        Steps:
        1. Retrieve the expected reference title for the task.
        2. Check title token overlap (>= 0.7).
        3. Check Constitution II compliance.
        4. If both pass, increment review points and return True.
           If either fails, log the failure and return False.

        Args:
            task_id: The ID of the task being reviewed.
            candidate_title: The title proposed by the contributor.
            research_metadata: Metadata about the contribution (citations, etc.).

        Returns:
            True if the contribution is approved and points are added.
            False if the contribution is blocked.
        """
        reference_title = self.reference_titles_map.get(task_id)

        # If no reference title is known for this task, we cannot validate overlap.
        # We allow it to pass but log a warning, assuming the task is new or reference is pending.
        if not reference_title:
            logger.warning(f"No reference title found for task {task_id}. Skipping overlap check.")
            overlap_valid = True
            overlap_score = 1.0
        else:
            overlap_valid, overlap_score = validate_reference_title_overlap(candidate_title, reference_title)

        # Check Constitution II
        constitution_valid, missing_claims = check_constitution_ii_compliance(research_metadata)

        # Log the attempt
        log_entry = {
            "task_id": task_id,
            "candidate_title": candidate_title,
            "reference_title": reference_title,
            "overlap_score": overlap_score,
            "overlap_valid": overlap_valid,
            "constitution_valid": constitution_valid,
            "missing_claims": missing_claims,
            "approved": False
        }

        if overlap_valid and constitution_valid:
            self._review_points_accumulated += 1
            log_entry["approved"] = True
            logger.info(f"Validation passed for {task_id}. Points: {self._review_points_accumulated}")
        else:
            reasons = []
            if not overlap_valid:
                reasons.append(f"Title overlap {overlap_score:.2f} < {TITLE_TOKEN_OVERLAP_THRESHOLD}")
            if not constitution_valid:
                reasons.append(f"Missing claims: {missing_claims}")
            log_entry["reasons"] = reasons
            logger.warning(f"Validation BLOCKED for {task_id}: {'; '.join(reasons)}")

        self._validation_log.append(log_entry)
        return log_entry["approved"]

    def get_review_points(self) -> int:
        """Return the total accumulated review points."""
        return self._review_points_accumulated

    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Return the history of validation attempts."""
        return self._validation_log


def main():
    """
    Main entry point for standalone testing of the ReferenceValidatorAgent.
    Demonstrates the blocking gate behavior.
    """
    # Mock reference titles
    references = {
        "T006a": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "T001": "Verify time-series dataset availability"
    }

    agent = ReferenceValidatorAgent(reference_titles_map=references)

    # Test Case 1: Valid title, compliant metadata
    print("Test 1: Valid title + Compliant metadata")
    is_approved = agent.validate_and_approve(
        task_id="T006a",
        candidate_title="Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        research_metadata={"cited_claims": list(CONSTITUTION_II_REQUIRED_CLAIMS)}
    )
    print(f"  Approved: {is_approved} (Expected: True)\n")

    # Test Case 2: Invalid title (low overlap)
    print("Test 2: Invalid title (low overlap)")
    is_approved = agent.validate_and_approve(
        task_id="T006a",
        candidate_title="Completely Different Research Topic",
        research_metadata={"cited_claims": list(CONSTITUTION_II_REQUIRED_CLAIMS)}
    )
    print(f"  Approved: {is_approved} (Expected: False)\n")

    # Test Case 3: Valid title, non-compliant metadata (missing claims)
    print("Test 3: Valid title + Non-compliant metadata")
    is_approved = agent.validate_and_approve(
        task_id="T006a",
        candidate_title="Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        research_metadata={"cited_claims": ["claim:c_12345"]}
    )
    print(f"  Approved: {is_approved} (Expected: False)\n")

    print(f"Total Review Points: {agent.get_review_points()}")


if __name__ == "__main__":
    main()
