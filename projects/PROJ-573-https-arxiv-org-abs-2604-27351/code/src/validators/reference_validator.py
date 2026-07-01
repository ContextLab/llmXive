"""
Reference Validator Agent for llmXive.

Implements Constitution II compliance checks and reference validation
for research contributions, specifically:
1. Title-token-overlap check (>= 0.7 threshold)
2. Blocking gate for Constitution II compliance
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constitution II Compliance Thresholds
TITLE_TOKEN_OVERLAP_THRESHOLD = 0.7
CONSTITUTION_II_REQUIRED_FIELDS = [
    'claim_id',
    'claim_text',
    'source_reference',
    'validation_status',
    'compliance_check'
]


class ReferenceValidatorAgent:
    """
    Agent to validate research references and enforce Constitution II compliance.

    This agent performs:
    - Token overlap analysis between claims and references
    - Constitution II compliance verification
    - Blocking gates for non-compliant contributions
    """

    def __init__(
        self,
        overlap_threshold: float = TITLE_TOKEN_OVERLAP_THRESHOLD,
        constitution_ii_required_fields: Optional[List[str]] = None
    ):
        """
        Initialize the Reference Validator Agent.

        Args:
            overlap_threshold: Minimum token overlap ratio (0.0 to 1.0)
            constitution_ii_required_fields: List of required fields for Constitution II
        """
        self.overlap_threshold = overlap_threshold
        self.required_fields = constitution_ii_required_fields or CONSTITUTION_II_REQUIRED_FIELDS
        self._validation_log: List[Dict[str, Any]] = []

        logger.info(
            f"ReferenceValidatorAgent initialized with threshold={overlap_threshold}"
        )

    def _tokenize(self, text: str) -> Set[str]:
        """
        Tokenize text into lowercase alphanumeric tokens.

        Args:
            text: Input text string

        Returns:
            Set of normalized tokens
        """
        if not text:
            return set()

        # Convert to lowercase and extract alphanumeric tokens
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return set(tokens)

    def calculate_title_token_overlap(
        self,
        title1: str,
        title2: str
    ) -> float:
        """
        Calculate Jaccard similarity between token sets of two titles.

        Args:
            title1: First title string
            title2: Second title string

        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        tokens1 = self._tokenize(title1)
        tokens2 = self._tokenize(title2)

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def validate_title_overlap(
        self,
        claim_title: str,
        reference_title: str
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Validate that claim title has sufficient token overlap with reference.

        Args:
            claim_title: Title of the research claim
            reference_title: Title of the reference paper

        Returns:
            Tuple of (is_valid, overlap_score, details_dict)
        """
        overlap_score = self.calculate_title_token_overlap(
            claim_title, reference_title
        )
        is_valid = overlap_score >= self.overlap_threshold

        details = {
            'claim_title': claim_title,
            'reference_title': reference_title,
            'overlap_score': overlap_score,
            'threshold': self.overlap_threshold,
            'is_valid': is_valid,
            'tokens_claim': len(self._tokenize(claim_title)),
            'tokens_reference': len(self._tokenize(reference_title))
        }

        logger.debug(
            f"Title overlap validation: {overlap_score:.3f} "
            f"(threshold={self.overlap_threshold}, valid={is_valid})"
        )

        return is_valid, overlap_score, details

    def check_constitution_ii_compliance(
        self,
        contribution: Dict[str, Any]
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Check if a research contribution meets Constitution II requirements.

        Args:
            contribution: Dictionary containing claim/review data

        Returns:
            Tuple of (is_compliant, missing_fields, details_dict)
        """
        missing_fields = []
        for field in self.required_fields:
            if field not in contribution or contribution[field] is None:
                missing_fields.append(field)

        # Additional checks for specific field validity
        validation_issues = []

        # Check claim_id format (should be non-empty string)
        if 'claim_id' in contribution:
            if not isinstance(contribution['claim_id'], str) or not contribution['claim_id'].strip():
                validation_issues.append("claim_id must be a non-empty string")

        # Check validation_status values
        valid_statuses = ['pending', 'verified', 'rejected', 'flagged']
        if 'validation_status' in contribution:
            if contribution['validation_status'] not in valid_statuses:
                validation_issues.append(
                    f"validation_status must be one of {valid_statuses}"
                )

        is_compliant = len(missing_fields) == 0 and len(validation_issues) == 0

        details = {
            'required_fields': self.required_fields,
            'present_fields': list(contribution.keys()),
            'missing_fields': missing_fields,
            'validation_issues': validation_issues,
            'is_compliant': is_compliant
        }

        logger.info(
            f"Constitution II compliance check: {is_compliant} "
            f"(missing={missing_fields}, issues={validation_issues})"
        )

        return is_compliant, missing_fields, details

    def validate_reference_contribution(
        self,
        claim: Dict[str, Any],
        reference: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform full validation of a reference contribution.

        This is the main entry point for validating a research contribution
        before it can be added to the knowledge base.

        Args:
            claim: The claim/review being submitted
            reference: The reference paper being cited

        Returns:
            Validation result dictionary with all checks and decisions
        """
        logger.info(f"Validating reference contribution for claim: {claim.get('claim_id', 'unknown')}")

        results = {
            'claim_id': claim.get('claim_id', 'unknown'),
            'is_valid': True,
            'blocking_gates': [],
            'checks': {},
            'timestamp': None
        }

        # Check 1: Constitution II Compliance
        is_compliant, missing_fields, compliance_details = self.check_constitution_ii_compliance(claim)
        results['checks']['constitution_ii'] = compliance_details

        if not is_compliant:
            results['blocking_gates'].append(
                f"Constitution II violation: missing fields {missing_fields}"
            )
            results['is_valid'] = False

        # Check 2: Title Token Overlap (if both titles available)
        if 'claim_title' in claim and 'reference_title' in reference:
            is_valid_overlap, overlap_score, overlap_details = self.validate_title_overlap(
                claim['claim_title'],
                reference['reference_title']
            )
            results['checks']['title_overlap'] = overlap_details

            if not is_valid_overlap:
                results['blocking_gates'].append(
                    f"Title overlap {overlap_score:.3f} below threshold {self.overlap_threshold}"
                )
                results['is_valid'] = False
        else:
            results['checks']['title_overlap'] = {
                'skipped': True,
                'reason': 'Missing claim_title or reference_title'
            }

        # Check 3: Required data presence
        if 'claim_text' not in claim or not claim.get('claim_text'):
            results['blocking_gates'].append("claim_text is required")
            results['is_valid'] = False

        if 'source_reference' not in claim or not claim.get('source_reference'):
            results['blocking_gates'].append("source_reference is required")
            results['is_valid'] = False

        # Final decision
        if results['is_valid']:
            logger.info(
                f"Reference contribution VALIDATED: {claim.get('claim_id', 'unknown')}"
            )
        else:
            logger.warning(
                f"Reference contribution BLOCKED: {claim.get('claim_id', 'unknown')}. "
                f"Gates: {results['blocking_gates']}"
            )

        # Record in validation log
        self._validation_log.append(results)

        return results

    def get_validation_log(self) -> List[Dict[str, Any]]:
        """Return the complete validation log."""
        return self._validation_log.copy()

    def clear_validation_log(self) -> None:
        """Clear the validation log."""
        self._validation_log.clear()
        logger.info("Validation log cleared")


def main():
    """
    Main entry point for ReferenceValidatorAgent CLI/testing.

    Demonstrates the validation workflow with sample data.
    """
    logger.info("ReferenceValidatorAgent - Main entry point")

    # Initialize agent
    validator = ReferenceValidatorAgent(
        overlap_threshold=TITLE_TOKEN_OVERLAP_THRESHOLD
    )

    # Sample claim data (simulating a research contribution)
    sample_claim = {
        'claim_id': 'c_ee9dd6c2',
        'claim_text': 'The model achieves 85% accuracy on the benchmark.',
        'claim_title': 'Benchmark Performance Analysis',
        'source_reference': 'https://arxiv.org/abs/2604.27351',
        'validation_status': 'pending',
        'compliance_check': None
    }

    # Sample reference data
    sample_reference = {
        'reference_title': 'Heterogeneous Scientific Foundation Model Collaboration Benchmark',
        'reference_url': 'https://arxiv.org/abs/2604.27351',
        'authors': ['Research Team'],
        'year': 2026
    }

    # Perform validation
    logger.info("Running validation on sample claim...")
    result = validator.validate_reference_contribution(sample_claim, sample_reference)

    # Output results
    print("\n=== Reference Validation Results ===")
    print(f"Claim ID: {result['claim_id']}")
    print(f"Is Valid: {result['is_valid']}")
    print(f"Blocking Gates: {result['blocking_gates']}")
    print(f"Title Overlap Score: {result['checks'].get('title_overlap', {}).get('overlap_score', 'N/A')}")
    print(f"Constitution II Compliant: {result['checks'].get('constitution_ii', {}).get('is_compliant', 'N/A')}")

    if not result['is_valid']:
        print("\n⚠️  CONTRIBUTION BLOCKED - See blocking gates above")
        return 1
    else:
        print("\n✅ CONTRIBUTION VALIDATED - Ready for knowledge base")
        return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
