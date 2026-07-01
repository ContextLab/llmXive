"""
Reference Validator Agent for llmXive.

Implements:
1. Title-token-overlap check (≥ 0.7 threshold) before contributing review points.
2. Blocking gate for Constitution II compliance.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

# Threshold for title-token overlap
TITLE_TOKEN_OVERLAP_THRESHOLD = 0.7

# Constitution II Requirements (simplified for validation)
# Based on plan.md context: Constitution II ensures alignment with research goals
# and prevents fabrication.
CONSTITUTION_II_REQUIREMENTS = [
    "no_fabrication",
    "real_data_usage",
    "statistical_validity",
    "transparency"
]

logger = get_logger(__name__)


def tokenize_text(text: str) -> List[str]:
    """
    Tokenize text into lowercase alphanumeric tokens.

    Args:
        text: Input string to tokenize.

    Returns:
        List of lowercase alphanumeric tokens.
    """
    if not text:
        return []
    # Convert to lowercase and extract alphanumeric sequences
    tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
    return tokens


def compute_title_token_overlap(title1: str, title2: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Formula: |Tokens(T1) ∩ Tokens(T2)| / |Tokens(T1) ∪ Tokens(T2)|

    Args:
        title1: First title string.
        title2: Second title string.

    Returns:
        Float between 0.0 and 1.0 representing overlap score.
    """
    tokens1 = set(tokenize_text(title1))
    tokens2 = set(tokenize_text(title2))

    if not tokens1 and not tokens2:
        return 0.0
    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)

    return len(intersection) / len(union)


