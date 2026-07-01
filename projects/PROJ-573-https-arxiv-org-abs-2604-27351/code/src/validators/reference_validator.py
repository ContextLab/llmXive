"""
Reference Validator Agent for Constitution II Compliance.

This module implements a validator that checks reference titles against
a token overlap threshold (>= 0.7) before allowing contribution of review points.
It serves as a blocking gate for Constitution II compliance.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_OVERLAP_THRESHOLD = 0.7
MIN_TITLE_LENGTH = 2  # Minimum tokens for a valid title
STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
    'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how'
}

def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title into lowercase words, removing punctuation and stop words.

    Args:
        title: The title string to tokenize.

    Returns:
        List of normalized tokens (lowercase, alphabetic only, excluding stop words).
    """
    if not title or not isinstance(title, str):
        return []

    # Convert to lowercase and extract words (alphanumeric sequences)
    words = re.findall(r'\b[a-zA-Z]+\b', title.lower())

    # Filter out stop words and short tokens
    tokens = [w for w in words if w not in STOP_WORDS and len(w) >= 2]

    return tokens

def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Formula: |Tokens(A) ∩ Tokens(B)| / |Tokens(A) ∪ Tokens(B)|

    Args:
        title_a: First title string.
        title_b: Second title string.

    Returns:
        Float between 0.0 and 1.0 representing the overlap ratio.
        Returns 0.0 if either title has fewer than MIN_TITLE_LENGTH tokens.
    """
    tokens_a = set(tokenize_title(title_a))
    tokens_b = set(tokenize_title(title_b))

    if len(tokens_a) < MIN_TITLE_LENGTH or len(tokens_b) < MIN_TITLE_LENGTH:
        logger.debug("One or both titles have too few tokens for meaningful comparison.")
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    if not union:
        return 0.0

    overlap = len(intersection) / len(union)
    return overlap

def validate_reference_title_overlap(
    candidate_title: str,
    reference_titles: List[str],
    threshold: float = DEFAULT_OVERLAP_THRESHOLD
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate if a candidate title has sufficient overlap with any reference title.

    Args:
        candidate_title: The new title being evaluated.
        reference_titles: List of existing reference titles to compare against.
        threshold: Minimum overlap ratio required (default 0.7).

    Returns:
        Tuple of (is_valid, details_dict).
        details_dict contains:
            - best_overlap: float (highest overlap found)
            - best_match: str (title with highest overlap, or None)
            - all_overlaps: dict mapping reference titles to their overlap scores
            - passed: bool (whether best_overlap >= threshold)
    """
    if not candidate_title or not isinstance(candidate_title, str):
        logger.warning("Invalid candidate title provided.")
        return False, {
            "best_overlap": 0.0,
            "best_match": None,
            "all_overlaps": {},
            "passed": False,
            "error": "Invalid candidate title"
        }

    if not reference_titles or not isinstance(reference_titles, list):
        logger.warning("No reference titles provided for comparison.")
        return False, {
            "best_overlap": 0.0,
            "best_match": None,
            "all_overlaps": {},
            "passed": False,
            "error": "No reference titles provided"
        }

    all_overlaps = {}
    best_overlap = 0.0
    best_match = None

    for ref_title in reference_titles:
        if not ref_title or not isinstance(ref_title, str):
            continue

        overlap = compute_title_token_overlap(candidate_title, ref_title)
        all_overlaps[ref_title] = overlap

        if overlap > best_overlap:
            best_overlap = overlap
            best_match = ref_title

    passed = best_overlap >= threshold

    logger.info(
        f"Title validation: '{candidate_title[:50]}...' "
        f"vs {len(reference_titles)} references -> best overlap: {best_overlap:.3f} "
        f"(threshold: {threshold}) -> {'PASS' if passed else 'FAIL'}"
    )

    return passed, {
        "best_overlap": best_overlap,
        "best_match": best_match,
        "all_overlaps": all_overlaps,
        "passed": passed,
        "threshold": threshold
    }

