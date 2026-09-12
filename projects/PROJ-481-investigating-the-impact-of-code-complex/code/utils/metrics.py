"""
Metrics calculation utilities for code complexity analysis.

Wrappers around Radon library for Cyclomatic, Halstead, and Cognitive complexity.
Includes robust error handling for invalid syntax and edge cases.
"""

import ast
from typing import Dict, Any, Optional, List, Tuple

from radon.complexity import cc_visit, cc_visit_ast
from radon.halstead import HalsteadMetrics
from radon.cognitive import cognitive_complexity


class MetricsCalculationError(Exception):
    """Custom exception for metrics calculation failures."""
    pass


def validate_code_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that the provided code string is valid Python syntax.
    
    Args:
        code: The code string to validate.
        
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not code or not code.strip():
        return False, "Code string is empty"
        
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Unexpected error during syntax validation: {str(e)}"


def calculate_cyclomatic_complexity(code: str) -> float:
    """
    Calculate the Cyclomatic Complexity (McCabe) of the provided code.
    
    Uses radon.complexity to visit the AST and sum up the complexity.
    
    Args:
        code: The code string to analyze.
        
    Returns:
        The total cyclomatic complexity score.
        
    Raises:
        MetricsCalculationError: If the code has invalid syntax.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
        
    try:
        # cc_visit returns a list of ComplexityVisitor objects for each function/class
        # We sum the complexity of all blocks
        complexity_list = cc_visit(code)
        total_complexity = sum(block.complexity for block in complexity_list)
        return float(total_complexity)
    except Exception as e:
        raise MetricsCalculationError(f"Failed to calculate cyclomatic complexity: {str(e)}")


def calculate_halstead_metrics(code: str) -> Dict[str, float]:
    """
    Calculate Halstead Complexity Metrics for the provided code.
    
    Uses radon.halstead.HalsteadMetrics to compute:
    - Program length
    - Vocabulary size
    - Volume
    - Difficulty
    - Effort
    - Time required
    - Bugs estimated
    
    Args:
        code: The code string to analyze.
        
    Returns:
        Dictionary containing Halstead metrics.
        
    Raises:
        MetricsCalculationError: If the code has invalid syntax.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
        
    try:
        # Parse the code to an AST
        tree = ast.parse(code)
        
        # HalsteadMetrics expects an AST node
        metrics = HalsteadMetrics(tree)
        
        return {
            'program_length': float(metrics.length),
            'vocabulary_size': float(metrics.vocabulary),
            'volume': float(metrics.volume),
            'difficulty': float(metrics.difficulty),
            'effort': float(metrics.effort),
            'time': float(metrics.time),
            'bugs': float(metrics.bugs)
        }
    except Exception as e:
        raise MetricsCalculationError(f"Failed to calculate Halstead metrics: {str(e)}")


def calculate_cognitive_complexity(code: str) -> float:
    """
    Calculate the Cognitive Complexity of the provided code.
    
    Uses radon.cognitive to compute the cognitive complexity score,
    which measures how difficult code is to understand.
    
    Args:
        code: The code string to analyze.
        
    Returns:
        The cognitive complexity score.
        
    Raises:
        MetricsCalculationError: If the code has invalid syntax.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
        
    try:
        # Parse the code to an AST
        tree = ast.parse(code)
        
        # Calculate cognitive complexity
        complexity = cognitive_complexity(tree)
        return float(complexity)
    except Exception as e:
        raise MetricsCalculationError(f"Failed to calculate cognitive complexity: {str(e)}")


def calculate_all_metrics(code: str) -> Dict[str, Any]:
    """
    Calculate all complexity metrics (Cyclomatic, Halstead, Cognitive) for the provided code.
    
    Args:
        code: The code string to analyze.
        
    Returns:
        Dictionary containing all calculated metrics.
        
    Raises:
        MetricsCalculationError: If any metric calculation fails.
    """
    is_valid, error_msg = validate_code_syntax(code)
    if not is_valid:
        raise MetricsCalculationError(f"Invalid syntax: {error_msg}")
        
    try:
        # Calculate Cyclomatic Complexity
        cyclomatic = calculate_cyclomatic_complexity(code)
        
        # Calculate Halstead Metrics
        halstead = calculate_halstead_metrics(code)
        
        # Calculate Cognitive Complexity
        cognitive = calculate_cognitive_complexity(code)
        
        return {
            'cyclomatic_complexity': cyclomatic,
            'halstead_metrics': halstead,
            'cognitive_complexity': cognitive,
            'valid_syntax': True
        }
    except MetricsCalculationError:
        raise
    except Exception as e:
        raise MetricsCalculationError(f"Unexpected error during metrics calculation: {str(e)}")


def get_single_function_metrics(code: str) -> Dict[str, Any]:
    """
    Calculate metrics for a single function definition.
    
    This is a convenience wrapper that handles the case where the code
    might be a single function or a snippet containing a single function.
    
    Args:
        code: The code string containing the function.
        
    Returns:
        Dictionary containing all metrics for the function.
        
    Raises:
        MetricsCalculationError: If the code is invalid or metrics cannot be calculated.
    """
    return calculate_all_metrics(code)