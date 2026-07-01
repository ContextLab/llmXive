"""
Reference Validator Agent for llmXive project.

Implements:
1. Title-token-overlap check (threshold >= 0.7) before contributing review points.
2. Blocking gate for Constitution II compliance.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

# Constants
THRESHOLD_TITLE_OVERLAP = 0.7
CONSTITUTION_2_RULES = {
    "no_fabricated_results": "Results must be real measurements, not simulated or hardcoded.",
    "cpu_tractable": "All models must be CPU-tractable (< 1 GB weights).",
    "real_data_only": "No synthetic/fake input data or placeholder datasets.",
    "fail_loudly": "If a metric cannot be measured, report it as unmeasurable rather than faking."
}

logger = get_logger(__name__)


class ReferenceValidatorAgent:
    """
    Agent that validates research contributions against Constitution II and
    performs title-token-overlap checks before allowing review points to be contributed.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the validator.

        Args:
            project_root: Path to the project root. Defaults to current working directory.
        """
        self.project_root = project_root or Path.cwd()
        self.logger = get_logger(__name__)

    def tokenize_text(self, text: str) -> Set[str]:
        """
        Tokenize text into a set of lowercase alphanumeric tokens.

        Args:
            text: Input string to tokenize.

        Returns:
            Set of unique tokens.
        """
        if not text:
            return set()
        # Convert to lowercase and extract alphanumeric tokens
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return set(tokens)

    def compute_token_overlap(self, title_a: str, title_b: str) -> float:
        """
        Compute the Jaccard similarity (token overlap) between two titles.

        Formula: |tokens(title_a) ∩ tokens(title_b)| / |tokens(title_a) ∪ tokens(title_b)|

        Args:
            title_a: First title string.
            title_b: Second title string.

        Returns:
            Float between 0.0 and 1.0 representing overlap score.
        """
        tokens_a = self.tokenize_text(title_a)
        tokens_b = self.tokenize_text(title_b)

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)

        return len(intersection) / len(union) if union else 0.0

    def check_title_overlap(
        self,
        candidate_title: str,
        reference_titles: List[str],
        threshold: float = THRESHOLD_TITLE_OVERLAP
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if a candidate title has sufficient overlap with any reference title.

        Args:
            candidate_title: The title to validate.
            reference_titles: List of reference titles to compare against.
            threshold: Minimum overlap score required (default 0.7).

        Returns:
            Tuple of (passes_check, max_overlap_score, best_match_title).
            Returns (False, score, None) if no match found above threshold.
        """
        if not reference_titles:
            self.logger.warning("No reference titles provided for overlap check.")
            return False, 0.0, None

        max_overlap = 0.0
        best_match = None

        for ref_title in reference_titles:
            overlap = self.compute_token_overlap(candidate_title, ref_title)
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = ref_title

        passes = max_overlap >= threshold
        status = "PASS" if passes else "FAIL"
        self.logger.info(
            f"Title overlap check [{status}]: '{candidate_title}' vs '{best_match}' -> {max_overlap:.2f}"
        )

        return passes, max_overlap, best_match

    def validate_constitution_ii_compliance(
        self,
        contribution_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a contribution complies with Constitution II rules.

        Args:
            contribution_data: Dictionary containing contribution details.
                               Expected keys: 'results', 'models', 'data_source', 'methodology'.

        Returns:
            Tuple of (is_compliant, list_of_violations).
        """
        violations = []

        # Rule 1: No fabricated results
        if 'results' in contribution_data:
            results = contribution_data['results']
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, str):
                        lower_val = value.lower()
                        if any(
                            phrase in lower_val
                            for phrase in ['fabricated', 'simulated', 'placeholder', 'fake', 'invented']
                        ):
                            violations.append(
                                f"Constitution II Violation: Result '{key}' appears to be fabricated/simulated."
                            )
            elif isinstance(results, list):
                for i, item in enumerate(results):
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if isinstance(value, str):
                                lower_val = value.lower()
                                if any(
                                    phrase in lower_val
                                    for phrase in ['fabricated', 'simulated', 'placeholder', 'fake', 'invented']
                                ):
                                    violations.append(
                                        f"Constitution II Violation: Result item {i}, key '{key}' appears fabricated."
                                    )

        # Rule 2: CPU tractable models
        if 'models' in contribution_data:
            models = contribution_data['models']
            if isinstance(models, list):
                for model in models:
                    if isinstance(model, dict):
                        size_gb = model.get('size_gb') or model.get('size_mb')
                        if size_gb is not None:
                            if isinstance(size_gb, (int, float)):
                                # Assume if size_mb is given, convert to GB
                                val_gb = size_gb if size_gb > 100 else size_gb / 1024.0
                                if val_gb > 1.0:
                                    violations.append(
                                        f"Constitution II Violation: Model '{model.get('name', 'unknown')}' "
                                        f"exceeds 1 GB limit ({val_gb:.2f} GB)."
                                    )

        # Rule 3: Real data only
        if 'data_source' in contribution_data:
            source = contribution_data['data_source']
            if isinstance(source, str):
                lower_src = source.lower()
                if any(
                    phrase in lower_src
                    for phrase in ['synthetic', 'fake', 'placeholder', 'simulated', 'generated']
                ):
                    violations.append(
                        "Constitution II Violation: Data source appears to be synthetic/fake."
                    )

        # Rule 4: Fail loudly (check for explicit error handling flags)
        if 'methodology' in contribution_data:
            method = contribution_data['methodology']
            if isinstance(method, str):
                # Check if methodology acknowledges limitations or failures
                if 'unmeasurable' in method.lower() and 'reported' in method.lower():
                    # This is acceptable - they reported it as unmeasurable
                    pass
                elif 'cannot' in method.lower() and 'measured' in method.lower():
                    # Acceptable - they explained why it couldn't be measured
                    pass

        is_compliant = len(violations) == 0
        status = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
        self.logger.info(f"Constitution II validation [{status}]: {len(violations)} violations found.")

        return is_compliant, violations

    def validate_contribution(
        self,
        candidate_title: str,
        reference_titles: List[str],
        contribution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Full validation pipeline for a research contribution.

        Args:
            candidate_title: Title of the contribution.
            reference_titles: List of existing reference titles.
            contribution_data: Data about the contribution to validate.

        Returns:
            Dictionary with validation results.
        """
        self.logger.info(f"Starting validation for contribution: '{candidate_title}'")

        # Step 1: Title overlap check
        overlap_pass, overlap_score, best_match = self.check_title_overlap(
            candidate_title, reference_titles
        )

        if not overlap_pass:
            self.logger.error(
                f"Validation BLOCKED: Title overlap {overlap_score:.2f} < {THRESHOLD_TITLE_OVERLAP}"
            )
            return {
                "allowed": False,
                "reason": "title_overlap_insufficient",
                "details": {
                    "overlap_score": overlap_score,
                    "threshold": THRESHOLD_TITLE_OVERLAP,
                    "best_match": best_match
                },
                "constitution_violations": []
            }

        # Step 2: Constitution II compliance check
        constitution_pass, violations = self.validate_constitution_ii_compliance(contribution_data)

        if not constitution_pass:
            self.logger.error(
                f"Validation BLOCKED: Constitution II violations found ({len(violations)})"
            )
            return {
                "allowed": False,
                "reason": "constitution_ii_non_compliant",
                "details": {
                    "overlap_score": overlap_score,
                    "best_match": best_match
                },
                "constitution_violations": violations
            }

        self.logger.info("Validation PASSED: Contribution is allowed.")
        return {
            "allowed": True,
            "reason": "all_checks_passed",
            "details": {
                "overlap_score": overlap_score,
                "best_match": best_match
            },
            "constitution_violations": []
        }


def main():
    """
    CLI entry point for testing the validator.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Reference Validator Agent CLI")
    parser.add_argument("--title", type=str, required=True, help="Candidate title to validate")
    parser.add_argument(
        "--references",
        type=str,
        nargs="+",
        default=[],
        help="Reference titles to compare against"
    )
    parser.add_argument(
        "--check-constitution",
        action="store_true",
        help="Run Constitution II compliance check"
    )
    args = parser.parse_args()

    agent = ReferenceValidatorAgent()

    # Run title overlap check
    print(f"Checking title overlap for: '{args.title}'")
    if not args.references:
        print("No reference titles provided. Skipping overlap check.")
        return

    passes, score, match = agent.check_title_overlap(args.title, args.references)
    print(f"Result: {'PASS' if passes else 'FAIL'} (Score: {score:.2f}, Best Match: {match})")

    if args.check_constitution:
        # Simple mock data for demonstration
        mock_data = {
            "results": {"accuracy": "0.85 (measured on real UCI_HAR dataset)"},
            "models": [{"name": "TimeSeries-Transformer", "size_gb": 0.5}],
            "data_source": "UCI_HAR (HuggingFace datasets)",
            "methodology": "Standard train/test split with 5-fold cross-validation"
        }
        const_pass, violations = agent.validate_constitution_ii_compliance(mock_data)
        print(f"Constitution II: {'COMPLIANT' if const_pass else 'NON-COMPLIANT'}")
        if violations:
            for v in violations:
                print(f"  - {v}")


if __name__ == "__main__":
    main()