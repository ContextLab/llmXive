"""
Reference-Validator Agent for llmXive scientific benchmark.

This module implements a validator agent that checks reference claims
before contributing review points. It enforces:
1. Title-token-overlap >= 0.7 threshold for reference matching
2. Constitution II compliance gating
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)


# Constitution II compliance requirements
CONSTITUTION_II_REQUIREMENTS = {
    "requires_citation": True,
    "requires_verification": True,
    "requires_reproducibility": True,
    "min_token_overlap": 0.7,
    "max_age_days": 365,  # References should be within 1 year unless seminal
}


def compute_title_token_overlap(title1: str, title2: str) -> float:
    """
    Compute the Jaccard similarity (token overlap) between two titles.

    Args:
        title1: First title string
        title2: Second title string

    Returns:
        Float between 0.0 and 1.0 representing token overlap ratio
    """
    # Normalize and tokenize
    def tokenize(text: str) -> Set[str]:
        # Lowercase, remove punctuation, split on whitespace
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = set(text.split())
        # Remove common stop words that don't add semantic value
        stop_words = {'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from'}
        return tokens - stop_words

    tokens1 = tokenize(title1)
    tokens2 = tokenize(title2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return len(intersection) / len(union)


def validate_reference_claim(claim: Dict[str, Any], reference_db: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a scientific claim against a reference database.

    Args:
        claim: Dictionary containing claim details with 'title' and 'source'
        reference_db: List of reference dictionaries with 'title', 'url', 'verified'

    Returns:
        Tuple of (is_valid, validation_details)
    """
    claim_title = claim.get('title', '')
    validation_details = {
        'claim_title': claim_title,
        'matched_reference': None,
        'overlap_score': 0.0,
        'constitution_compliant': False,
        'issues': []
    }

    if not claim_title:
        validation_details['issues'].append("Claim missing title")
        return False, validation_details

    # Find best matching reference
    best_match = None
    best_score = 0.0

    for ref in reference_db:
        ref_title = ref.get('title', '')
        score = compute_title_token_overlap(claim_title, ref_title)

        if score > best_score:
            best_score = score
            best_match = ref

    validation_details['overlap_score'] = best_score

    # Check threshold
    if best_score < CONSTITUTION_II_REQUIREMENTS['min_token_overlap']:
        validation_details['issues'].append(
            f"Token overlap {best_score:.2f} below threshold {CONSTITUTION_II_REQUIREMENTS['min_token_overlap']}"
        )
        return False, validation_details

    validation_details['matched_reference'] = best_match.get('url', 'unknown')

    # Check Constitution II compliance
    is_compliant = True

    if not best_match.get('verified', False):
        validation_details['issues'].append("Matched reference not verified")
        is_compliant = False

    if 'citation' not in claim:
        validation_details['issues'].append("Claim missing citation")
        is_compliant = False

    validation_details['constitution_compliant'] = is_compliant

    if is_compliant:
        logger.info(f"Claim validated: {claim_title} (overlap: {best_score:.2f})")
    else:
        logger.warning(f"Claim validation failed: {claim_title} - {validation_details['issues']}")

    return is_compliant, validation_details


