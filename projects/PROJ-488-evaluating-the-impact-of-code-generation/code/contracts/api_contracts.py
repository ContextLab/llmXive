"""
API Contracts Module

Defines contracts for CLI interfaces and function signatures
to ensure consistent API usage across the pipeline.

Contracts:
- CLIContract: Validates command-line argument structures
- validate_stage_function_signature: Ensures pipeline stage functions
  have correct signatures
"""

import argparse
from typing import List, Optional, Callable, Any
from pathlib import Path
from ..logging_config import get_logger

logger = get_logger(__name__)


class CLIContract:
    """
    Contract for CLI argument validation.
    
    Defines expected arguments for pipeline stages and validates
    that provided arguments conform to the contract.
    """
    
    def __init__(self, stage_name: str, required_args: List[str], 
                 optional_args: Optional[Dict[str, Any]] = None):
        """
        Initialize a CLI contract.
        
        Args:
            stage_name: Name of the pipeline stage
            required_args: List of required argument names
            optional_args: Dict of optional argument names and their defaults
        """
        self.stage_name = stage_name
        self.required_args = required_args
        self.optional_args = optional_args or {}
    
    def validate(self, args: argparse.Namespace) -> bool:
        """
        Validate parsed CLI arguments against the contract.
        
        Args:
            args: Parsed arguments from argparse
        
        Returns:
            bool: True if valid, False otherwise
        """
        errors = []
        
        # Check required arguments
        for arg in self.required_args:
            if not hasattr(args, arg) or getattr(args, arg) is None:
                errors.append(f"Missing required argument: --{arg}")
        
        # Check optional arguments have correct types if provided
        for arg_name, expected_type in self.optional_args.items():
            if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
                if not isinstance(getattr(args, arg_name), expected_type):
                    errors.append(f"Argument --{arg_name} has wrong type: "
                                  f"expected {expected_type}, got {type(getattr(args, arg_name))}")
        
        if errors:
            for error in errors:
                logger.error(f"CLI Contract violation for {self.stage_name}: {error}")
            return False
        
        return True
    
    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create an ArgumentParser configured with this contract's arguments.
        
        Returns:
            argparse.ArgumentParser: Configured parser
        """
        parser = argparse.ArgumentParser(
            description=f"CLI for {self.stage_name} pipeline stage"
        )
        
        for arg in self.required_args:
            parser.add_argument(
                f"--{arg}",
                required=True,
                help=f"Required argument: {arg}"
            )
        
        for arg_name, default in self.optional_args.items():
            parser.add_argument(
                f"--{arg_name}",
                default=default,
                help=f"Optional argument: {arg_name}"
            )
        
        return parser


def validate_stage_function_signature(func: Callable, expected_params: List[str], 
                                      return_type: Optional[type] = None) -> bool:
    """
    Validate that a pipeline stage function has the expected signature.
    
    Args:
        func: The function to validate
        expected_params: List of expected parameter names (excluding 'self'/'cls')
        return_type: Expected return type (optional)
    
    Returns:
        bool: True if signature matches, False otherwise
    """
    import inspect
    
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    # Filter out 'self' and 'cls' for methods
    filtered_params = [p for p in params if p not in ('self', 'cls')]
    
    # Check if all expected parameters are present
    missing = [p for p in expected_params if p not in filtered_params]
    if missing:
        logger.error(f"Function '{func.__name__}' missing parameters: {missing}")
        return False
    
    # Check for unexpected parameters (optional, but log warning)
    unexpected = [p for p in filtered_params if p not in expected_params]
    if unexpected:
        logger.warning(f"Function '{func.__name__}' has extra parameters: {unexpected}")
    
    # Check return type annotation if specified
    if return_type is not None:
        if sig.return_annotation == inspect.Signature.empty:
            logger.warning(f"Function '{func.__name__}' has no return type annotation")
        elif sig.return_annotation != return_type:
            logger.error(f"Function '{func.__name__}' has wrong return type: "
                         f"expected {return_type}, got {sig.return_annotation}")
            return False
    
    return True
