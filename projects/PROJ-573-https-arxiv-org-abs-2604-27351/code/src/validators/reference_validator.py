"""
Reference Validator Agent for llmXive.

This module implements a validation agent that ensures references contributed
to the research pipeline meet specific quality criteria:
1. Title-token-overlap >= 0.7 with the target paper title.
2. Constitution II compliance (blocking gate).
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constitution II requirements (simplified for this implementation)
CONSTITUTION_II_REQUIREMENTS = {
    "must_have_abstract": True,
    "must_have_doi_or_arxiv": True,
    "max_authors": 50,
    "must_be_peer_reviewed": False,  # Preprints allowed
    "language": "en"
}

def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title into lowercase alphanumeric tokens.

    Args:
        title: The paper title string.

    Returns:
        List of normalized tokens.
    """
    if not title:
        return []
    # Convert to lowercase and split on non-alphanumeric characters
    tokens = re.findall(r'[a-z0-9]+', title.lower())
    # Filter out very short tokens (stopwords would be filtered in a real system)
    return [t for t in tokens if len(t) > 1]

def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Args:
        title_a: First title.
        title_b: Second title.

    Returns:
        Float between 0.0 and 1.0 representing overlap.
    """
    tokens_a = set(tokenize_title(title_a))
    tokens_b = set(tokenize_title(title_b))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    return len(intersection) / len(union) if union else 0.0

def validate_reference_title_overlap(reference_title: str, target_title: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """
    Validate that a reference title has sufficient token overlap with the target title.

    Args:
        reference_title: The title of the reference being validated.
        target_title: The title of the target paper (e.g., the one being reviewed).
        threshold: Minimum overlap required (default 0.7).

    Returns:
        Tuple of (is_valid, overlap_score).
    """
    overlap = compute_title_token_overlap(reference_title, target_title)
    is_valid = overlap >= threshold
    logger.debug(f"Title overlap check: '{reference_title}' vs '{target_title}' -> {overlap:.4f} (valid: {is_valid})")
    return is_valid, overlap

def check_constitution_ii_compliance(reference_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if a reference meets Constitution II compliance requirements.

    Args:
        reference_data: Dictionary containing reference metadata (title, abstract, doi, etc.).

    Returns:
        Tuple of (is_compliant, list_of_violations).
    """
    violations = []

    # Check abstract presence
    if CONSTITUTION_II_REQUIREMENTS["must_have_abstract"]:
        if not reference_data.get("abstract") or len(reference_data.get("abstract", "")) < 50:
            violations.append("Missing or too short abstract")

    # Check DOI or arXiv ID
    if CONSTITUTION_II_REQUIREMENTS["must_have_doi_or_arxiv"]:
        has_doi = bool(reference_data.get("doi"))
        has_arxiv = bool(reference_data.get("arxiv_id"))
        if not (has_doi or has_arxiv):
            violations.append("Missing DOI or arXiv ID")

    # Check author count
    authors = reference_data.get("authors", [])
    if len(authors) > CONSTITUTION_II_REQUIREMENTS["max_authors"]:
        violations.append(f"Too many authors: {len(authors)} > {CONSTITUTION_II_REQUIREMENTS['max_authors']}")

    # Language check (basic)
    if CONSTITUTION_II_REQUIREMENTS["language"] == "en":
        title = reference_data.get("title", "")
        # Simple heuristic: if title contains non-ASCII characters that aren't common in English
        if not re.match(r'^[\x00-\x7F]+$', title):
            # More sophisticated NLP would be needed for a real system
            logger.warning("Non-ASCII title detected, assuming English compatibility for now")

    is_compliant = len(violations) == 0
    return is_compliant, violations