class ReferenceValidatorAgent:
    """
    Agent that validates references before contributing review points.

    This agent enforces Constitution II compliance by:
    1. Checking title-token-overlap >= 0.7 for reference matching
    2. Verifying claims against a reference database
    3. Blocking non-compliant contributions
    """

    def __init__(self, reference_db_path: Optional[str] = None):
        """
        Initialize the Reference Validator Agent.

        Args:
            reference_db_path: Path to YAML file containing reference database
        """
        self.reference_db: List[Dict[str, Any]] = []
        self.validation_log: List[Dict[str, Any]] = []
        self._load_reference_db(reference_db_path)

    def _load_reference_db(self, db_path: Optional[str]) -> None:
        """Load reference database from file or initialize empty."""
        import yaml

        if db_path:
            try:
                path = Path(db_path)
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        self.reference_db = data.get('references', [])
                    logger.info(f"Loaded {len(self.reference_db)} references from {db_path}")
                else:
                    logger.warning(f"Reference database not found at {db_path}, using empty database")
            except Exception as e:
                logger.error(f"Failed to load reference database: {e}")
                self.reference_db = []
        else:
            # Initialize with common scientific references for benchmark
            self.reference_db = [
                {
                    'title': 'Attention Is All You Need',
                    'url': 'https://arxiv.org/abs/1706.03762',
                    'verified': True,
                    'year': 2017
                },
                {
                    'title': 'BERT Pre-Training of Deep Bidirectional Transformers',
                    'url': 'https://arxiv.org/abs/1810.04805',
                    'verified': True,
                    'year': 2018
                },
                {
                    'title': 'TabPFN: A Transformer That Solves Tabular Problems',
                    'url': 'https://arxiv.org/abs/2207.01848',
                    'verified': True,
                    'year': 2022
                },
                {
                    'title': 'Time Series Transformer for Human Activity Recognition',
                    'url': 'https://arxiv.org/abs/2101.11991',
                    'verified': True,
                    'year': 2021
                }
            ]
            logger.info("Initialized with default reference database")

    def validate(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single claim against the reference database.

        Args:
            claim: Dictionary containing claim details

        Returns:
            Validation result dictionary
        """
        is_valid, details = validate_reference_claim(claim, self.reference_db)

        result = {
            'claim': claim,
            'is_valid': is_valid,
            'details': details,
            'can_contribute': is_valid and details['constitution_compliant']
        }

        self.validation_log.append(result)
        return result

    def validate_batch(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate multiple claims at once.

        Args:
            claims: List of claim dictionaries

        Returns:
            List of validation results
        """
        return [self.validate(claim) for claim in claims]

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validations performed.

        Returns:
            Summary dictionary with counts and statistics
        """
        total = len(self.validation_log)
        valid = sum(1 for v in self.validation_log if v['is_valid'])
        compliant = sum(1 for v in self.validation_log if v['can_contribute'])

        return {
            'total_validations': total,
            'valid_claims': valid,
            'constitution_compliant': compliant,
            'compliance_rate': compliant / total if total > 0 else 0.0,
            'recent_validations': self.validation_log[-10:]  # Last 10 validations
        }

    def add_reference(self, reference: Dict[str, Any]) -> None:
        """
        Add a new reference to the database.

        Args:
            reference: Reference dictionary with title, url, verified fields
        """
        if 'title' not in reference or 'url' not in reference:
            raise ValueError("Reference must have 'title' and 'url' fields")

        self.reference_db.append(reference)
        logger.info(f"Added reference: {reference['title']}")

    def export_validation_report(self, output_path: str) -> None:
        """
        Export validation log to a YAML file.

        Args:
            output_path: Path to output file
        """
        import yaml

        report = {
            'summary': self.get_validation_summary(),
            'validations': self.validation_log
        }

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Exported validation report to {output_path}")


def main():
    """Main entry point for standalone execution."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Reference Validator Agent')
    parser.add_argument('--test', action='store_true', help='Run self-test with sample claims')
    parser.add_argument('--db', type=str, help='Path to reference database YAML')
    parser.add_argument('--output', type=str, help='Path to output validation report')

    args = parser.parse_args()

    # Initialize agent
    agent = ReferenceValidatorAgent(reference_db_path=args.db)

    if args.test:
        # Run self-test with sample claims
        test_claims = [
            {
                'title': 'Attention Is All You Need',
                'source': 'arxiv',
                'citation': 'Vaswani et al., 2017'
            },
            {
                'title': 'BERT Pre-Training of Deep Bidirectional Transformers for Language Understanding',
                'source': 'arxiv',
                'citation': 'Devlin et al., 2018'
            },
            {
                'title': 'Completely Made Up Paper Title That Should Not Match',
                'source': 'unknown',
                'citation': None
            }
        ]

        print("Running self-test with sample claims...")
        results = agent.validate_batch(test_claims)

        for i, result in enumerate(results):
            print(f"\nClaim {i+1}: {result['claim']['title']}")
            print(f"  Valid: {result['is_valid']}")
            print(f"  Overlap Score: {result['details']['overlap_score']:.2f}")
            print(f"  Constitution Compliant: {result['details']['constitution_compliant']}")
            print(f"  Can Contribute: {result['can_contribute']}")
            if result['details']['issues']:
                print(f"  Issues: {', '.join(result['details']['issues'])}")

        summary = agent.get_validation_summary()
        print(f"\nSummary: {summary['valid_claims']}/{summary['total_validations']} valid "
              f"({summary['compliance_rate']:.1%} compliance rate)")

        if args.output:
            agent.export_validation_report(args.output)
            print(f"Report exported to {args.output}")

    else:
        print("Reference Validator Agent initialized.")
        print("Use --test to run self-test or integrate via Python API.")

        # Interactive mode example
        if not args.test:
            sample_claim = {
                'title': 'Attention Is All You Need',
                'source': 'arxiv',
                'citation': 'Vaswani et al., 2017'
            }
            result = agent.validate(sample_claim)
            print(f"\nSample validation result:")
            print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
