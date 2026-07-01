"""
Reference Validator Agent for llmXive.

This module implements a validation agent that checks incoming research
contributions against a set of reference criteria before allowing them
to contribute review points.

Key Features:
1. Title-Token-Overlap Check: Ensures the contribution title shares
   at least 70% token overlap with the reference title.
2. Constitution II Compliance Gate: Blocks contributions that violate
   specific constitutional rules (e.g., missing required fields,
   unauthorized data sources).
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

# Constants
MIN_TITLE_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_REQUIRED_FIELDS = {
    "title",
    "abstract",
    "methodology",
    "results",
    "conclusion",
    "references"
}

logger = get_logger(__name__)


class ReferenceValidatorAgent:
    """
    An agent that validates research contributions against reference standards.

    Attributes:
        reference_title (str): The canonical title to compare against.
        reference_abstract (str): The canonical abstract for context.
        constitution_ii_rules (Dict): Configuration for Constitution II compliance.
    """

    def __init__(
        self,
        reference_title: str,
        reference_abstract: Optional[str] = None,
        constitution_ii_rules: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the validator with reference materials.

        Args:
            reference_title: The authoritative title for overlap comparison.
            reference_abstract: Optional abstract for context matching.
            constitution_ii_rules: Optional dict of specific rules to enforce.
        """
        self.reference_title = reference_title
        self.reference_abstract = reference_abstract or ""
        self.constitution_ii_rules = constitution_ii_rules or {}
        self._token_cache: Set[str] = set()

        logger.info(f"ReferenceValidatorAgent initialized with title: '{reference_title}'")

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into a list of normalized tokens.

        Args:
            text: Input string to tokenize.

        Returns:
            List of lowercased, alphanumeric tokens.
        """
        if not text:
            return []
        # Normalize: lowercase, keep alphanumeric and spaces, split
        normalized = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
        tokens = [t for t in normalized.split() if len(t) > 1] # Filter very short tokens
        return tokens

    def calculate_title_token_overlap(
        self,
        candidate_title: str,
        reference_title: Optional[str] = None
    ) -> Tuple[float, Set[str], Set[str]]:
        """
        Calculate the Jaccard similarity (token overlap) between two titles.

        Formula: |A ∩ B| / |A ∪ B|

        Args:
            candidate_title: The title to validate.
            reference_title: Optional override for the reference title.

        Returns:
            Tuple of (overlap_score, candidate_tokens, reference_tokens)
        """
        ref_title = reference_title or self.reference_title
        candidate_tokens = set(self._tokenize(candidate_title))
        reference_tokens = set(self._tokenize(ref_title))

        if not candidate_tokens or not reference_tokens:
            return 0.0, candidate_tokens, reference_tokens

        intersection = candidate_tokens & reference_tokens
        union = candidate_tokens | reference_tokens

        overlap = len(intersection) / len(union)
        return overlap, candidate_tokens, reference_tokens

    def validate_title_overlap(
        self,
        candidate_title: str,
        threshold: float = MIN_TITLE_OVERLAP_THRESHOLD
    ) -> bool:
        """
        Validate that the candidate title meets the token overlap threshold.

        Args:
            candidate_title: Title to check.
            threshold: Minimum required overlap ratio (default 0.7).

        Returns:
            True if overlap >= threshold, False otherwise.
        """
        overlap, _, _ = self.calculate_title_token_overlap(candidate_title)
        logger.debug(f"Title overlap check: '{candidate_title}' -> {overlap:.2f} (threshold: {threshold})")
        return overlap >= threshold

    def validate_constitution_ii_compliance(
        self,
        contribution: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a contribution against Constitution II rules.

        Checks:
        1. Presence of all required fields (title, abstract, etc.).
        2. Absence of prohibited keywords (if configured in rules).
        3. Data source verification (if configured).

        Args:
            contribution: Dict containing the research contribution data.

        Returns:
            Tuple of (is_compliant, list_of_violations)
        """
        violations = []

        # 1. Check Required Fields
        missing_fields = CONSTITUTION_II_REQUIRED_FIELDS - set(contribution.keys())
        if missing_fields:
            violations.append(f"Missing required fields: {', '.join(missing_fields)}")

        # 2. Check Prohibited Keywords (from rules)
        prohibited = self.constitution_ii_rules.get("prohibited_keywords", [])
        if prohibited:
            content_text = " ".join(str(v) for v in contribution.values()).lower()
            found_prohibited = [k for k in prohibited if k.lower() in content_text]
            if found_prohibited:
                violations.append(f"Contains prohibited keywords: {', '.join(found_prohibited)}")

        # 3. Check Data Source Whitelist (from rules)
        allowed_sources = self.constitution_ii_rules.get("allowed_data_sources", [])
        if allowed_sources:
            # Assume 'data_sources' key exists if provided in contribution
            sources = contribution.get("data_sources", [])
            if isinstance(sources, str):
                sources = [sources]
            invalid_sources = [s for s in sources if s not in allowed_sources]
            if invalid_sources:
                violations.append(f"Unauthorized data sources: {', '.join(invalid_sources)}")

        is_compliant = len(violations) == 0
        if not is_compliant:
            logger.warning(f"Constitution II violation detected: {violations}")
        else:
            logger.info("Constitution II compliance check passed.")

        return is_compliant, violations

    def validate_contribution(
        self,
        contribution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform a full validation of a research contribution.

        This is the main entry point for the agent. It checks:
        1. Title Token Overlap (blocking if < 0.7)
        2. Constitution II Compliance (blocking if false)

        Args:
            contribution: The full contribution dictionary.

        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "title_overlap_score": float,
                "title_overlap_passed": bool,
                "constitution_ii_compliant": bool,
                "violations": List[str],
                "can_contribute_points": bool
            }
        """
        candidate_title = contribution.get("title", "")
        if not candidate_title:
            return {
                "valid": False,
                "title_overlap_score": 0.0,
                "title_overlap_passed": False,
                "constitution_ii_compliant": False,
                "violations": ["Missing title"],
                "can_contribute_points": False
            }

        # Check 1: Title Overlap
        overlap_score, _, _ = self.calculate_title_token_overlap(candidate_title)
        title_passed = overlap_score >= MIN_TITLE_OVERLAP_THRESHOLD

        # Check 2: Constitution II
        const_passed, const_violations = self.validate_constitution_ii_compliance(contribution)

        # Aggregate Results
        is_valid = title_passed and const_passed
        all_violations = []
        if not title_passed:
            all_violations.append(
                f"Title token overlap ({overlap_score:.2f}) is below threshold ({MIN_TITLE_OVERLAP_THRESHOLD})"
            )
        all_violations.extend(const_violations)

        return {
            "valid": is_valid,
            "title_overlap_score": overlap_score,
            "title_overlap_passed": title_passed,
            "constitution_ii_compliant": const_passed,
            "violations": all_violations,
            "can_contribute_points": is_valid
        }


def main():
    """
    CLI entry point for testing the ReferenceValidatorAgent.
    Runs a simple self-test with mock data.
    """
    print("Running ReferenceValidatorAgent Self-Test...")

    # Mock Reference
    ref_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"
    validator = ReferenceValidatorAgent(
        reference_title=ref_title,
        constitution_ii_rules={
            "prohibited_keywords": ["fake", "fabricated", "simulated"],
            "allowed_data_sources": ["UCI_HAR", "DROP", "MUST", "HuggingFace"]
        }
    )

    # Test Case 1: Valid Contribution
    valid_contrib = {
        "title": "Heterogeneous Scientific Foundation Model Benchmarking",
        "abstract": "A study on heterogeneous models.",
        "methodology": "We used standard benchmarks.",
        "results": "Accuracy improved by 5%.",
        "conclusion": "The approach works.",
        "references": ["Ref1"],
        "data_sources": ["UCI_HAR"]
    }

    result1 = validator.validate_contribution(valid_contrib)
    print(f"\nTest 1 (Valid): {result1['valid']}")
    print(f"  Overlap: {result1['title_overlap_score']:.2f}")
    print(f"  Violations: {result1['violations']}")
    assert result1['valid'], "Valid contribution should pass."

    # Test Case 2: Low Overlap Title
    bad_title_contrib = {
        "title": "Completely Unrelated Topic About Cats",
        "abstract": "Cats are great.",
        "methodology": "We observed cats.",
        "results": "Cats sleep a lot.",
        "conclusion": "Cats are good.",
        "references": [],
        "data_sources": ["UCI_HAR"]
    }

    result2 = validator.validate_contribution(bad_title_contrib)
    print(f"\nTest 2 (Low Overlap): {result2['valid']}")
    print(f"  Overlap: {result2['title_overlap_score']:.2f}")
    print(f"  Violations: {result2['violations']}")
    assert not result2['valid'], "Low overlap title should fail."
    assert not result2['title_overlap_passed'], "Title check should fail."

    # Test Case 3: Constitution II Violation (Missing Field)
    missing_field_contrib = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration",
        "abstract": "Brief abstract.",
        # Missing methodology, results, etc.
        "data_sources": ["UCI_HAR"]
    }

    result3 = validator.validate_contribution(missing_field_contrib)
    print(f"\nTest 3 (Missing Fields): {result3['valid']}")
    print(f"  Violations: {result3['violations']}")
    assert not result3['valid'], "Missing fields should fail."
    assert not result3['constitution_ii_compliant'], "Constitution II check should fail."

    # Test Case 4: Prohibited Keyword
    bad_keyword_contrib = {
        "title": "Heterogeneous Scientific Foundation Model Collaboration",
        "abstract": "This study is fabricated.",
        "methodology": "We simulated results.",
        "results": "Fake data used.",
        "conclusion": "Simulated outcome.",
        "references": [],
        "data_sources": ["UCI_HAR"]
    }

    result4 = validator.validate_contribution(bad_keyword_contrib)
    print(f"\nTest 4 (Prohibited Keyword): {result4['valid']}")
    print(f"  Violations: {result4['violations']}")
    assert not result4['valid'], "Prohibited keyword should fail."
    assert not result4['constitution_ii_compliant'], "Constitution II check should fail."

    print("\n✅ All self-tests passed.")


if __name__ == "__main__":
    main()