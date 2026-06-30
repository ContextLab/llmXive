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

# Configuration constants
MIN_TITLE_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_REQUIRED_SECTIONS = [
    "abstract",
    "introduction",
    "methodology",
    "results",
    "discussion",
    "conclusion",
    "references"
]

logger = get_logger(__name__)


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title string into a list of lowercase words.

    Args:
        title: The title string to tokenize.

    Returns:
        List of lowercase word tokens.
    """
    if not title:
        return []
    # Convert to lowercase and split on non-alphanumeric characters
    tokens = re.findall(r'\b\w+\b', title.lower())
    return tokens


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Formula: |A ∩ B| / |A ∪ B|

    Args:
        title_a: First title string.
        title_b: Second title string.

    Returns:
        Float between 0.0 and 1.0 representing overlap ratio.
    """
    tokens_a = set(tokenize_title(title_a))
    tokens_b = set(tokenize_title(title_b))

    if not tokens_a and not tokens_b:
        return 0.0
    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    return len(intersection) / len(union)


def validate_reference_title_overlap(
    candidate_title: str,
    reference_titles: List[str],
    threshold: float = MIN_TITLE_OVERLAP_THRESHOLD
) -> Tuple[bool, float, Optional[str]]:
    """
    Validate that a candidate title does not have excessive overlap
    with any reference title (indicating potential plagiarism or
    insufficient novelty).

    Args:
        candidate_title: The title being validated.
        reference_titles: List of existing reference titles to compare against.
        threshold: Minimum overlap ratio that triggers a block (default 0.7).

    Returns:
        Tuple of (is_valid, max_overlap, blocking_reference_title).
        is_valid is True if max_overlap < threshold.
    """
    if not reference_titles:
        logger.info("No reference titles provided; skipping overlap check.")
        return True, 0.0, None

    max_overlap = 0.0
    blocking_title = None

    for ref_title in reference_titles:
        overlap = compute_title_token_overlap(candidate_title, ref_title)
        if overlap > max_overlap:
            max_overlap = overlap
            blocking_title = ref_title

    is_valid = max_overlap < threshold

    if not is_valid:
        logger.warning(
            f"Title overlap check FAILED: '{candidate_title}' has {max_overlap:.2f} "
            f"overlap with '{blocking_title}' (threshold: {threshold})"
        )
    else:
        logger.debug(
            f"Title overlap check PASSED: max overlap {max_overlap:.2f} < {threshold}"
        )

    return is_valid, max_overlap, blocking_title


