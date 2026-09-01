"""
Reference Validator Agent.

Implements Constitution Principle II (Verified Accuracy) by validating external
citations and enforcing a title-token-overlap threshold >= 0.7 between a claimed
source and the actual retrieved document metadata.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Threshold for token overlap (Constitution Principle II)
TOKEN_OVERLAP_THRESHOLD = 0.7

def _normalize_tokens(text: str) -> List[str]:
    """
    Normalize text into a sorted list of unique tokens.
    - Lowercase
    - Remove punctuation
    - Split on whitespace
    - Remove common stop-words (optional, but improves robustness)
    - Sort for deterministic comparison
    """
    if not text:
        return []
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation and special chars, keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Split and filter empty strings
    tokens = [t for t in text.split() if t]
    # Remove common stop-words to focus on meaningful tokens
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where',
        'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now'
    }
    meaningful_tokens = [t for t in tokens if t not in stop_words]
    # Sort and return unique tokens
    return sorted(list(set(meaningful_tokens)))

def _calculate_token_overlap(set1: List[str], set2: List[str]) -> float:
    """
    Calculate the Jaccard similarity (token overlap) between two sets of tokens.
    Jaccard = |Intersection| / |Union|
    Returns a float between 0.0 and 1.0.
    """
    if not set1 or not set2:
        return 0.0
    s1 = set(set1)
    s2 = set(set2)
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    if union == 0:
        return 0.0
    return intersection / union

def validate_citation(
    claimed_title: str,
    actual_metadata: Dict[str, Any]
) -> Tuple[bool, float, str]:
    """
    Validate a citation by comparing the claimed title against actual metadata.

    Args:
        claimed_title: The title string provided in the citation claim.
        actual_metadata: A dictionary containing metadata from the retrieved source,
                         expected to have at least a 'title' key.

    Returns:
        Tuple of (is_valid, overlap_score, reason_message)
        - is_valid: True if overlap_score >= TOKEN_OVERLAP_THRESHOLD
        - overlap_score: The calculated Jaccard similarity
        - reason_message: Human-readable explanation of the result
    """
    actual_title = actual_metadata.get('title', '')
    if not actual_title:
        return False, 0.0, "Actual metadata missing 'title' field."

    claimed_tokens = _normalize_tokens(claimed_title)
    actual_tokens = _normalize_tokens(actual_title)

    overlap = _calculate_token_overlap(claimed_tokens, actual_tokens)
    is_valid = overlap >= TOKEN_OVERLAP_THRESHOLD

    if is_valid:
        reason = (
            f"Validation PASSED. Overlap score {overlap:.2f} >= {TOKEN_OVERLAP_THRESHOLD}. "
            f"Claimed: '{claimed_title[:50]}...' | Actual: '{actual_title[:50]}...'"
        )
        logger.info(reason)
    else:
        reason = (
            f"Validation FAILED. Overlap score {overlap:.2f} < {TOKEN_OVERLAP_THRESHOLD}. "
            f"Claimed: '{claimed_title[:50]}...' | Actual: '{actual_title[:50]}...'"
        )
        logger.warning(reason)

    return is_valid, overlap, reason

def run_validation_on_samples(
    sample_claims: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run validation on a list of sample claims and return a summary report.

    Args:
        sample_claims: List of dicts with keys:
                       - 'claimed_title': str
                       - 'actual_metadata': dict (must contain 'title')

    Returns:
        Dict with:
          - 'total': int
          - 'passed': int
          - 'failed': int
          - 'details': List of detailed results
    """
    results = {
        'total': len(sample_claims),
        'passed': 0,
        'failed': 0,
        'details': []
    }

    for claim in sample_claims:
        claimed_title = claim.get('claimed_title', '')
        actual_meta = claim.get('actual_metadata', {})

        if not claimed_title or not actual_meta:
            results['details'].append({
                'status': 'error',
                'reason': 'Missing claimed_title or actual_metadata'
            })
            results['failed'] += 1
            continue

        is_valid, score, reason = validate_citation(claimed_title, actual_meta)
        status = 'passed' if is_valid else 'failed'
        if is_valid:
            results['passed'] += 1
        else:
            results['failed'] += 1

        results['details'].append({
            'claimed_title': claimed_title,
            'actual_title': actual_meta.get('title', ''),
            'overlap_score': score,
            'status': status,
            'reason': reason
        })

    return results

def main():
    """
    Main entry point to demonstrate the Reference Validator Agent.
    Runs validation on a set of sample claims (hardcoded for demonstration).
    """
    logger.info("Starting Reference Validator Agent (Constitution Principle II)")

    # Sample claims for demonstration
    # In a real scenario, these would come from a research log or dataset
    sample_claims = [
        {
            "claimed_title": "Experimental Solvation Energies of Small Ions in Water",
            "actual_metadata": {
                "title": "Experimental Solvation Energies of Small Ions in Water and Alcohols",
                "source": "NIST Chemistry WebBook"
            }
        },
        {
            "claimed_title": "Born Model Predictions for Ionic Radii",
            "actual_metadata": {
                "title": "A Study on Crystal Radii and Hydration Shells",
                "source": "Journal of Physical Chemistry"
            }
        },
        {
            "claimed_title": "Dielectric Constants of Organic Solvents",
            "actual_metadata": {
                "title": "Dielectric Constants of Organic Solvents at 298K",
                "source": "CRC Handbook of Chemistry and Physics"
            }
        },
        {
            "claimed_title": "Completely Unrelated Fake Paper Title",
            "actual_metadata": {
                "title": "Quantum Entanglement in Macroscopic Systems",
                "source": "Physical Review Letters"
            }
        }
    ]

    report = run_validation_on_samples(sample_claims)

    print("\n--- Reference Validation Report ---")
    print(f"Total Claims: {report['total']}")
    print(f"Passed: {report['passed']}")
    print(f"Failed: {report['failed']}")
    print("Threshold: >= 0.7 token overlap")
    print("-----------------------------------\n")

    for i, detail in enumerate(report['details'], 1):
        print(f"Claim {i}: {detail['status'].upper()}")
        print(f"  Overlap Score: {detail['overlap_score']:.2f}")
        print(f"  Reason: {detail['reason']}")
        print()

    if report['failed'] > 0:
        print("WARNING: Some citations failed validation.")
        return 1
    else:
        print("SUCCESS: All citations validated.")
        return 0

if __name__ == "__main__":
    import sys
    # Set up basic logging for console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
