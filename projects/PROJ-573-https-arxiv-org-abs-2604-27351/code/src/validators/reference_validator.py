"""
Reference Validator Agent for llmXive.

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

# Constants for Constitution II compliance
CONSTITUTION_II_REQUIRED_FIELDS = [
    "title",
    "abstract",
    "methodology",
    "results",
    "conclusion",
    "references"
]

# Threshold for title token overlap
TITLE_OVERLAP_THRESHOLD = 0.7


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a paper title into a set of lowercase words.

    Args:
        title: The paper title string.

    Returns:
        A list of lowercase alphanumeric tokens.
    """
    if not title or not isinstance(title, str):
        return []

    # Convert to lowercase and extract alphanumeric words
    tokens = re.findall(r'\b[a-z0-9]+\b', title.lower())
    return tokens


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Args:
        title_a: First title string.
        title_b: Second title string.

    Returns:
        A float between 0.0 and 1.0 representing the overlap ratio.
        Returns 0.0 if either title has no tokens.
    """
    tokens_a = set(tokenize_title(title_a))
    tokens_b = set(tokenize_title(title_b))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)


def validate_reference_title_overlap(
    candidate_title: str,
    reference_titles: List[str],
    threshold: float = TITLE_OVERLAP_THRESHOLD
) -> Tuple[bool, float, Optional[str]]:
    """
    Validate that a candidate title does not have excessive overlap with existing references.

    This acts as a gate to prevent duplicate or near-duplicate submissions.

    Args:
        candidate_title: The title of the paper being reviewed.
        reference_titles: List of titles from existing references.
        threshold: The minimum overlap ratio that triggers a block (default 0.7).

    Returns:
        A tuple of (is_valid, max_overlap, conflicting_title).
        - is_valid: True if no overlap exceeds threshold.
        - max_overlap: The highest overlap ratio found.
        - conflicting_title: The title that caused the conflict, or None if valid.
    """
    max_overlap = 0.0
    conflicting_title = None

    for ref_title in reference_titles:
        overlap = compute_title_token_overlap(candidate_title, ref_title)
        if overlap > max_overlap:
            max_overlap = overlap
            conflicting_title = ref_title

        if overlap >= threshold:
            logger.warning(
                f"Title overlap threshold exceeded: {overlap:.2f} >= {threshold} "
                f"against '{ref_title[:50]}...'"
            )
            return False, max_overlap, conflicting_title

    logger.info(f"Title validation passed. Max overlap: {max_overlap:.2f}")
    return True, max_overlap, None


def check_constitution_ii_compliance(doc: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if a document review entry complies with Constitution II requirements.

    Constitution II requires specific sections to be present and non-empty.

    Args:
        doc: A dictionary representing a review entry or document.

    Returns:
        A tuple of (is_compliant, missing_fields).
        - is_compliant: True if all required fields are present and non-empty.
        - missing_fields: List of required field names that are missing or empty.
    """
    missing_fields = []

    for field in CONSTITUTION_II_REQUIRED_FIELDS:
        value = doc.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)

    is_compliant = len(missing_fields) == 0

    if not is_compliant:
        logger.error(
            f"Constitution II compliance failed. Missing fields: {missing_fields}"
        )
    else:
        logger.info("Constitution II compliance check passed.")

    return is_compliant, missing_fields


