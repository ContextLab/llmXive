"""
Validation Contracts Module

Defines preconditions, postconditions, and runtime validation
contracts for pipeline stages.

Contracts:
- ContractViolationError: Exception raised when a contract is violated
- validate_preconditions: Check preconditions before execution
- validate_postconditions: Check postconditions after execution
- run_contract_check: Execute a full contract check
- File/Directory existence validators
- Data quality validators (no NaN, minimum counts, etc.)
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..logging_config import get_logger
from ..data_model import MetricResult

logger = get_logger(__name__)


class ContractViolationError(Exception):
    """Exception raised when a contract validation fails."""
    
    def __init__(self, contract_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.contract_name = contract_name
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
        super().__init__(f"[{contract_name}] {message}")


def validate_preconditions(contract_name: str, preconditions: Dict[str, Any]) -> bool:
    """
    Validate preconditions before executing a pipeline stage.
    
    Args:
        contract_name: Name of the contract being validated
        preconditions: Dict of precondition name -> validator function
    
    Returns:
        bool: True if all preconditions pass
    
    Raises:
        ContractViolationError: If any precondition fails
    """
    for name, validator in preconditions.items():
        try:
            if not validator():
                raise ContractViolationError(
                    contract_name,
                    f"Precondition '{name}' failed"
                )
        except Exception as e:
            logger.error(f"Precondition check error for '{name}': {e}")
            raise ContractViolationError(
                contract_name,
                f"Precondition '{name}' raised exception: {str(e)}"
            )
    
    return True


def validate_postconditions(contract_name: str, postconditions: Dict[str, Any]) -> bool:
    """
    Validate postconditions after executing a pipeline stage.
    
    Args:
        contract_name: Name of the contract being validated
        postconditions: Dict of postcondition name -> validator function
    
    Returns:
        bool: True if all postconditions pass
    
    Raises:
        ContractViolationError: If any postcondition fails
    """
    for name, validator in postconditions.items():
        try:
            if not validator():
                raise ContractViolationError(
                    contract_name,
                    f"Postcondition '{name}' failed"
                )
        except Exception as e:
            logger.error(f"Postcondition check error for '{name}': {e}")
            raise ContractViolationError(
                contract_name,
                f"Postcondition '{name}' raised exception: {str(e)}"
            )
    
    return True


def run_contract_check(contract_name: str, preconditions: Dict[str, Any], 
                       postconditions: Dict[str, Any], 
                       execution_func: callable) -> Any:
    """
    Run a full contract check around an execution function.
    
    Args:
        contract_name: Name of the contract
        preconditions: Pre-execution validators
        postconditions: Post-execution validators
        execution_func: Function to execute between checks
    
    Returns:
        The result of execution_func
    
    Raises:
        ContractViolationError: If pre or post conditions fail
    """
    validate_preconditions(contract_name, preconditions)
    
    try:
        result = execution_func()
        validate_postconditions(contract_name, postconditions)
        return result
    except ContractViolationError:
        raise
    except Exception as e:
        logger.error(f"Execution error in contract {contract_name}: {e}")
        raise ContractViolationError(
            contract_name,
            f"Execution failed: {str(e)}"
        )


# File and Directory Validators

def file_exists(path: str) -> bool:
    """Validator: Check if a file exists."""
    exists = os.path.isfile(path)
    if not exists:
        logger.error(f"File does not exist: {path}")
    return exists


def directory_exists(path: str) -> bool:
    """Validator: Check if a directory exists."""
    exists = os.path.isdir(path)
    if not exists:
        logger.error(f"Directory does not exist: {path}")
    return exists


def not_empty(value: Any) -> bool:
    """Validator: Check if a value is not empty."""
    is_empty = not bool(value)
    if is_empty:
        logger.error("Value is empty")
    return not is_empty


def valid_metric_result(result: MetricResult) -> bool:
    """Validator: Check if a MetricResult is valid."""
    from ..data_model import validate_metric_result
    is_valid = validate_metric_result(result)
    if not is_valid:
        logger.error("MetricResult validation failed")
    return is_valid


def sample_count_minimum(data: List[Any], minimum: int) -> bool:
    """Validator: Check if sample count meets minimum requirement."""
    count = len(data)
    if count < minimum:
        logger.error(f"Sample count {count} is below minimum {minimum}")
    return count >= minimum


def no_nan_values(data: List[float]) -> bool:
    """Validator: Check that a list contains no NaN values."""
    import math
    has_nan = any(math.isnan(x) for x in data if isinstance(x, float))
    if has_nan:
        logger.error("Data contains NaN values")
    return not has_nan
