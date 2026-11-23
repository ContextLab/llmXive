import ast
from typing import Dict, Any, Optional, List, Tuple
from radon.complexity import cc_visit, cc_visit_ast
from radon.halstead import HalsteadMetrics
from radon.cognitive import cognitive_complexity

class MetricsCalculationError(Exception):
    """Custom exception for metrics calculation errors."""
    pass

def validate_code_syntax(code: str) -> bool:
    """Validate that the code has valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def calculate_cyclomatic_complexity(code: str) -> int:
    """Calculate cyclomatic complexity using radon."""
    try:
        blocks = cc_visit(code)
        if not blocks:
            return 0
        return sum(block.complexity for block in blocks)
    except Exception as e:
        raise MetricsCalculationError(f"Cyclomatic complexity calculation failed: {e}")

def calculate_halstead_metrics(code: str) -> Dict[str, float]:
    """Calculate Halstead metrics using radon."""
    try:
        metrics = HalsteadMetrics(code)
        return {
            'halstead_length': metrics.length,
            'halstead_volume': metrics.volume,
            'halstead_difficulty': metrics.difficulty,
            'halstead_effort': metrics.effort
        }
    except Exception as e:
        raise MetricsCalculationError(f"Halstead metrics calculation failed: {e}")

def calculate_cognitive_complexity(code: str) -> int:
    """Calculate cognitive complexity using radon."""
    try:
        return cognitive_complexity(code)
    except Exception as e:
        raise MetricsCalculationError(f"Cognitive complexity calculation failed: {e}")

def calculate_all_metrics(code: str) -> Dict[str, Any]:
    """Calculate all complexity metrics for a code snippet."""
    if not validate_code_syntax(code):
        raise MetricsCalculationError("Invalid code syntax")
    
    return {
        'cyclomatic': calculate_cyclomatic_complexity(code),
        'halstead': calculate_halstead_metrics(code),
        'cognitive': calculate_cognitive_complexity(code)
    }

def get_single_function_metrics(code: str) -> Dict[str, Any]:
    """Get metrics for a single function."""
    return calculate_all_metrics(code)