class ReferenceValidatorAgent:
    """
    Agent responsible for validating research references before contributing points.

    This agent enforces:
    1. Title-token-overlap check (>= 0.7 blocks contribution).
    2. Constitution II compliance (missing required fields blocks contribution).
    """

    def __init__(
        self,
        reference_db_path: Optional[Path] = None,
        title_overlap_threshold: float = TITLE_OVERLAP_THRESHOLD
    ):
        """
        Initialize the Reference Validator Agent.

        Args:
            reference_db_path: Path to a JSON/YAML file containing existing reference titles.
            title_overlap_threshold: Threshold for blocking duplicate titles.
        """
        self.reference_titles: List[str] = []
        self.title_overlap_threshold = title_overlap_threshold
        self.logger = get_logger(__name__)

        if reference_db_path and reference_db_path.exists():
            self._load_reference_titles(reference_db_path)
        else:
            self.logger.info("No reference database found. Starting with empty list.")

    def _load_reference_titles(self, path: Path) -> None:
        """Load existing reference titles from a JSON or YAML file."""
        import json
        import yaml

        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix == '.json':
                    data = json.load(f)
                else:
                    self.logger.warning(f"Unsupported file format: {path.suffix}")
                    return

            if isinstance(data, list):
                self.reference_titles = [
                    item.get('title', '') for item in data if isinstance(item, dict)
                ]
            elif isinstance(data, dict) and 'references' in data:
                self.reference_titles = [
                    ref.get('title', '') for ref in data['references']
                    if isinstance(ref, dict)
                ]

            self.logger.info(f"Loaded {len(self.reference_titles)} reference titles.")

        except Exception as e:
            self.logger.error(f"Failed to load reference database: {e}")
            self.reference_titles = []

    def validate_contribution(
        self,
        candidate_review: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate a candidate review contribution.

        Args:
            candidate_review: A dictionary containing 'title' and review content fields.

        Returns:
            A tuple of (is_allowed, reason, validation_details).
            - is_allowed: True if the review can be contributed.
            - reason: Human-readable explanation of the decision.
            - validation_details: Dictionary with metrics (overlap score, missing fields, etc).
        """
        title = candidate_review.get('title', '')
        details = {
            'title_overlap_valid': False,
            'constitution_ii_compliant': False,
            'max_overlap': 0.0,
            'conflicting_title': None,
            'missing_constitution_fields': []
        }

        # Step 1: Check Title Token Overlap
        is_overlap_valid, max_overlap, conflicting = validate_reference_title_overlap(
            title,
            self.reference_titles,
            self.title_overlap_threshold
        )

        details['max_overlap'] = max_overlap
        details['conflicting_title'] = conflicting
        details['title_overlap_valid'] = is_overlap_valid

        if not is_overlap_valid:
            return (
                False,
                f"Title overlap too high ({max_overlap:.2f}) with '{conflicting}'. "
                "Contribution blocked.",
                details
            )

        # Step 2: Check Constitution II Compliance
        is_compliant, missing_fields = check_constitution_ii_compliance(candidate_review)
        details['constitution_ii_compliant'] = is_compliant
        details['missing_constitution_fields'] = missing_fields

        if not is_compliant:
            return (
                False,
                f"Constitution II compliance failed. Missing fields: {missing_fields}. "
                "Contribution blocked.",
                details
            )

        # If both checks pass
        self.logger.info(
            f"Review contribution validated successfully for title: '{title[:50]}...'"
        )
        return (True, "Validation passed. Contribution allowed.", details)

    def contribute_review(self, review: Dict[str, Any]) -> bool:
        """
        Attempt to contribute a review. Returns True if accepted, False if blocked.

        This is a convenience method that calls validate_contribution and logs the result.
        """
        allowed, reason, details = self.validate_contribution(review)
        if allowed:
            # In a real system, we would save the review here
            self.reference_titles.append(review.get('title', ''))
        return allowed


def main() -> None:
    """
    Main entry point for standalone testing of the Reference Validator Agent.
    """
    # Example usage
    agent = ReferenceValidatorAgent()

    # Test Case 1: Valid review
    valid_review = {
        "title": "A Novel Approach to Heterogeneous Foundation Models",
        "abstract": "This paper presents...",
        "methodology": "We used...",
        "results": "Our results show...",
        "conclusion": "We conclude...",
        "references": ["..."]
    }

    allowed, reason, details = agent.validate_contribution(valid_review)
    print(f"Test 1 (Valid): {allowed} - {reason}")
    print(f"  Details: {details}")

    # Test Case 2: Duplicate title (high overlap)
    duplicate_review = {
        "title": "A Novel Approach to Heterogeneous Foundation Models",
        "abstract": "This paper presents...",
        "methodology": "We used...",
        "results": "Our results show...",
        "conclusion": "We conclude...",
        "references": ["..."]
    }
    # Add the valid review title to the agent's DB to simulate a duplicate
    agent.reference_titles.append(valid_review["title"])

    allowed, reason, details = agent.validate_contribution(duplicate_review)
    print(f"Test 2 (Duplicate): {allowed} - {reason}")
    print(f"  Details: {details}")

    # Test Case 3: Missing Constitution II fields
    incomplete_review = {
        "title": "Another Novel Approach",
        "abstract": "Brief abstract",
        # Missing methodology, results, etc.
    }
    allowed, reason, details = agent.validate_contribution(incomplete_review)
    print(f"Test 3 (Incomplete): {allowed} - {reason}")
    print(f"  Details: {details}")


if __name__ == "__main__":
    main()