def validate_constitution_ii(
    review_data: Dict[str, Any],
    reference_plan: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that review data complies with Constitution II requirements.

    Checks:
    1. no_fabrication: Results must be marked as measured, not simulated/fake.
    2. real_data_usage: Must reference real data sources.
    3. statistical_validity: Must include statistical metrics if applicable.
    4. transparency: Must log methodology and parameters.

    Args:
        review_data: Dictionary containing review results and metadata.
        reference_plan: Optional reference to plan.md requirements.

    Returns:
        Tuple of (is_compliant, list_of_violations).
    """
    violations = []

    # Check for fabrication flags
    if "metrics" in review_data:
        for metric_name, metric_value in review_data["metrics"].items():
            if isinstance(metric_value, dict):
                if metric_value.get("fabricated", False):
                    violations.append(f"Fabricated metric detected: {metric_name}")
                if metric_value.get("simulated", False):
                    violations.append(f"Simulated metric detected: {metric_name}")
            elif isinstance(metric_value, str):
                lower_val = metric_value.lower()
                if "fabricated" in lower_val or "simulated" in lower_val or "fake" in lower_val:
                    violations.append(f"Fabricated result string detected in {metric_name}")

    # Check for real data usage
    if "data_sources" not in review_data or not review_data["data_sources"]:
        violations.append("No data sources specified (Constitution II: real_data_usage)")
    else:
        for source in review_data["data_sources"]:
            if source.get("type") == "synthetic" and not source.get("labelled_as_synthetic"):
                violations.append(f"Unlabelled synthetic data source: {source.get('name')}")

    # Check for statistical validity if metrics are present
    if "metrics" in review_data and review_data["metrics"]:
        # If statistical tests are claimed, check for required fields
        if "statistical_tests" in review_data:
            required_fields = ["test_name", "p_value", "effect_size"]
            for test in review_data["statistical_tests"]:
                for field in required_fields:
                    if field not in test:
                        violations.append(f"Missing statistical field '{field}' in test {test.get('test_name', 'unknown')}")

    # Check transparency (logging)
    if "methodology" not in review_data:
        violations.append("Missing methodology documentation (Constitution II: transparency)")

    is_compliant = len(violations) == 0
    return is_compliant, violations


class ReferenceValidatorAgent:
    """
    Agent that validates research contributions against reference criteria.

    Features:
    - Title-token-overlap check (≥ 0.7) before contributing review points.
    - Blocking gate for Constitution II compliance.
    """

    def __init__(self, reference_title: str, plan_path: Optional[Path] = None):
        """
        Initialize the validator with a reference title.

        Args:
            reference_title: The target reference title to compare against.
            plan_path: Optional path to the plan.md file for Constitution checks.
        """
        self.reference_title = reference_title
        self.plan_path = plan_path
        self.logger = get_logger(__name__)

        if self.plan_path and not self.plan_path.exists():
            self.logger.warning(f"Plan path not found: {self.plan_path}")
            self.plan_path = None

    def validate_contribution(
        self,
        contribution_title: str,
        review_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a research contribution.

        Performs two checks:
        1. Title-token-overlap ≥ 0.7 with reference title.
        2. Constitution II compliance.

        Args:
            contribution_title: Title of the contribution being validated.
            review_data: Data to validate for Constitution II.

        Returns:
            Dictionary with validation results:
            - passed: bool
            - title_overlap_score: float
            - constitution_compliant: bool
            - violations: list of strings
            - review_points: int (0 if failed, 1 if passed)
        """
        result = {
            "passed": False,
            "title_overlap_score": 0.0,
            "constitution_compliant": False,
            "violations": [],
            "review_points": 0,
            "blocked_reason": None
        }

        # Check 1: Title-token-overlap
        overlap_score = compute_title_token_overlap(self.reference_title, contribution_title)
        result["title_overlap_score"] = overlap_score

        if overlap_score < TITLE_TOKEN_OVERLAP_THRESHOLD:
            result["blocked_reason"] = (
                f"Title overlap {overlap_score:.2f} < threshold {TITLE_TOKEN_OVERLAP_THRESHOLD}"
            )
            self.logger.warning(f"Title overlap check failed: {result['blocked_reason']}")
            return result

        # Check 2: Constitution II compliance
        is_compliant, violations = validate_constitution_ii(review_data)
        result["constitution_compliant"] = is_compliant
        result["violations"] = violations

        if not is_compliant:
            result["blocked_reason"] = "Constitution II compliance failed"
            self.logger.warning(f"Constitution II check failed: {violations}")
            return result

        # Both checks passed
        result["passed"] = True
        result["review_points"] = 1
        self.logger.info(f"Contribution validated successfully. Overlap: {overlap_score:.2f}")

        return result

    def get_review_points(
        self,
        contribution_title: str,
        review_data: Dict[str, Any]
    ) -> int:
        """
        Get review points for a contribution (0 if blocked, 1 if passed).

        This is a convenience method that runs full validation and returns points.

        Args:
            contribution_title: Title of the contribution.
            review_data: Data to validate.

        Returns:
            Integer review points (0 or 1).
        """
        validation_result = self.validate_contribution(contribution_title, review_data)
        return validation_result["review_points"]


def main():
    """
    Main entry point for testing the ReferenceValidatorAgent.
    Demonstrates title-token-overlap and Constitution II checks.
    """
    import sys
    import json

    # Example reference title (from the paper)
    reference_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"

    # Create validator
    validator = ReferenceValidatorAgent(reference_title)

    # Test Case 1: High overlap, compliant
    contribution_1 = {
        "title": "Benchmark for Heterogeneous Scientific Foundation Models",
        "data": {
            "metrics": {
                "accuracy": {"value": 0.85, "fabricated": False},
                "f1_score": {"value": 0.82, "fabricated": False}
            },
            "data_sources": [
                {"name": "UCI_HAR", "type": "real", "url": "https://archive.ics.uci.edu/"}
            ],
            "statistical_tests": [
                {"test_name": "paired_ttest", "p_value": 0.03, "effect_size": 0.5}
            ],
            "methodology": "Standard benchmark protocol with 5 seeds"
        }
    }

    result_1 = validator.validate_contribution(
        contribution_1["title"],
        contribution_1["data"]
    )

    print("Test Case 1 (High Overlap, Compliant):")
    print(json.dumps(result_1, indent=2))
    print()

    # Test Case 2: Low overlap
    contribution_2 = {
        "title": "Random Image Classification Study",
        "data": {
            "metrics": {"accuracy": 0.5},
            "data_sources": [{"name": "COCO", "type": "real"}],
            "methodology": "Simple test"
        }
    }

    result_2 = validator.validate_contribution(
        contribution_2["title"],
        contribution_2["data"]
    )

    print("Test Case 2 (Low Overlap):")
    print(json.dumps(result_2, indent=2))
    print()

    # Test Case 3: High overlap, but fabrication detected
    contribution_3 = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "data": {
            "metrics": {
                "accuracy": {"value": 0.99, "fabricated": True}
            },
            "data_sources": [],
            "methodology": "Simulated results"
        }
    }

    result_3 = validator.validate_contribution(
        contribution_3["title"],
        contribution_3["data"]
    )

    print("Test Case 3 (Fabrication Detected):")
    print(json.dumps(result_3, indent=2))

    # Exit with code based on test case 1 success
    sys.exit(0 if result_1["passed"] else 1)


if __name__ == "__main__":
    main()
