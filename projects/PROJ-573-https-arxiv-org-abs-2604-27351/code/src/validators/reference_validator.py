"""
Reference Validator Agent for llmXive.

Implements a blocking gate for Constitution II compliance and validates
reference contributions using title-token-overlap scoring.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for validation
MIN_TITLE_OVERLAP_SCORE = 0.7
CONSTITUTION_II_REQUIREMENTS = [
    "title_token_overlap",
    "source_verification",
    "citation_format",
]


def normalize_text(text: str) -> str:
    """Normalize text for token comparison: lowercase and remove punctuation."""
    text = text.lower()
    # Remove punctuation and extra whitespace
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text: str) -> Set[str]:
    """Tokenize normalized text into a set of words."""
    return set(normalize_text(text).split())


def compute_title_token_overlap(title1: str, title2: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Args:
        title1: First title string.
        title2: Second title string.

    Returns:
        Float between 0.0 and 1.0 representing the overlap score.
    """
    tokens1 = tokenize(title1)
    tokens2 = tokenize(title2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


class ReferenceValidatorAgent:
    """
    Agent responsible for validating reference contributions against
    Constitution II compliance requirements.

    This agent enforces:
    1. Title-token-overlap score >= 0.7 for reference matching.
    2. Blocking gate for Constitution II compliance before points contribution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ReferenceValidatorAgent.

        Args:
            config: Optional configuration dictionary. Can contain:
                    - min_overlap_threshold: Override default 0.7 threshold.
        """
        self.config = config or {}
        self.min_overlap_threshold = self.config.get(
            "min_overlap_threshold", MIN_TITLE_OVERLAP_SCORE
        )
        logger.info(f"ReferenceValidatorAgent initialized with threshold {self.min_overlap_threshold}")

    def validate_title_match(
        self, submitted_title: str, reference_title: str
    ) -> Tuple[bool, float]:
        """
        Validate if a submitted reference title matches a known reference.

        Args:
            submitted_title: Title from the contribution.
            reference_title: Title from the known reference database.

        Returns:
            Tuple of (is_valid, overlap_score).
            is_valid is True if overlap_score >= min_overlap_threshold.
        """
        score = compute_title_token_overlap(submitted_title, reference_title)
        is_valid = score >= self.min_overlap_threshold

        if not is_valid:
            logger.warning(
                f"Title overlap {score:.3f} below threshold {self.min_overlap_threshold} "
                f"for submitted: '{submitted_title[:50]}...' vs ref: '{reference_title[:50]}...'"
            )
        else:
            logger.debug(
                f"Title overlap {score:.3f} passed for: '{submitted_title[:50]}...'"
            )

        return is_valid, score

    def check_constitution_ii_compliance(
        self, contribution_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if a contribution meets Constitution II compliance requirements.

        Args:
            contribution_data: Dictionary containing contribution details.
                               Expected keys: 'title', 'source', 'citation'.

        Returns:
            Tuple of (is_compliant, list_of_missing_requirements).
        """
        missing = []
        requirements_met = []

        # Check 1: Title Token Overlap
        if "title" not in contribution_data:
            missing.append("title_token_overlap")
        elif "reference_title" not in contribution_data:
            missing.append("title_token_overlap")
        else:
            is_valid, score = self.validate_title_match(
                contribution_data["title"], contribution_data["reference_title"]
            )
            if not is_valid:
                missing.append("title_token_overlap")
            else:
                requirements_met.append(f"title_token_overlap (score: {score:.3f})")

        # Check 2: Source Verification
        if "source" not in contribution_data or not contribution_data["source"]:
            missing.append("source_verification")
        else:
            requirements_met.append("source_verification")

        # Check 3: Citation Format
        if "citation" not in contribution_data or not contribution_data["citation"]:
            missing.append("citation_format")
        else:
            requirements_met.append("citation_format")

        is_compliant = len(missing) == 0

        if not is_compliant:
            logger.warning(
                f"Contribution failed Constitution II check. Missing: {missing}"
            )
        else:
            logger.info(f"Contribution passed Constitution II check: {requirements_met}")

        return is_compliant, missing

    def evaluate_contribution(
        self, contribution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform full evaluation of a contribution.

        Args:
            contribution_data: Dictionary with contribution details.

        Returns:
            Dictionary with evaluation results including:
            - passed: Boolean indicating if contribution is approved.
            - score: Overlap score (if applicable).
            - missing_requirements: List of failed checks.
        """
        is_compliant, missing = self.check_constitution_ii_compliance(contribution_data)

        result = {
            "passed": is_compliant,
            "missing_requirements": missing,
            "score": None,
            "message": ""
        }

        if is_compliant:
            result["message"] = "Contribution approved for points allocation."
        else:
            result["message"] = f"Contribution blocked. Missing: {', '.join(missing)}"

        # Extract score if title validation was attempted
        if "title" in contribution_data and "reference_title" in contribution_data:
            _, score = self.validate_title_match(
                contribution_data["title"], contribution_data["reference_title"]
            )
            result["score"] = score

        return result


def main():
    """
    Entry point for standalone execution and demonstration.
    """
    logger.info("Starting ReferenceValidatorAgent demonstration.")

    # Create agent instance
    validator = ReferenceValidatorAgent()

    # Test Case 1: Valid Match
    test_contribution_1 = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "source": "arxiv.org",
        "citation": "2604.27351"
    }
    result_1 = validator.evaluate_contribution(test_contribution_1)
    logger.info(f"Test 1 (Exact Match): {result_1}")

    # Test Case 2: Invalid Match (Low Overlap)
    test_contribution_2 = {
        "title": "Different Paper Title Completely Unrelated",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "source": "arxiv.org",
        "citation": "1234.5678"
    }
    result_2 = validator.evaluate_contribution(test_contribution_2)
    logger.info(f"Test 2 (Low Overlap): {result_2}")

    # Test Case 3: Missing Source
    test_contribution_3 = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "source": "",
        "citation": "2604.27351"
    }
    result_3 = validator.evaluate_contribution(test_contribution_3)
    logger.info(f"Test 3 (Missing Source): {result_3}")

    logger.info("ReferenceValidatorAgent demonstration complete.")


if __name__ == "__main__":
    main()
