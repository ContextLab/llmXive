"""
Reference Validator Agent for llmXive.

This module implements the ReferenceValidatorAgent which enforces:
1. Title-token-overlap >= 0.7 check before contributing review points.
2. A blocking gate for Constitution II compliance.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants
MIN_TITLE_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_GATE_KEY = "constitution_ii_compliant"
CONSTITUTION_II_CONFIG_PATH = Path("state/projects/PROJ-573-https-arxiv-org-abs-2604-27351/constitution_ii_status.yaml")


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard-like token overlap between two titles.

    Args:
        title_a: First title string.
        title_b: Second title string.

    Returns:
        Float between 0.0 and 1.0 representing the overlap ratio.
    """
    if not title_a or not title_b:
        return 0.0

    # Normalize: lowercase and extract alphanumeric tokens
    def tokenize(text: str) -> Set[str]:
        return set(re.findall(r'\b[a-z0-9]+\b', text.lower()))

    tokens_a = tokenize(title_a)
    tokens_b = tokenize(title_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    return len(intersection) / len(union) if union else 0.0


def validate_reference_claim(
    claim_title: str,
    reference_title: str,
    min_overlap: float = MIN_TITLE_OVERLAP_THRESHOLD
) -> Tuple[bool, float, str]:
    """
    Validate a claim against a reference title.

    Args:
        claim_title: The title of the claim being reviewed.
        reference_title: The title of the reference paper/document.
        min_overlap: Minimum required token overlap.

    Returns:
        Tuple of (is_valid, overlap_score, message)
    """
    score = compute_title_token_overlap(claim_title, reference_title)
    is_valid = score >= min_overlap

    if is_valid:
        msg = f"Validation passed: overlap {score:.2f} >= {min_overlap}"
    else:
        msg = f"Validation failed: overlap {score:.2f} < {min_overlap}"

    return is_valid, score, msg


class ReferenceValidatorAgent:
    """
    Agent that validates references before allowing review points to be contributed.
    Enforces Constitution II compliance as a blocking gate.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.min_overlap = self.config.get("min_title_overlap", MIN_TITLE_OVERLAP_THRESHOLD)
        self._constitution_ii_loaded = False
        self._constitution_ii_status = False
        self._load_constitution_ii_status()

    def _load_constitution_ii_status(self) -> None:
        """Load Constitution II compliance status from state file."""
        try:
            if CONSTITUTION_II_CONFIG_PATH.exists():
                import yaml
                with open(CONSTITUTION_II_CONFIG_PATH, "r") as f:
                    data = yaml.safe_load(f)
                    self._constitution_ii_status = bool(data.get(CONSTITUTION_II_GATE_KEY, False))
                self._constitution_ii_loaded = True
                logger.info(f"Constitution II status loaded: {self._constitution_ii_status}")
            else:
                logger.warning(f"Constitution II config not found at {CONSTITUTION_II_CONFIG_PATH}. Gate is blocking.")
                self._constitution_ii_status = False
        except Exception as e:
            logger.error(f"Failed to load Constitution II status: {e}")
            self._constitution_ii_status = False

    def check_constitution_ii_gate(self) -> bool:
        """
        Check if Constitution II compliance gate is passed.

        Returns:
            True if compliant, False otherwise.
        """
        return self._constitution_ii_status

    def validate_and_contribute_points(
        self,
        claim_title: str,
        reference_title: str,
        potential_points: int = 1
    ) -> Dict[str, Any]:
        """
        Attempt to validate a reference and contribute review points.

        This method performs two checks:
        1. Constitution II compliance (blocking gate).
        2. Title token overlap >= 0.7.

        Args:
            claim_title: Title of the claim being reviewed.
            reference_title: Title of the reference being cited.
            potential_points: Points to award if validation passes.

        Returns:
            Dictionary with validation result and points awarded.
        """
        result = {
            "points_awarded": 0,
            "overlap_score": 0.0,
            "validation_passed": False,
            "gate_passed": False,
            "message": ""
        }

        # Check 1: Constitution II Gate
        if not self.check_constitution_ii_gate():
            result["message"] = "BLOCKED: Constitution II compliance gate not passed."
            logger.warning(result["message"])
            return result

        result["gate_passed"] = True

        # Check 2: Title Token Overlap
        is_valid, score, msg = validate_reference_claim(
            claim_title,
            reference_title,
            self.min_overlap
        )
        result["overlap_score"] = score
        result["validation_passed"] = is_valid

        if is_valid:
            result["points_awarded"] = potential_points
            result["message"] = f"Validation passed: {msg}. Awarded {potential_points} points."
            logger.info(result["message"])
        else:
            result["message"] = f"Validation failed: {msg}. Points not awarded."
            logger.warning(result["message"])

        return result

    def update_constitution_ii_status(self, is_compliant: bool) -> None:
        """
        Update the Constitution II compliance status.

        Args:
            is_compliant: New compliance status.
        """
        self._constitution_ii_status = is_compliant
        self._constitution_ii_loaded = True

        # Persist to state file
        CONSTITUTION_II_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        import yaml
        with open(CONSTITUTION_II_CONFIG_PATH, "w") as f:
            yaml.dump({CONSTITUTION_II_GATE_KEY: is_compliant}, f)
        logger.info(f"Constitution II status updated to {is_compliant} and persisted.")


def main():
    """Entry point for testing the ReferenceValidatorAgent."""
    import argparse
    parser = argparse.ArgumentParser(description="Reference Validator Agent")
    parser.add_argument("--claim-title", type=str, required=True, help="Title of the claim")
    parser.add_argument("--ref-title", type=str, required=True, help="Title of the reference")
    parser.add_argument("--constit-ii", type=bool, default=False, help="Set Constitution II status")
    args = parser.parse_args()

    agent = ReferenceValidatorAgent()

    if args.constit_ii is not None:
        agent.update_constitution_ii_status(args.constit_ii)

    result = agent.validate_and_contribute_points(
        claim_title=args.claim_title,
        reference_title=args.ref_title
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    main()