class ReferenceValidatorAgent:
    """
    Agent that validates references before they contribute review points.

    This agent enforces:
    1. Title-token-overlap >= 0.7 with the target paper.
    2. Constitution II compliance as a blocking gate.
    """

    def __init__(self, target_title: str, overlap_threshold: float = 0.7):
        """
        Initialize the validator agent.

        Args:
            target_title: The title of the paper being reviewed.
            overlap_threshold: Minimum token overlap required (default 0.7).
        """
        self.target_title = target_title
        self.overlap_threshold = overlap_threshold
        self.validation_log: List[Dict[str, Any]] = []

    def validate_reference(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single reference against all criteria.

        Args:
            reference: Dictionary containing reference metadata.

        Returns:
            Dictionary with validation results and whether points should be awarded.
        """
        ref_title = reference.get("title", "")
        result = {
            "reference_id": reference.get("id", "unknown"),
            "title": ref_title,
            "passed_title_overlap": False,
            "title_overlap_score": 0.0,
            "passed_constitution_ii": False,
            "constitution_violations": [],
            "should_contribute_points": False,
            "reason": ""
        }

        # Check 1: Title token overlap
        passed_overlap, overlap_score = validate_reference_title_overlap(
            ref_title, self.target_title, self.overlap_threshold
        )
        result["passed_title_overlap"] = passed_overlap
        result["title_overlap_score"] = overlap_score

        if not passed_overlap:
            result["reason"] = f"Title overlap {overlap_score:.2f} < {self.overlap_threshold}"
            self.validation_log.append(result)
            return result

        # Check 2: Constitution II compliance (blocking gate)
        passed_const, violations = check_constitution_ii_compliance(reference)
        result["passed_constitution_ii"] = passed_const
        result["constitution_violations"] = violations

        if not passed_const:
            result["reason"] = f"Constitution II violations: {', '.join(violations)}"
            self.validation_log.append(result)
            return result

        # All checks passed
        result["should_contribute_points"] = True
        result["reason"] = "All validation checks passed"
        self.validation_log.append(result)
        logger.info(f"Reference {result['reference_id']} validated successfully")
        return result

    def validate_batch(self, references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a batch of references.

        Args:
            references: List of reference dictionaries.

        Returns:
            List of validation result dictionaries.
        """
        return [self.validate_reference(ref) for ref in references]

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all validations performed.

        Returns:
            Dictionary with counts and statistics.
        """
        total = len(self.validation_log)
        if total == 0:
            return {
                "total_validated": 0,
                "passed": 0,
                "failed_overlap": 0,
                "failed_constitution": 0,
                "contribution_rate": 0.0
            }

        passed = sum(1 for r in self.validation_log if r["should_contribute_points"])
        failed_overlap = sum(1 for r in self.validation_log if not r["passed_title_overlap"])
        failed_const = sum(1 for r in self.validation_log if r["passed_title_overlap"] and not r["passed_constitution_ii"])

        return {
            "total_validated": total,
            "passed": passed,
            "failed_overlap": failed_overlap,
            "failed_constitution": failed_const,
            "contribution_rate": passed / total if total > 0 else 0.0
        }

def main():
    """
    Main entry point for standalone testing of the ReferenceValidatorAgent.
    """
    # Example usage
    target_paper_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"

    # Sample references (some valid, some invalid)
    sample_references = [
        {
            "id": "ref_001",
            "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
            "abstract": "This paper presents a benchmark for heterogeneous scientific foundation models...",
            "doi": "10.1234/example",
            "authors": ["Alice", "Bob"]
        },
        {
            "id": "ref_002",
            "title": "Completely Unrelated Title About Cats",
            "abstract": "A study on feline behavior...",
            "doi": "10.1234/cats",
            "authors": ["Charlie"]
        },
        {
            "id": "ref_003",
            "title": "Heterogeneous Model Collaboration",
            "abstract": "Short",  # Too short abstract
            "authors": ["Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy", "Kevin", "Liam", "Mia",
                        "Noah", "Olivia", "Peter", "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy",
                        "Xavier", "Yara", "Zack", "Amy", "Ben", "Cara", "Dan", "Ella", "Finn", "Gina", "Hank",
                        "Iris", "Jack", "Kate", "Leo", "Maya", "Nate", "Ora", "Paul", "Quin", "Rose", "Stan",
                        "Tara", "Ursula", "Vince", "Will", "Xena", "Yolanda", "Zane", "Anna", "Bill", "Cathy",
                        "Drew", "Ellen", "Fred", "Gwen", "Harry", "Irene", "James", "Karen", "Larry", "Monica"]
        }
    ]

    validator = ReferenceValidatorAgent(target_title=target_paper_title)
    results = validator.validate_batch(sample_references)

    print(f"Validation results for target: '{target_paper_title}'")
    print("-" * 80)
    for res in results:
        status = "PASS" if res["should_contribute_points"] else "FAIL"
        print(f"{res['reference_id']}: {status}")
        print(f"  Title: {res['title']}")
        print(f"  Overlap: {res['title_overlap_score']:.2f}")
        print(f"  Reason: {res['reason']}")
        print()

    summary = validator.get_validation_summary()
    print("Summary:")
    print(f"  Total: {summary['total_validated']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed (Overlap): {summary['failed_overlap']}")
    print(f"  Failed (Constitution II): {summary['failed_constitution']}")
    print(f"  Contribution Rate: {summary['contribution_rate']:.2%}")

if __name__ == "__main__":
    main()