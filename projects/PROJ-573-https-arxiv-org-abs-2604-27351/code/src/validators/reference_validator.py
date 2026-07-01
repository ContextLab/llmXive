"""
Reference Validator Agent for llmXive Scientific Pipeline.

This module implements a validation agent that ensures:
1. Reference titles have sufficient token overlap (>= 0.7) with the claim being reviewed.
2. Constitution II compliance is checked before contributing review points.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

# Constants
TOKEN_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_GATING_ENABLED = True

logger = get_logger(__name__)


def tokenize_title(title: str) -> List[str]:
    """
    Tokenize a title into a set of normalized tokens.
    
    Args:
        title: The title string to tokenize.
        
    Returns:
        A list of lowercase alphanumeric tokens.
    """
    if not title:
        return []
    
    # Convert to lowercase and extract alphanumeric tokens
    tokens = re.findall(r'[a-z0-9]+', title.lower())
    return [t for t in tokens if len(t) > 1]  # Filter out single chars


def compute_title_token_overlap(title_a: str, title_b: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.
    
    Args:
        title_a: First title string.
        title_b: Second title string.
        
    Returns:
        Float between 0.0 and 1.0 representing the overlap ratio.
    """
    tokens_a = set(tokenize_title(title_a))
    tokens_b = set(tokenize_title(title_b))
    
    if not tokens_a or not tokens_b:
        return 0.0
    
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    
    if not union:
        return 0.0
        
    return len(intersection) / len(union)


def validate_reference_title_overlap(
    claim_title: str,
    reference_title: str,
    threshold: float = TOKEN_OVERLAP_THRESHOLD
) -> Tuple[bool, float]:
    """
    Validate that a reference title has sufficient overlap with a claim title.
    
    Args:
        claim_title: The title of the claim being reviewed.
        reference_title: The title of the reference being evaluated.
        threshold: Minimum overlap threshold (default 0.7).
        
    Returns:
        Tuple of (is_valid, overlap_score).
    """
    overlap = compute_title_token_overlap(claim_title, reference_title)
    is_valid = overlap >= threshold
    
    logger.debug(
        f"Title overlap check: '{claim_title[:30]}...' vs "
        f"'{reference_title[:30]}...' -> {overlap:.3f} (valid: {is_valid})"
    )
    
    return is_valid, overlap


