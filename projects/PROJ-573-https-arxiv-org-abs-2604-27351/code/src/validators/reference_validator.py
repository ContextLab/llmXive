"""
Reference Validator Agent for llmXive.

Implements a blocking gate for Constitution II compliance and validates
reference quality via title-token-overlap scoring before contributing
review points.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Threshold for title-token overlap (Constitution II compliance)
TITLE_TOKEN_OVERLAP_THRESHOLD = 0.7

class ReferenceValidatorAgent:
    """
    Agent that validates references against Constitution II requirements.
    
    Attributes:
        threshold (float): Minimum title-token overlap required to accept a reference.
    """

    def __init__(self, threshold: float = TITLE_TOKEN_OVERLAP_THRESHOLD):
        """
        Initialize the Reference Validator Agent.
        
        Args:
            threshold: Minimum overlap score (0.0 to 1.0) required.
        """
        self.threshold = threshold
        self._review_points = 0
        logger.info(f"ReferenceValidatorAgent initialized with threshold {threshold}")

    def tokenize_title(self, title: str) -> Set[str]:
        """
        Tokenize a title into a set of lowercase alphanumeric tokens.
        
        Args:
            title: The title string to tokenize.
            
        Returns:
            A set of normalized tokens.
        """
        if not title:
            return set()
        # Convert to lowercase, replace non-alphanumeric with space, split
        tokens = re.sub(r'[^a-z0-9\s]', ' ', title.lower()).split()
        # Filter out very short tokens (noise)
        return {t for t in tokens if len(t) > 2}

    def compute_title_token_overlap(self, title_a: str, title_b: str) -> float:
        """
        Compute the Jaccard similarity (token overlap) between two titles.
        
        Formula: |A ∩ B| / |A ∪ B|
        
        Args:
            title_a: First title string.
            title_b: Second title string.
            
        Returns:
            Float between 0.0 and 1.0 representing overlap.
        """
        tokens_a = self.tokenize_title(title_a)
        tokens_b = self.tokenize_title(title_b)
        
        if not tokens_a or not tokens_b:
            return 0.0
            
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)

    def validate_reference(self, reference: Dict[str, Any], target_title: str) -> Tuple[bool, float, str]:
        """
        Validate a single reference against a target title.
        
        Args:
            reference: Dictionary containing reference metadata (must include 'title').
            target_title: The target title to compare against.
            
        Returns:
            Tuple of (is_valid, overlap_score, reason_string)
        """
        ref_title = reference.get("title", "")
        
        if not ref_title:
            return False, 0.0, "Reference missing title"

        score = self.compute_title_token_overlap(ref_title, target_title)
        
        if score >= self.threshold:
            return True, score, f"Overlap {score:.2f} >= threshold {self.threshold}"
        else:
            return False, score, f"Overlap {score:.2f} < threshold {self.threshold}"

    def validate_batch(self, references: List[Dict[str, Any]], target_title: str) -> Dict[str, Any]:
        """
        Validate a batch of references against a target title.
        
        Args:
            references: List of reference dictionaries.
            target_title: The target title to compare against.
            
        Returns:
            Dictionary with validation results summary.
        """
        results = {
            "target_title": target_title,
            "total_references": len(references),
            "valid_count": 0,
            "invalid_count": 0,
            "details": []
        }
        
        for ref in references:
            is_valid, score, reason = self.validate_reference(ref, target_title)
            
            if is_valid:
                results["valid_count"] += 1
                self._review_points += 1
            else:
                results["invalid_count"] += 1
                
            results["details"].append({
                "title": ref.get("title", "Unknown"),
                "overlap_score": score,
                "is_valid": is_valid,
                "reason": reason
            })
            
        logger.info(f"Batch validation complete: {results['valid_count']}/{results['total_references']} valid")
        return results

    def check_constitution_ii_compliance(self, reference: Dict[str, Any], target_title: str) -> bool:
        """
        Blocking gate check for Constitution II compliance.
        
        This method MUST return True before any review points are contributed
        for the given reference.
        
        Args:
            reference: The reference to validate.
            target_title: The target title to compare against.
            
        Returns:
            True if compliant (overlap >= threshold), False otherwise.
        """
        is_valid, score, reason = self.validate_reference(reference, target_title)
        
        if not is_valid:
            logger.warning(f"Constitution II Gate Blocked: {reason}")
            return False
            
        logger.info(f"Constitution II Gate Passed: {reason}")
        return True

    def contribute_review_points(self, reference: Dict[str, Any], target_title: str) -> int:
        """
        Attempt to contribute review points for a reference.
        
        Points are only contributed if the reference passes the 
        Constitution II blocking gate.
        
        Args:
            reference: The reference to validate.
            target_title: The target title to compare against.
            
        Returns:
            Number of points contributed (1 if passed, 0 if blocked).
        """
        if self.check_constitution_ii_compliance(reference, target_title):
            return 1
        return 0

    def get_review_points(self) -> int:
        """
        Get the current total of accumulated review points.
        
        Returns:
            Integer count of review points.
        """
        return self._review_points

    def reset_points(self):
        """Reset the accumulated review points to zero."""
        self._review_points = 0
        logger.info("Review points reset to 0")


def main():
    """
    Main entry point for the Reference Validator Agent.
    
    Runs a demonstration of the validation logic using synthetic data
    that represents real-world scenarios (no fabrication of metrics).
    """
    agent = ReferenceValidatorAgent(threshold=TITLE_TOKEN_OVERLAP_THRESHOLD)
    
    # Define a target paper title (simulating a query)
    target = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"
    
    # Define test references (simulating a candidate list)
    test_references = [
        {"title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark", "id": "ref_001"},
        {"title": "Benchmarking Scientific Models", "id": "ref_002"},
        {"title": "Foundation Models for Science", "id": "ref_003"},
        {"title": "Collaboration in Scientific AI", "id": "ref_004"},
        {"title": "Heterogeneous Models and Scientific Collaboration", "id": "ref_005"}
    ]
    
    logger.info(f"--- Starting Reference Validation for: '{target}' ---")
    logger.info(f"Threshold: {agent.threshold}")
    
    results = agent.validate_batch(test_references, target)
    
    # Log detailed results
    for detail in results["details"]:
        status = "PASS" if detail["is_valid"] else "FAIL"
        logger.info(f"  [{status}] {detail['title']} (Score: {detail['overlap_score']:.3f})")
    
    # Log summary
    logger.info(f"--- Summary ---")
    logger.info(f"Total Valid: {results['valid_count']}")
    logger.info(f"Total Invalid: {results['invalid_count']}")
    logger.info(f"Accumulated Review Points: {agent.get_review_points()}")
    
    # Verify blocking gate behavior
    blocked_ref = {"title": "Completely Unrelated Topic"}
    points = agent.contribute_review_points(blocked_ref, target)
    if points == 0:
        logger.info("Blocking gate correctly prevented points for unrelated reference.")
    else:
        logger.error("Blocking gate failed: points awarded for unrelated reference.")

if __name__ == "__main__":
    main()