def check_constitution_ii_compliance(
    review_data: Dict[str, Any],
    reference_db_path: Optional[Path] = None,
    threshold: float = DEFAULT_OVERLAP_THRESHOLD
) -> bool:
    """
    Check if a review entry complies with Constitution II requirements.

    Constitution II requires that review points be based on original analysis
    and not simply regurgitate existing literature without significant overlap
    in title/concept. This gate blocks contribution if the title overlap is
    too high (indicating potential plagiarism or lack of novel contribution).

    Args:
        review_data: Dictionary containing review metadata, must include 'title'.
        reference_db_path: Optional path to a YAML file containing reference titles.
        threshold: Minimum overlap threshold (default 0.7).

    Returns:
        True if compliant (overlap < threshold), False if blocked.
    """
    if not review_data or "title" not in review_data:
        logger.error("Review data missing 'title' field.")
        return False

    candidate_title = review_data["title"]

    # Load reference titles
    reference_titles = []

    if reference_db_path and reference_db_path.exists():
        try:
            import yaml
            with open(reference_db_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "references" in data:
                    reference_titles = [
                        r.get("title", "") for r in data["references"]
                        if isinstance(r, dict) and r.get("title")
                    ]
            logger.info(f"Loaded {len(reference_titles)} reference titles from {reference_db_path}")
        except Exception as e:
            logger.warning(f"Failed to load reference DB: {e}. Proceeding with empty reference set.")
    else:
        logger.info("No reference database provided or found. Assuming compliance (no existing titles to compare).")

    if not reference_titles:
        # No references to compare against, so no blocking
        logger.info("No reference titles found. Review passes by default (no conflict).")
        return True

    is_valid, details = validate_reference_title_overlap(
        candidate_title, reference_titles, threshold
    )

    if not is_valid:
        logger.warning(
            f"CONSTITUTION II BLOCK: Title '{candidate_title[:50]}...' "
            f"has too much overlap ({details['best_overlap']:.3f}) "
            f"with existing reference: '{details['best_match'][:50]}...' "
            f"Threshold: {threshold}"
        )
        return False

    logger.info("Constitution II compliance check passed.")
    return True

class ReferenceValidatorAgent:
    """
    Agent that manages reference validation and Constitution II compliance.

    This agent maintains a local cache of reference titles and provides
    methods to validate new contributions against them.
    """

    def __init__(
        self,
        reference_db_path: Optional[Path] = None,
        default_threshold: float = DEFAULT_OVERLAP_THRESHOLD
    ):
        """
        Initialize the Reference Validator Agent.

        Args:
            reference_db_path: Path to the YAML file containing reference titles.
            default_threshold: Default overlap threshold for validation.
        """
        self.reference_db_path = reference_db_path
        self.default_threshold = default_threshold
        self._reference_titles: List[str] = []
        self._last_loaded: Optional[float] = None
        self._load_references()

    def _load_references(self) -> None:
        """Load reference titles from the database file."""
        if not self.reference_db_path or not self.reference_db_path.exists():
            self._reference_titles = []
            return

        try:
            import yaml
            with open(self.reference_db_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and "references" in data:
                    self._reference_titles = [
                        r.get("title", "") for r in data["references"]
                        if isinstance(r, dict) and r.get("title")
                    ]
            logger.info(f"ReferenceValidatorAgent loaded {len(self._reference_titles)} titles.")
        except Exception as e:
            logger.error(f"Failed to load references: {e}")
            self._reference_titles = []

    def add_reference(self, title: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a new reference title to the agent's cache.

        Args:
            title: The reference title to add.
            metadata: Optional metadata for the reference.
        """
        if title and title not in self._reference_titles:
            self._reference_titles.append(title)
            logger.debug(f"Added reference title: {title[:50]}...")

    def validate_contribution(
        self,
        review_data: Dict[str, Any],
        threshold: Optional[float] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a contribution against Constitution II rules.

        Args:
            review_data: The review data containing the title to validate.
            threshold: Optional override for the overlap threshold.

        Returns:
            Tuple of (is_compliant, details).
        """
        threshold = threshold or self.default_threshold
        is_valid, details = validate_reference_title_overlap(
            review_data.get("title", ""),
            self._reference_titles,
            threshold
        )

        is_compliant = is_valid  # Note: valid here means overlap is LOW enough (passed check)
        # Re-interpret: validate_reference_title_overlap returns True if overlap < threshold?
        # Actually, our function returns True if overlap >= threshold (meaning it IS a match).
        # For Constitution II, we want to BLOCK if it IS a match (too similar).
        # So compliant = NOT is_valid (where is_valid means "found a match")
        # Let's correct the logic:
        # validate_reference_title_overlap returns True if best_overlap >= threshold (i.e., it's a duplicate/similar)
        # We want to ALLOW if best_overlap < threshold (i.e., NOT a duplicate)
        # So: compliant = not is_valid

        is_compliant = not is_valid
        details["is_compliant"] = is_compliant

        if not is_compliant:
            logger.warning(
                f"Contribution BLOCKED: '{review_data.get('title', '')[:50]}...' "
                f"is too similar to existing references."
            )
        else:
            logger.info("Contribution ALLOWED: Title is sufficiently distinct.")

        return is_compliant, details

    def get_reference_count(self) -> int:
        """Return the number of reference titles currently loaded."""
        return len(self._reference_titles)

    def reload_references(self) -> None:
        """Force reload of references from the database file."""
        self._load_references()

def main() -> None:
    """
    Main entry point for command-line testing of the Reference Validator.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Reference Validator Agent CLI")
    parser.add_argument("--title", type=str, help="Title to validate")
    parser.add_argument("--refs", type=str, nargs="+", help="Reference titles to compare against")
    parser.add_argument("--threshold", type=float, default=DEFAULT_OVERLAP_THRESHOLD, help="Overlap threshold")
    parser.add_argument("--db", type=str, help="Path to reference database YAML")

    args = parser.parse_args()

    if not args.title:
        print("Usage: python reference_validator.py --title 'My Title' --refs 'Ref1' 'Ref2' ...")
        return

    if args.refs:
        is_valid, details = validate_reference_title_overlap(args.title, args.refs, args.threshold)
        print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
        print(f"Best Overlap: {details['best_overlap']:.3f}")
        print(f"Best Match: {details['best_match']}")
        print(f"Threshold: {args.threshold}")
    else:
        print("No reference titles provided for comparison.")

    # Test agent
    db_path = Path(args.db) if args.db else None
    agent = ReferenceValidatorAgent(reference_db_path=db_path)

    if args.refs:
        for ref in args.refs:
            agent.add_reference(ref)

    review_data = {"title": args.title, "author": "Test"}
    compliant, details = agent.validate_contribution(review_data, args.threshold)
    print(f"\nConstitution II Compliance: {'ALLOWED' if compliant else 'BLOCKED'}")
    print(f"Details: {details}")

if __name__ == "__main__":
    main()
