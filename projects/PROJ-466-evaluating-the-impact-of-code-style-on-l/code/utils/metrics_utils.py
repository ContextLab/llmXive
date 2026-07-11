import ast
import logging
from typing import List, Optional, Tuple, Any
from utils.logger import log_generation_error

logger = logging.getLogger(__name__)

def safe_parse_ast(code: str, task_id: str = "", style: str = "") -> Optional[ast.AST]:
    """
    Safely parse code into an AST, returning None if parsing fails.
    
    Args:
        code: The code string to parse
        task_id: Optional task ID for logging
        style: Optional style for logging
        
    Returns:
        AST object or None if parsing fails
    """
    try:
        return ast.parse(code)
    except SyntaxError as e:
        log_generation_error(task_id, style, f"SyntaxError: {e}")
        return None
    except Exception as e:
        log_generation_error(task_id, style, f"Unexpected error parsing AST: {e}")
        return None

def detect_zero_variance(values: List[float], task_id: str = "", style: str = "") -> bool:
    """
    Detect if a list of values has zero variance (all identical).
    
    Args:
        values: List of numeric values
        task_id: Optional task ID for logging
        style: Optional style for logging
        
    Returns:
        True if all values are identical, False otherwise
    """
    if len(values) < 2:
        return True
    
    unique_values = set(values)
    is_zero_variance = len(unique_values) == 1
    
    if is_zero_variance:
        logger.warning(
            f"Zero variance detected: Task {task_id} ({style}) "
            f"has {len(values)} identical values"
        )
    
    return is_zero_variance
