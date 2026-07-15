"""
Contracts module for llmXive pipeline.

This module provides data, API, and validation contracts
to ensure consistency and correctness across the pipeline stages.
"""

from .data_contracts import (
    CodeSnippetContract,
    MetricScoreContract,
    DatasetGroupContract,
    MetricResultContract,
    validate_data_contract
)
from .api_contracts import CLIContract, validate_stage_function_signature
from .validation_contracts import (
    ContractViolationError,
    validate_preconditions,
    validate_postconditions,
    run_contract_check,
    file_exists,
    directory_exists,
    not_empty,
    valid_metric_result,
    sample_count_minimum,
    no_nan_values
)
from .contracts_config import get_contract_config

__all__ = [
    # Data Contracts
    'CodeSnippetContract',
    'MetricScoreContract',
    'DatasetGroupContract',
    'MetricResultContract',
    'validate_data_contract',
    
    # API Contracts
    'CLIContract',
    'validate_stage_function_signature',
    
    # Validation Contracts
    'ContractViolationError',
    'validate_preconditions',
    'validate_postconditions',
    'run_contract_check',
    'file_exists',
    'directory_exists',
    'not_empty',
    'valid_metric_result',
    'sample_count_minimum',
    'no_nan_values',
    
    # Configuration
    'get_contract_config'
]
