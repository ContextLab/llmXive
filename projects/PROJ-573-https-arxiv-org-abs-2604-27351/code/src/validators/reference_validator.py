import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Threshold for title-token-overlap check
TITLE_TOKEN_OVERLAP_THRESHOLD = 0.7

# Constitution II compliance check identifiers
CONSTITUTION_II_REQUIREMENTS = [
    "peer_review_compliance",
    "citation_accuracy",
    "claim_verification"
]

def compute_title_token_overlap(title1: str, title2: str) -> float:
    """
    Compute the token overlap similarity between two titles.
    Uses Jaccard similarity on lowercased, tokenized words.
    
    Args:
        title1: First title string
        title2: Second title string
        
    Returns:
        Float between 0.0 and 1.0 representing overlap ratio
    """
    if not title1 or not title2:
        return 0.0
        
    # Tokenize: lowercase, split on whitespace/punctuation
    tokens1 = set(re.findall(r'\b\w+\b', title1.lower()))
    tokens2 = set(re.findall(r'\b\w+\b', title2.lower()))
    
    if not tokens1 or not tokens2:
        return 0.0
        
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    return len(intersection) / len(union) if union else 0.0

def validate_reference_claim(
    claim_title: str,
    reference_title: str,
    threshold: float = TITLE_TOKEN_OVERLAP_THRESHOLD
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Validate a reference claim by checking title-token-overlap.
    
    Args:
        claim_title: Title of the claim being validated
        reference_title: Title of the reference paper/document
        threshold: Minimum overlap required (default 0.7)
        
    Returns:
        Tuple of (is_valid, overlap_score, details_dict)
    """
    overlap = compute_title_token_overlap(claim_title, reference_title)
    is_valid = overlap >= threshold
    
    details = {
        "claim_title": claim_title,
        "reference_title": reference_title,
        "overlap_score": overlap,
        "threshold": threshold,
        "passed": is_valid
    }
    
    logger.debug(f"Reference validation: overlap={overlap:.3f}, valid={is_valid}")
    return is_valid, overlap, details

def check_constitution_ii_compliance(
    review_data: Dict[str, Any]
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Perform blocking gate check for Constitution II compliance.
    
    Args:
        review_data: Dictionary containing review metadata and claims
        
    Returns:
        Tuple of (is_compliant, missing_requirements, compliance_details)
    """
    missing = []
    details = {
        "requirements_checked": CONSTITUTION_II_REQUIREMENTS,
        "results": {}
    }
    
    for req in CONSTITUTION_II_REQUIREMENTS:
        if req in review_data and review_data[req]:
            details["results"][req] = True
        else:
            details["results"][req] = False
            missing.append(req)
    
    is_compliant = len(missing) == 0
    
    logger.info(
        f"Constitution II compliance: {is_compliant}, "
        f"missing: {missing}"
    )
    
    return is_compliant, missing, details

class ReferenceValidatorAgent:
    """
    Agent for validating research references and enforcing Constitution II compliance.
    
    This agent performs:
    1. Title-token-overlap checks between claims and references
    2. Constitution II compliance gating before allowing review contributions
    """
    
    def __init__(
        self,
        overlap_threshold: float = TITLE_TOKEN_OVERLAP_THRESHOLD
    ):
        """
        Initialize the ReferenceValidatorAgent.
        
        Args:
            overlap_threshold: Minimum title-token-overlap score required
        """
        self.overlap_threshold = overlap_threshold
        self.validation_log: List[Dict[str, Any]] = []
        logger.info(f"ReferenceValidatorAgent initialized with threshold={overlap_threshold}")
    
    def validate_claim_reference(
        self,
        claim_title: str,
        reference_title: str
    ) -> Dict[str, Any]:
        """
        Validate a single claim against a reference.
        
        Args:
            claim_title: Title of the claim
            reference_title: Title of the reference
            
        Returns:
            Dictionary with validation results
        """
        is_valid, score, details = validate_reference_claim(
            claim_title,
            reference_title,
            self.overlap_threshold
        )
        
        result = {
            "claim_title": claim_title,
            "reference_title": reference_title,
            "is_valid": is_valid,
            "overlap_score": score,
            "timestamp": None  # Can be populated by caller if needed
        }
        result.update(details)
        
        self.validation_log.append(result)
        return result
    
    def validate_batch(
        self,
        claims: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple claims against their references.
        
        Args:
            claims: List of dicts with 'claim_title' and 'reference_title' keys
            
        Returns:
            List of validation result dictionaries
        """
        results = []
        for claim in claims:
            claim_title = claim.get("claim_title", "")
            ref_title = claim.get("reference_title", "")
            
            if not claim_title or not ref_title:
                logger.warning("Skipping validation: missing claim or reference title")
                continue
                
            result = self.validate_claim_reference(claim_title, ref_title)
            results.append(result)
        
        return results
    
    def gate_contribution(
        self,
        review_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Blocking gate for Constitution II compliance before contributing review points.
        
        Args:
            review_data: Dictionary containing review metadata
            
        Returns:
            Tuple of (can_contribute, reason)
        """
        is_compliant, missing_reqs, details = check_constitution_ii_compliance(review_data)
        
        if not is_compliant:
            reason = f"Constitution II compliance failed. Missing: {', '.join(missing_reqs)}"
            logger.warning(reason)
            return False, reason
        
        # Also check title-token-overlap for any claims in review_data
        claims = review_data.get("claims", [])
        if claims:
            batch_results = self.validate_batch(claims)
            failed_checks = [r for r in batch_results if not r["is_valid"]]
            
            if failed_checks:
                reason = (
                    f"Title-token-overlap check failed for {len(failed_checks)} claims. "
                    f"Threshold: {self.overlap_threshold}"
                )
                logger.warning(reason)
                return False, reason
        
        logger.info("Contribution gate passed: Constitution II compliant")
        return True, "Contribution approved"
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validations performed by this agent.
        
        Returns:
            Dictionary with validation statistics
        """
        total = len(self.validation_log)
        passed = sum(1 for v in self.validation_log if v["is_valid"])
        avg_score = (
            sum(v["overlap_score"] for v in self.validation_log) / total
            if total > 0 else 0.0
        )
        
        return {
            "total_validations": total,
            "passed_count": passed,
            "failed_count": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "average_overlap_score": avg_score,
            "threshold_used": self.overlap_threshold
        }

def main():
    """
    CLI entry point for testing the ReferenceValidatorAgent.
    Demonstrates title-token-overlap check and Constitution II gating.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reference Validator Agent - Validate claims and enforce Constitution II"
    )
    parser.add_argument(
        "--claim-title",
        type=str,
        default="Heterogeneous Scientific Foundation Model Collaboration",
        help="Title of the claim to validate"
    )
    parser.add_argument(
        "--ref-title",
        type=str,
        default="Heterogeneous Scientific Foundation Model Collaboration Benchmark",
        help="Title of the reference paper"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=TITLE_TOKEN_OVERLAP_THRESHOLD,
        help=f"Minimum overlap threshold (default: {TITLE_TOKEN_OVERLAP_THRESHOLD})"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting Reference Validator Agent")
    
    # Initialize agent
    agent = ReferenceValidatorAgent(overlap_threshold=args.threshold)
    
    # Validate claim
    result = agent.validate_claim_reference(args.claim_title, args.ref_title)
    logger.info(f"Validation result: {result}")
    
    # Simulate Constitution II check
    mock_review_data = {
        "peer_review_compliance": True,
        "citation_accuracy": True,
        "claim_verification": True,
        "claims": [
            {"claim_title": args.claim_title, "reference_title": args.ref_title}
        ]
    }
    
    can_contribute, reason = agent.gate_contribution(mock_review_data)
    logger.info(f"Contribution gate: {can_contribute}, reason: {reason}")
    
    # Print summary
    summary = agent.get_validation_summary()
    logger.info(f"Agent summary: {summary}")
    
    if can_contribute:
        print("✅ Contribution approved - Constitution II compliant")
    else:
        print(f"❌ Contribution blocked: {reason}")
        exit(1)

if __name__ == "__main__":
    main()
