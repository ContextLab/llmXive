"""
Metrics calculation utilities using Radon.

Wrappers for Cyclomatic, Halstead, and Cognitive complexity calculations
with robust error handling for invalid syntax.
"""

import ast
from typing import Dict, Any, Optional, List, Tuple

from radon.complexity import cc_visit, cc_visit_ast
from radon.halstead import HalsteadMetrics
from radon.cognitive import cognitive_complexity


class MetricsCalculationError(Exception):
    """Custom exception for metric calculation failures."""
    pass


def validate_code_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that the provided code string is syntactically valid Python.
    
    Args:
        code: The code string to validate.
        
    Returns:
        A tuple (is_valid, error_message).
        If is_valid is True, error_message is None.
        If is_valid is False, error_message contains the syntax error details.
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def calculate_cyclomatic_complexity(code: str) -> float:
    """
    Calculate the Cyclomatic Complexity (McCabe) of the provided code.
    
    Args:
        code: The Python code string.
        
    Returns:
        The total cyclomatic complexity score.
        
    Raises:
        MetricsCalculationError: If the code is invalid or calculation fails.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
    
    try:
        # cc_visit returns a list of results for each function/class
        # We sum the complexity of all functions in the code
        results = cc_visit(code)
        if not results:
            # If no functions found (e.g., just a script), complexity is 1
            return 1.0
        
        total_complexity = sum(r.complexity for r in results)
        return float(total_complexity)
    except Exception as e:
        raise MetricsCalculationError(f"Failed to calculate cyclomatic complexity: {str(e)}")


def calculate_halstead_metrics(code: str) -> Dict[str, float]:
    """
    Calculate Halstead Complexity Metrics for the provided code.
    
    Args:
        code: The Python code string.
        
    Returns:
        A dictionary containing Halstead metrics:
        - n1: Number of unique operators
        - n2: Number of unique operands
        - N1: Total number of operators
        - N2: Total number of operands
        - Length: Program length
        - Estimated Length: Estimated program length
        - Volume: Program volume
        - Difficulty: Program difficulty
        - Effort: Program effort
        - Time: Time required to program
        - Bugs: Estimated number of delivered bugs
        
    Raises:
        MetricsCalculationError: If the code is invalid or calculation fails.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
    
    try:
        # HalsteadMetrics expects a string of code
        metrics = HalsteadMetrics(code)
        
        return {
            "n1": float(metrics.n1),
            "n2": float(metrics.n2),
            "N1": float(metrics.N1),
            "N2": float(metrics.N2),
            "length": float(metrics.length),
            "estimated_length": float(metrics.estimated_length),
            "volume": float(metrics.volume),
            "difficulty": float(metrics.difficulty),
            "effort": float(metrics.effort),
            "time": float(metrics.time),
            "bugs": float(metrics.bugs)
        }
    except Exception as e:
        raise MetricsCalculationError(f"Failed to calculate Halstead metrics: {str(e)}")


def calculate_cognitive_complexity(code: str) -> float:
    """
    Calculate Cognitive Complexity of the provided code.
    
    Cognitive complexity is a measure of how hard code is to understand.
    Unlike cyclomatic complexity, it gives higher weight to nested structures.
    
    Args:
        code: The Python code string.
        
    Returns:
        The cognitive complexity score.
        
    Raises:
        MetricsCalculationError: If the code is invalid or calculation fails.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
    
    try:
        # cognitive_complexity function from radon.cognitive
        score = cognitive_complexity(code)
        return float(score)
    except Exception as e:
        raise MetricsCalculationError(f"Failed to calculate cognitive complexity: {str(e)}")


def calculate_all_metrics(code: str) -> Dict[str, Any]:
    """
    Calculate all complexity metrics (Cyclomatic, Halstead, Cognitive) for the code.
    
    Args:
        code: The Python code string.
        
    Returns:
        A dictionary containing all calculated metrics:
        - cyclomatic_complexity: float
        - cognitive_complexity: float
        - halstead: dict (Halstead metrics)
        
    Raises:
        MetricsCalculationError: If any metric calculation fails.
    """
    # Validate syntax first to avoid repeated checks
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
    
    try:
        cyclomatic = calculate_cyclomatic_complexity(code)
        cognitive = calculate_cognitive_complexity(code)
        halstead = calculate_halstead_metrics(code)
        
        return {
            "cyclomatic_complexity": cyclomatic,
            "cognitive_complexity": cognitive,
            "halstead": halstead
        }
    except MetricsCalculationError:
        # Re-raise the custom exception
        raise
    except Exception as e:
        raise MetricsCalculationError(f"Unexpected error during metrics calculation: {str(e)}")


def get_single_function_metrics(function_node: ast.FunctionDef, 
                                source_code: str) -> Dict[str, Any]:
    """
    Calculate metrics for a specific function node extracted from source code.
    
    Args:
        function_node: An ast.FunctionDef node.
        source_code: The full source code string (needed for radon).
        
    Returns:
        A dictionary with metrics for this specific function.
        
    Raises:
        MetricsCalculationError: If metrics cannot be calculated.
    """
    try:
        # Extract the function source code
        function_source = ast.get_source_segment(source_code, function_node)
        if function_source is None:
            # Fallback: reconstruct from AST if get_source_segment fails
            function_source = ast.unparse(function_node)
        
        return calculate_all_metrics(function_source)
    except MetricsCalculationError:
        raise
    except Exception as e:
        raise MetricsCalculationError(f"Failed to extract function metrics: {str(e)}")