def check_constitution_ii_compliance(
    review_data: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Tuple[bool, List[str]]:
    """
    Check if a review contribution complies with Constitution II requirements.
    
    Constitution II requires:
    - Evidence-based claims
    - Proper citation of sources
    - No fabricated data
    - Transparent methodology
    
    Args:
        review_data: Dictionary containing review metadata and content.
        context: Optional context about the task or project state.
        
    Returns:
        Tuple of (is_compliant, list_of_violations).
    """
    violations = []
    
    # Check 1: Title overlap requirement
    claim_title = review_data.get("claim_title", "")
    reference_title = review_data.get("reference_title", "")
    
    if claim_title and reference_title:
        is_valid, overlap = validate_reference_title_overlap(
            claim_title, reference_title
        )
        if not is_valid:
            violations.append(
                f"Title token overlap ({overlap:.2f}) below threshold "
                f"({TOKEN_OVERLAP_THRESHOLD})"
            )
    else:
        if not claim_title:
            violations.append("Missing claim title")
        if not reference_title:
            violations.append("Missing reference title")
    
    # Check 2: Evidence presence
    if not review_data.get("evidence_provided"):
        violations.append("No evidence provided for review claim")
    
    # Check 3: Data integrity check (flag if fabricated data detected)
    if review_data.get("data_fabricated", False):
        violations.append("Fabricated data detected - Constitution II violation")
    
    # Check 4: Methodology transparency
    if not review_data.get("methodology_documented"):
        violations.append("Methodology not documented")
    
    is_compliant = len(violations) == 0
    
    if not is_compliant:
        logger.warning(
            f"Constitution II compliance check failed for review: "
            f"{len(violations)} violation(s): {', '.join(violations)}"
        )
    else:
        logger.info("Constitution II compliance check passed")
    
    return is_compliant, violations


class ReferenceValidatorAgent:
    """
    Agent that validates scientific references and review contributions.
    
    This agent enforces Constitution II compliance by:
    1. Checking title-token overlap between claims and references.
    2. Validating evidence and methodology documentation.
    3. Blocking non-compliant contributions from receiving review points.
    """
    
    def __init__(
        self,
        overlap_threshold: float = TOKEN_OVERLAP_THRESHOLD,
        gating_enabled: bool = CONSTITUTION_II_GATING_ENABLED
    ):
        """
        Initialize the Reference Validator Agent.
        
        Args:
            overlap_threshold: Minimum title token overlap required (default 0.7).
            gating_enabled: Whether to block non-compliant reviews (default True).
        """
        self.overlap_threshold = overlap_threshold
        self.gating_enabled = gating_enabled
        self.validation_log: List[Dict[str, Any]] = []
        
        logger.info(
            f"ReferenceValidatorAgent initialized with "
            f"overlap_threshold={overlap_threshold}, gating_enabled={gating_enabled}"
        )
    
    def validate_review(
        self,
        review_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a review contribution against Constitution II requirements.
        
        Args:
            review_data: Dictionary containing review metadata.
            context: Optional context about the task or project.
            
        Returns:
            Dictionary with validation results:
            - is_valid: Boolean indicating if review passed all checks.
            - overlap_score: Title token overlap score (if applicable).
            - violations: List of Constitution II violations found.
            - can_contribute_points: Whether review can contribute points.
        """
        # Perform title overlap check
        claim_title = review_data.get("claim_title", "")
        reference_title = review_data.get("reference_title", "")
        
        overlap_score = 0.0
        if claim_title and reference_title:
            is_valid_overlap, overlap_score = validate_reference_title_overlap(
                claim_title, reference_title, self.overlap_threshold
            )
        else:
            is_valid_overlap = False
            if not claim_title:
                logger.warning("Missing claim title for overlap validation")
            if not reference_title:
                logger.warning("Missing reference title for overlap validation")
        
        # Perform Constitution II compliance check
        is_compliant, violations = check_constitution_ii_compliance(
            review_data, context
        )
        
        # Determine if review can contribute points
        can_contribute = is_valid_overlap and is_compliant
        
        if self.gating_enabled and not can_contribute:
            logger.warning(
                "Review blocked by Constitution II gate - no points contributed"
            )
        
        result = {
            "is_valid": can_contribute,
            "overlap_score": overlap_score,
            "title_overlap_valid": is_valid_overlap,
            "constitution_ii_compliant": is_compliant,
            "violations": violations,
            "can_contribute_points": can_contribute
        }
        
        self.validation_log.append({
            "timestamp": context.get("timestamp") if context else None,
            "claim_title": claim_title,
            "reference_title": reference_title,
            "result": result
        })
        
        return result
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about validation attempts.
        
        Returns:
            Dictionary with validation statistics.
        """
        if not self.validation_log:
            return {
                "total_validations": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0
            }
        
        passed = sum(
            1 for entry in self.validation_log 
            if entry["result"]["can_contribute_points"]
        )
        
        return {
            "total_validations": len(self.validation_log),
            "passed": passed,
            "failed": len(self.validation_log) - passed,
            "pass_rate": passed / len(self.validation_log)
        }


def main():
    """
    Main entry point for standalone testing of the Reference Validator Agent.
    """
    # Create agent instance
    agent = ReferenceValidatorAgent()
    
    # Test case 1: Valid reference with high overlap
    valid_review = {
        "claim_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "evidence_provided": True,
        "methodology_documented": True,
        "data_fabricated": False
    }
    
    result1 = agent.validate_review(valid_review)
    logger.info(f"Test 1 (Valid): {result1}")
    
    # Test case 2: Invalid reference with low overlap
    invalid_review = {
        "claim_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Completely Unrelated Research Topic",
        "evidence_provided": True,
        "methodology_documented": True,
        "data_fabricated": False
    }
    
    result2 = agent.validate_review(invalid_review)
    logger.info(f"Test 2 (Low Overlap): {result2}")
    
    # Test case 3: Missing evidence (Constitution II violation)
    missing_evidence_review = {
        "claim_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "reference_title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        "evidence_provided": False,
        "methodology_documented": True,
        "data_fabricated": False
    }
    
    result3 = agent.validate_review(missing_evidence_review)
    logger.info(f"Test 3 (Missing Evidence): {result3}")
    
    # Print stats
    stats = agent.get_validation_stats()
    logger.info(f"Validation Statistics: {stats}")
    
    return stats


if __name__ == "__main__":
    main()
