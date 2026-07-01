"""
Reference Validator Agent for llmXive.

Implements a blocking gate for Constitution II compliance and
a title-token-overlap check before contributing review points.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Threshold for title-token-overlap (Constitution II Gate)
TITLE_TOKEN_OVERLAP_THRESHOLD = 0.7

# Constitution II Compliance Rules (simplified for gate logic)
# In a full implementation, these would be loaded from a spec file
CONSTITUTION_II_RULES = [
    "Must cite original paper",
    "Must verify dataset source",
    "Must not fabricate results",
    "Must report real measurements"
]

class ReferenceValidatorAgent:
    """
    Agent that validates references and research contributions.

    Attributes:
        title_token_overlap_threshold (float): Minimum overlap required.
        constitution_ii_rules (List[str]): List of compliance rules.
    """

    def __init__(self, threshold: Optional[float] = None):
        """
        Initialize the ReferenceValidatorAgent.

        Args:
            threshold: Optional override for the title-token-overlap threshold.
        """
        self.title_token_overlap_threshold = (
            threshold if threshold is not None else TITLE_TOKEN_OVERLAP_THRESHOLD
        )
        self.constitution_ii_rules = CONSTITUTION_II_RULES
        logger.info(
            "ReferenceValidatorAgent initialized with threshold: %s",
            self.title_token_overlap_threshold
        )

    def _tokenize_title(self, title: str) -> Set[str]:
        """
        Tokenize a title into a set of lowercase alphanumeric tokens.

        Args:
            title: The title string to tokenize.

        Returns:
            A set of unique tokens.
        """
        if not title:
            return set()
        # Convert to lowercase and extract alphanumeric words
        tokens = re.findall(r'\b[a-z0-9]+\b', title.lower())
        return set(tokens)

    def compute_token_overlap(self, title_a: str, title_b: str) -> float:
        """
        Compute the Jaccard similarity (token overlap) between two titles.

        Formula: |A ∩ B| / |A ∪ B|

        Args:
            title_a: First title string.
            title_b: Second title string.

        Returns:
            Float between 0.0 and 1.0 representing overlap.
        """
        tokens_a = self._tokenize_title(title_a)
        tokens_b = self._tokenize_title(title_b)

        if not tokens_a and not tokens_b:
            return 1.0 if title_a == title_b else 0.0

        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def check_title_token_overlap(
        self,
        candidate_title: str,
        reference_title: str
    ) -> Tuple[bool, float]:
        """
        Check if the candidate title meets the overlap threshold against a reference.

        Args:
            candidate_title: The title of the new contribution.
            reference_title: The title of the reference paper.

        Returns:
            Tuple of (passes_check, overlap_score).
        """
        overlap = self.compute_token_overlap(candidate_title, reference_title)
        passes = overlap >= self.title_token_overlap_threshold
        
        logger.debug(
            "Token overlap check: candidate='%s', reference='%s', overlap=%.2f, passes=%s",
            candidate_title, reference_title, overlap, passes
        )
        
        return passes, overlap

    def validate_constitution_ii_compliance(
        self,
        contribution: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a contribution meets Constitution II requirements.

        Args:
            contribution: Dictionary containing contribution details.
                         Expected keys: 'title', 'citations', 'data_sources', 'results_type'.

        Returns:
            Tuple of (is_compliant, list_of_violations).
        """
        violations = []

        # 1. Check for title-token-overlap if a reference is provided
        if "reference_title" in contribution:
            passes, score = self.check_title_token_overlap(
                contribution.get("title", ""),
                contribution.get("reference_title", "")
            )
            if not passes:
                violations.append(
                    f"Title-token-overlap ({score:.2f}) below threshold "
                    f"({self.title_token_overlap_threshold}) against reference."
                )

        # 2. Check for required citations (Rule: Must cite original paper)
        if "citations" not in contribution or not contribution["citations"]:
            violations.append("Constitution II Violation: No citations provided.")

        # 3. Check for data source verification (Rule: Must verify dataset source)
        if "data_sources" not in contribution or not contribution["data_sources"]:
            violations.append("Constitution II Violation: No data sources verified.")

        # 4. Check for real results (Rule: Must not fabricate results)
        results_type = contribution.get("results_type", "").lower()
        if results_type in ["fabricated", "simulated", "placeholder", "random"]:
            violations.append(
                "Constitution II Violation: Results are fabricated or simulated. "
                "Must report real measurements."
            )

        is_compliant = len(violations) == 0
        return is_compliant, violations

    def validate_contribution(
        self,
        contribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform full validation of a research contribution.

        This is the main entry point for the blocking gate.

        Args:
            contribution: The contribution dictionary to validate.

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "overlap_score": float (if applicable),
                "violations": List[str],
                "can_contribute_points": bool
            }
        """
        logger.info("Validating contribution: %s", contribution.get("title", "Untitled"))

        # Check Constitution II compliance
        is_compliant, violations = self.validate_constitution_ii_compliance(contribution)

        # Calculate overlap score if a reference exists
        overlap_score = None
        if "reference_title" in contribution:
            _, overlap_score = self.check_title_token_overlap(
                contribution.get("title", ""),
                contribution.get("reference_title", "")
            )

        # Determine if points can be contributed
        # Blocking gate: Points only if compliant AND (no reference OR overlap met)
        can_contribute = is_compliant and (
            overlap_score is None or overlap_score >= self.title_token_overlap_threshold
        )

        result = {
            "is_valid": is_compliant,
            "overlap_score": overlap_score,
            "violations": violations,
            "can_contribute_points": can_contribute
        }

        if can_contribute:
            logger.info("Contribution validated. Points can be contributed.")
        else:
            logger.warning(
                "Contribution blocked. Violations: %s, Can contribute: %s",
                violations, can_contribute
            )

        return result

def main():
    """
    Main entry point for standalone testing of the ReferenceValidatorAgent.
    """
    agent = ReferenceValidatorAgent()

    # Test Case 1: High overlap, compliant
    contribution_1 = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Foundation Model Benchmark for Science",
        "citations": ["paper123"],
        "data_sources": ["UCI_HAR", "HuggingFace"],
        "results_type": "real_measurement"
    }
    result_1 = agent.validate_contribution(contribution_1)
    print(f"Test 1 (Compliant, High Overlap): {result_1}")

    # Test Case 2: Low overlap (Blocking Gate)
    contribution_2 = {
        "title": "Random Data Generation Script",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "citations": ["paper123"],
        "data_sources": ["UCI_HAR"],
        "results_type": "real_measurement"
    }
    result_2 = agent.validate_contribution(contribution_2)
    print(f"Test 2 (Low Overlap): {result_2}")

    # Test Case 3: Fabricated results (Blocking Gate)
    contribution_3 = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "citations": ["paper123"],
        "data_sources": ["UCI_HAR"],
        "results_type": "fabricated"
    }
    result_3 = agent.validate_contribution(contribution_3)
    print(f"Test 3 (Fabricated Results): {result_3}")

    # Test Case 4: Missing citations (Blocking Gate)
    contribution_4 = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "citations": [],
        "data_sources": ["UCI_HAR"],
        "results_type": "real_measurement"
    }
    result_4 = agent.validate_contribution(contribution_4)
    print(f"Test 4 (Missing Citations): {result_4}")

if __name__ == "__main__":
    main()
