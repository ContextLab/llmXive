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

# Constants for thresholds
TOKEN_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_REQUIRED_FIELDS = ["title", "abstract", "authors", "year", "doi"]

logger = get_logger(__name__)


def tokenize_title(title: str) -> Set[str]:
    """
    Tokenize a paper title into a set of lowercase alphanumeric tokens.
    Removes punctuation and splits on whitespace.

    Args:
        title: The paper title string.

    Returns:
        Set of normalized tokens.
    """
    if not title:
        return set()
    # Lowercase, remove non-alphanumeric (except spaces), split
    tokens = re.sub(r'[^a-z0-9\s]', '', title.lower()).split()
    # Filter out very short tokens (stopwords like 'a', 'the' could be added later)
    return {t for t in tokens if len(t) > 2}


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Formula: |Tokens(A) ∩ Tokens(B)| / |Tokens(A) ∪ Tokens(B)|

    Args:
        title_a: First title string.
        title_b: Second title string.

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


def validate_reference_title_overlap(reference_title: str, known_titles: List[str]) -> Tuple[bool, float, Optional[str]]:
    """
    Check if a reference title has sufficient overlap (>= 0.7) with any known title.
    This acts as a deduplication or relevance check before allowing review points.

    Args:
        reference_title: The title of the reference being validated.
        known_titles: List of existing/reference titles to compare against.

    Returns:
        Tuple of (is_valid, max_overlap_score, matched_title).
        is_valid is True if max_overlap >= TOKEN_OVERLAP_THRESHOLD.
    """
    max_overlap = 0.0
    best_match = None

    for known in known_titles:
        overlap = compute_title_token_overlap(reference_title, known)
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = known

    is_valid = max_overlap >= TOKEN_OVERLAP_THRESHOLD

    if is_valid:
        logger.info(f"Reference title '{reference_title}' passed overlap check with '{best_match}' (score: {max_overlap:.3f})")
    else:
        logger.warning(f"Reference title '{reference_title}' failed overlap check. Max score: {max_overlap:.3f} (threshold: {TOKEN_OVERLAP_THRESHOLD})")

    return is_valid, max_overlap, best_match


def check_constitution_ii_compliance(reference_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if a reference entry complies with Constitution II requirements.
    Constitution II requires specific metadata fields to be present and non-empty.

    Args:
        reference_data: Dictionary containing reference metadata.

    Returns:
        Tuple of (is_compliant, list_of_missing_fields).
    """
    missing_fields = []
    for field in CONSTITUTION_II_REQUIRED_FIELDS:
        value = reference_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)

    is_compliant = len(missing_fields) == 0

    if not is_compliant:
        logger.error(f"Reference failed Constitution II compliance. Missing: {missing_fields}")
    else:
        logger.info("Reference passed Constitution II compliance check.")

    return is_compliant, missing_fields


class ReferenceValidatorAgent:
    """
    Agent that validates references before they contribute to the review process.

    Logic:
    1. Check Constitution II compliance (blocking gate).
    2. Check title-token-overlap against known references (>= 0.7).
    3. Only if both pass, the reference is allowed to contribute points.
    """

    def __init__(self, known_titles: Optional[List[str]] = None):
        """
        Initialize the validator agent.

        Args:
            known_titles: Optional list of existing titles to compare against for overlap.
        """
        self.known_titles = known_titles or []
        self.logger = get_logger(__name__)

    def validate_reference(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform full validation on a reference entry.

        Args:
            reference: Dictionary containing reference data (title, abstract, etc.).

        Returns:
            Dictionary with validation results:
            {
                "allowed": bool,
                "constitution_valid": bool,
                "overlap_valid": bool,
                "overlap_score": float,
                "errors": list of strings
            }
        """
        errors = []
        allowed = True

        # 1. Constitution II Check (Blocking Gate)
        const_valid, missing_fields = check_constitution_ii_compliance(reference)
        if not const_valid:
            errors.append(f"Constitution II violation: missing fields {missing_fields}")
            allowed = False

        # 2. Title Overlap Check (Only if we have known titles to compare)
        overlap_valid = True
        overlap_score = 0.0
        reference_title = reference.get("title", "")

        if self.known_titles and reference_title:
            overlap_valid, overlap_score, _ = validate_reference_title_overlap(reference_title, self.known_titles)
            if not overlap_valid:
                errors.append(f"Title overlap too low ({overlap_score:.3f} < {TOKEN_OVERLAP_THRESHOLD})")
                allowed = False
        elif not self.known_titles:
            self.logger.debug("No known titles provided for overlap check; skipping.")

        return {
            "allowed": allowed,
            "constitution_valid": const_valid,
            "overlap_valid": overlap_valid,
            "overlap_score": overlap_score,
            "errors": errors
        }

    def add_known_title(self, title: str) -> None:
        """Add a title to the set of known titles for future overlap checks."""
        if title not in self.known_titles:
            self.known_titles.append(title)
            self.logger.debug(f"Added known title: {title}")


def main():
    """
    Main entry point for testing the Reference Validator Agent.
    Runs a simple demonstration of the validation logic.
    """
    logger.info("Starting Reference Validator Agent demonstration.")

    # Initialize agent with a known reference
    agent = ReferenceValidatorAgent(known_titles=[
        "Deep Learning for Time Series Forecasting: A Survey",
        "TabPFN: A Transformer for Tabular Data"
    ])

    # Test Case 1: Valid reference (Constitution II pass, Overlap pass)
    valid_ref = {
        "title": "Deep Learning for Time Series: A Survey Update",
        "abstract": "Updated survey on time series...",
        "authors": ["Jane Doe"],
        "year": 2024,
        "doi": "10.1234/update"
    }
    result1 = agent.validate_reference(valid_ref)
    print(f"Test 1 (Valid Ref): {result1}")

    # Test Case 2: Invalid Constitution II (Missing fields)
    invalid_const_ref = {
        "title": "Some Paper",
        # Missing abstract, authors, year, doi
    }
    result2 = agent.validate_reference(invalid_const_ref)
    print(f"Test 2 (Invalid Constitution): {result2}")

    # Test Case 3: Low Overlap
    low_overlap_ref = {
        "title": "Completely Unrelated Topic",
        "abstract": "No relation to anything here.",
        "authors": ["John Smith"],
        "year": 2023,
        "doi": "10.1234/unrelated"
    }
    result3 = agent.validate_reference(low_overlap_ref)
    print(f"Test 3 (Low Overlap): {result3}")

    logger.info("Reference Validator Agent demonstration complete.")


if __name__ == "__main__":
    main()
