"""
Contracts module for PROJ-488-evaluating-the-impact-of-code-generation.

This module defines the formal contracts for data schemas, CLI interfaces,
and validation pre/post-conditions required by the pipeline.
"""
from .data_contracts import (
    CodeSnippetContract,
    MetricScoreContract,
    DatasetGroupContract,
    MetricResultContract
)
from .api_contracts import CLIContract
from .validation_contracts import (
    validate_preconditions,
    validate_postconditions,
    ContractViolationError
)

__all__ = [
    'CodeSnippetContract',
    'MetricScoreContract',
    'DatasetGroupContract',
    'MetricResultContract',
    'CLIContract',
    'validate_preconditions',
    'validate_postconditions',
    'ContractViolationError'
]
