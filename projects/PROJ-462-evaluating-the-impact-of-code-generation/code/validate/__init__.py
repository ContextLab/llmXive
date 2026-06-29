"""
Validation module for llmXive automated science pipeline.

Implements Constitution Principle II: Reference-Validator Agent
- Validates all external citations before data ingestion/analysis
- Blocks pipeline if citations are unverified
"""

from .citations import (
    CitationValidationResult,
    CitationValidationReport,
    verify_url_accessible,
    verify_checksum,
    verify_required_variables,
    validate_citation,
    validate_citations,
    generate_validation_report
)

__all__ = [
    'CitationValidationResult',
    'CitationValidationReport',
    'verify_url_accessible',
    'verify_checksum',
    'verify_required_variables',
    'validate_citation',
    'validate_citations',
    'generate_validation_report'
]