def check_constitution_ii_compliance(doc_metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if a document meets Constitution II compliance requirements.

    Constitution II requires:
    1. Presence of all standard sections (abstract, introduction, etc.)
    2. Explicit citation of at least 3 prior works in references
    3. Clear statement of contribution in introduction or abstract

    Args:
        doc_metadata: Dictionary containing document metadata including:
            - sections: List of section names present in the document
            - references_count: Number of references cited
            - has_contribution_statement: Boolean indicating if contribution is stated

    Returns:
        Tuple of (is_compliant, list_of_violations).
    """
    violations = []

    # Check 1: Required sections
    present_sections = set(doc_metadata.get("sections", []))
    missing_sections = [
        section for section in CONSTITUTION_II_REQUIRED_SECTIONS
        if section not in present_sections
    ]
    if missing_sections:
        violations.append(
            f"Missing required sections: {', '.join(missing_sections)}"
        )

    # Check 2: Minimum references
    references_count = doc_metadata.get("references_count", 0)
    if references_count < 3:
        violations.append(
            f"Insufficient references: {references_count} < 3 required"
        )

    # Check 3: Contribution statement
    if not doc_metadata.get("has_contribution_statement", False):
        violations.append("Missing explicit contribution statement")

    is_compliant = len(violations) == 0

    if not is_compliant:
        logger.warning(
            f"Constitution II compliance FAILED: {len(violations)} violations"
        )
        for v in violations:
            logger.warning(f"  - {v}")
    else:
        logger.info("Constitution II compliance PASSED")

    return is_compliant, violations


class ReferenceValidatorAgent:
    """
    Agent that validates research contributions before they are
    added to the review pool.

    Implements blocking gates for:
    1. Title novelty (token overlap < 0.7 with existing works)
    2. Constitution II compliance (structural and citation requirements)
    """

    def __init__(
        self,
        existing_titles: List[str],
        constitution_ii_enabled: bool = True
    ):
        """
        Initialize the validator agent.

        Args:
            existing_titles: List of titles from existing references to check against.
            constitution_ii_enabled: Whether to enforce Constitution II checks.
        """
        self.existing_titles = existing_titles
        self.constitution_ii_enabled = constitution_ii_enabled
        self.validation_log: List[Dict[str, Any]] = []

    def validate_contribution(
        self,
        candidate_title: str,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform full validation of a research contribution.

        Args:
            candidate_title: The title of the contribution to validate.
            doc_metadata: Optional metadata for Constitution II checks.

        Returns:
            Dictionary with validation results:
            {
                "approved": bool,
                "title_overlap_valid": bool,
                "title_max_overlap": float,
                "title_blocking_title": str | None,
                "constitution_ii_valid": bool | None,
                "constitution_ii_violations": list | None,
                "log_entry": dict
            }
        """
        result = {
            "approved": False,
            "title_overlap_valid": False,
            "title_max_overlap": 0.0,
            "title_blocking_title": None,
            "constitution_ii_valid": None,
            "constitution_ii_violations": None,
            "log_entry": {}
        }

        # Gate 1: Title Overlap Check
        title_valid, max_overlap, blocking_title = validate_reference_title_overlap(
            candidate_title,
            self.existing_titles
        )

        result["title_overlap_valid"] = title_valid
        result["title_max_overlap"] = max_overlap
        result["title_blocking_title"] = blocking_title

        if not title_valid:
            result["log_entry"] = {
                "status": "REJECTED",
                "reason": "TITLE_OVERLAP",
                "details": f"Overlap {max_overlap:.2f} >= 0.7 with '{blocking_title}'"
            }
            self.validation_log.append(result["log_entry"])
            logger.warning(f"Contribution REJECTED: {result['log_entry']['details']}")
            return result

        # Gate 2: Constitution II Check (if enabled)
        if self.constitution_ii_enabled:
            if doc_metadata is None:
                result["log_entry"] = {
                    "status": "REJECTED",
                    "reason": "MISSING_METADATA",
                    "details": "Constitution II check requires document metadata"
                }
                self.validation_log.append(result["log_entry"])
                logger.error("Contribution REJECTED: Missing metadata for Constitution II check")
                return result

            const_valid, violations = check_constitution_ii_compliance(doc_metadata)
            result["constitution_ii_valid"] = const_valid
            result["constitution_ii_violations"] = violations

            if not const_valid:
                result["log_entry"] = {
                    "status": "REJECTED",
                    "reason": "CONSTITUTION_II_FAILURE",
                    "details": violations
                }
                self.validation_log.append(result["log_entry"])
                logger.warning(f"Contribution REJECTED: Constitution II failures - {violations}")
                return result

        # All checks passed
        result["approved"] = True
        result["log_entry"] = {
            "status": "APPROVED",
            "reason": "ALL_GATES_PASSED",
            "details": "Contribution meets all validation criteria"
        }
        self.validation_log.append(result["log_entry"])
        logger.info(f"Contribution APPROVED: '{candidate_title}'")

        return result

    def get_validation_log(self) -> List[Dict[str, Any]]:
        """Return the history of all validation attempts."""
        return self.validation_log


def main():
    """
    CLI entry point for manual testing of the ReferenceValidatorAgent.
    """
    # Demo: validate a sample title against existing references
    existing = [
        "A Deep Learning Approach to Time Series Forecasting",
        "Tabular Data Processing with Transformer Models",
        "Natural Language Understanding via Distilled LLMs"
    ]

    agent = ReferenceValidatorAgent(existing_titles=existing)

    # Test case 1: High overlap (should fail)
    print("Test 1: High overlap title")
    result1 = agent.validate_contribution(
        "A Deep Learning Approach to Time Series Prediction",
        {
            "sections": ["abstract", "introduction", "methodology", "results", "discussion", "conclusion", "references"],
            "references_count": 5,
            "has_contribution_statement": True
        }
    )
    print(f"  Approved: {result1['approved']}")
    print(f"  Reason: {result1['log_entry']['details']}")

    # Test case 2: Novel title, valid metadata (should pass)
    print("\nTest 2: Novel title with valid metadata")
    result2 = agent.validate_contribution(
        "Heterogeneous Foundation Model Collaboration Benchmarks",
        {
            "sections": ["abstract", "introduction", "methodology", "results", "discussion", "conclusion", "references"],
            "references_count": 10,
            "has_contribution_statement": True
        }
    )
    print(f"  Approved: {result2['approved']}")
    print(f"  Reason: {result2['log_entry']['details']}")

    # Test case 3: Novel title, missing contribution statement (should fail Constitution II)
    print("\nTest 3: Novel title but missing contribution statement")
    result3 = agent.validate_contribution(
        "New Methods for Multi-Modal Learning",
        {
            "sections": ["abstract", "introduction", "methodology", "results", "discussion", "conclusion", "references"],
            "references_count": 5,
            "has_contribution_statement": False
        }
    )
    print(f"  Approved: {result3['approved']}")
    print(f"  Reason: {result3['log_entry']['details']}")


if __name__ == "__main__":
    main()