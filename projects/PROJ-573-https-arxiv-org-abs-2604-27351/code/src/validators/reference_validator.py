"""
Reference Validator Agent for llmXive.

Implements a blocking gate for Constitution II compliance:
- Computes title-token-overlap between a proposed review and the target paper title.
- Requires overlap >= 0.7 to contribute review points.
- Validates Constitution II compliance before allowing any contribution.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from src.utils.logging import get_logger

# Constants
MIN_TITLE_OVERLAP = 0.7
CONSTITUTION_II_VERSION = "1.0"

logger = get_logger(__name__)


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into lowercase alphanumeric tokens.
    Removes punctuation and splits on whitespace.
    """
    if not text:
        return []
    # Convert to lowercase and extract alphanumeric words
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def compute_title_token_overlap(title1: str, title2: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Returns:
        float: Overlap ratio between 0.0 and 1.0.
               1.0 if both sets are identical, 0.0 if no overlap.
    """
    tokens1 = set(tokenize_text(title1))
    tokens2 = set(tokenize_text(title2))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)

    return len(intersection) / len(union) if union else 0.0


def validate_constitution_ii(
    proposed_review: str,
    target_paper_title: str,
    constitution_text: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate if a proposed review complies with Constitution II.

    Constitution II Requirements:
    1. Title-token-overlap >= 0.7 between the review's focus and the target paper.
    2. No fabrication of data or results.
    3. Adherence to scientific methodology.

    Args:
        proposed_review: The text of the proposed review/contribution.
        target_paper_title: The title of the target paper being reviewed.
        constitution_text: Optional full text of Constitution II (defaults to internal rules).

    Returns:
        Tuple[bool, Dict]: (is_compliant, details)
                           details contains: overlap_score, blocked_reason, etc.
    """
    details = {
        "constitution_version": CONSTITUTION_II_VERSION,
        "overlap_score": 0.0,
        "is_compliant": False,
        "blocked_reason": None,
        "checks_performed": []
    }

    # Check 1: Title Token Overlap
    overlap = compute_title_token_overlap(proposed_review, target_paper_title)
    details["overlap_score"] = overlap
    details["checks_performed"].append("title_token_overlap")

    if overlap < MIN_TITLE_OVERLAP:
        details["blocked_reason"] = f"Title overlap {overlap:.2f} < {MIN_TITLE_OVERLAP}"
        logger.warning(f"Constitution II Violation: {details['blocked_reason']}")
        return False, details

    # Check 2: Fabrication Detection (Heuristic)
    # Look for keywords indicating simulation/fabrication without data
    fabrication_keywords = [
        "simulated", "fabricated", "placeholder", "fake", "hypothetical",
        "random.uniform", "np.random", "mock data", "invented"
    ]
    review_lower = proposed_review.lower()
    for keyword in fabrication_keywords:
        if keyword in review_lower:
            # Allow if it's explicitly stating what was NOT done
            if "not " in review_lower or "no " in review_lower:
                continue
            details["checks_performed"].append("fabrication_check")
            details["blocked_reason"] = f"Potential fabrication detected: '{keyword}'"
            logger.warning(f"Constitution II Violation: {details['blocked_reason']}")
            return False, details

    # Check 3: Methodology Consistency (Basic)
    # Ensure the review mentions at least one dataset or model name if it claims results
    if "result" in review_lower or "accuracy" in review_lower or "metric" in review_lower:
        # Simple heuristic: if claiming results, must mention a source or method
        if not any(word in review_lower for word in ["dataset", "model", "experiment", "run", "measure"]):
             details["checks_performed"].append("methodology_check")
             # Not a hard block for this agent, just a warning
             logger.info("Review claims results but lacks explicit methodology reference.")

    details["checks_performed"].append("all_checks_passed")
    details["is_compliant"] = True
    logger.info(f"Constitution II Compliant: Overlap={overlap:.2f}")
    return True, details


class ReferenceValidatorAgent:
    """
    Agent that validates contributions before they are accepted into the benchmark.
    Acts as a blocking gate for Constitution II compliance.
    """

    def __init__(self, target_paper_title: str):
        """
        Initialize the validator with the target paper title.

        Args:
            target_paper_title: The title of the paper this benchmark is based on.
        """
        self.target_paper_title = target_paper_title
        self.validation_log: List[Dict[str, Any]] = []

    def validate_contribution(self, contribution_text: str) -> bool:
        """
        Validate a contribution (review, result, analysis) against Constitution II.

        Args:
            contribution_text: The text of the contribution to validate.

        Returns:
            bool: True if compliant and can contribute points, False if blocked.
        """
        is_valid, details = validate_constitution_ii(
            proposed_review=contribution_text,
            target_paper_title=self.target_paper_title
        )

        log_entry = {
            "text_snippet": contribution_text[:100] + "..." if len(contribution_text) > 100 else contribution_text,
            "is_valid": is_valid,
            "details": details
        }
        self.validation_log.append(log_entry)

        if not is_valid:
            logger.error(f"Contribution blocked: {details['blocked_reason']}")
        else:
            logger.info("Contribution accepted.")

        return is_valid

    def get_validation_log(self) -> List[Dict[str, Any]]:
        """Return the history of validations."""
        return self.validation_log


def main():
    """
    CLI entry point for testing the Reference Validator.
    """
    import sys

    # Default target paper from the project context
    target_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"

    # Test cases
    test_cases = [
        ("This review analyzes the heterogeneous foundation model collaboration benchmark results.", True),
        ("Simulated results show 99% accuracy on random data.", False),
        ("The model architecture for the tabular data processing is described in section 3.", True),
        ("Fake data was generated to prove the point.", False),
    ]

    validator = ReferenceValidatorAgent(target_paper_title=target_title)

    print(f"Target Paper: {target_title}")
    print("-" * 50)

    for text, expected in test_cases:
        result = validator.validate_contribution(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] Input: '{text[:40]}...' -> Valid: {result}")

    print("-" * 50)
    print(f"Total validations: {len(validator.get_validation_log())}")

    return 0


if __name__ == "__main__":
    sys.exit(main())