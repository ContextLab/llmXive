"""AST-based clone detection with comprehensive error handling.

This module parses Python files using the built-in ast module and computes
clone density metrics. It includes robust error handling for syntax errors
and parse failures, logging them to data/parse_failures.csv.

Per Constitution Principle III (Data Hygiene), all parse failures are logged
with context for reproducibility and debugging.
"""
import ast
import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from parse_failure_logger import init_logger, log_parse_failure

# Module-level logger
_logger = None
_lock = threading.Lock()

def _get_logger() -> logging.Logger:
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        with _lock:
            if _logger is None:
                _logger = init_logger("ast_cloner")
    return _logger

def compute_ast_clone_density(code: str) -> Tuple[Optional[float], Optional[str]]:
    """Compute AST-based clone density for a code snippet.

    Clone density is calculated as the ratio of duplicate AST node patterns
    to total AST nodes. Uses structural hashing of AST nodes.

    Args:
        code: Python source code string

    Returns:
        Tuple of (clone_density, error_message). If error, density is None.
    """
    logger = _get_logger()

    if not code or not code.strip():
        logger.warning("Empty or whitespace-only code provided")
        return 0.0, None

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
        logger.error(f"Syntax error parsing code: {error_msg}")
        return None, error_msg
    except Exception as e:
        error_msg = f"AST parsing failed: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

    # Extract all AST nodes
    nodes = list(ast.walk(tree))

    if not nodes:
        return 0.0, None

    # Create structural hashes for each node
    node_hashes = []
    for node in nodes:
        try:
            node_type = type(node).__name__
            # Create a simple structural signature
            if hasattr(node, 'lineno'):
                signature = f"{node_type}:{node.lineno}"
            else:
                signature = node_type
            node_hashes.append(signature)
        except Exception as e:
            logger.warning(f"Could not hash node {type(node).__name__}: {e}")
            continue

    if not node_hashes:
        return 0.0, None

    # Count duplicates
    from collections import Counter
    hash_counts = Counter(node_hashes)
    total_nodes = len(node_hashes)
    duplicate_nodes = sum(count - 1 for count in hash_counts.values() if count > 1)

    if total_nodes == 0:
        return 0.0, None

    clone_density = duplicate_nodes / total_nodes

    # Validate the result
    if clone_density < 0 or clone_density > 1:
        logger.warning(f"Invalid clone density computed: {clone_density}")
        return None, "Invalid clone density value"

    logger.debug(f"Computed clone density: {clone_density:.4f} for {total_nodes} nodes")
    return clone_density, None

def process_file_with_error_handling(
    file_path: Path,
    failure_log_path: Optional[Path] = None
) -> Dict:
    """Process a single Python file with comprehensive error handling.

    This function wraps clone density computation with error handling for:
    - Syntax errors in source files
    - File I/O errors
    - Memory errors during AST parsing
    - Any unexpected exceptions

    Args:
        file_path: Path to the Python file to analyze
        failure_log_path: Optional path to log parse failures (defaults to data/parse_failures.csv)

    Returns:
        Dictionary with file_path, clone_density, error_message, timestamp
    """
    logger = _get_logger()
    timestamp = datetime.now().isoformat()

    # Default failure log path
    if failure_log_path is None:
        failure_log_path = Path("data/parse_failures.csv")

    result = {
        "file_path": str(file_path),
        "clone_density": None,
        "error_message": None,
        "timestamp": timestamp,
        "status": "pending"
    }

    # Check file exists
    if not file_path.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result

    # Check file is readable
    if not file_path.is_file():
        error_msg = f"Not a file: {file_path}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result

    # Check file extension
    if file_path.suffix != ".py":
        logger.debug(f"Skipping non-Python file: {file_path}")
        result["status"] = "skipped"
        return result

    # Read file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except UnicodeDecodeError as e:
        error_msg = f"Unicode decode error: {str(e)}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result
    except PermissionError as e:
        error_msg = f"Permission denied: {str(e)}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result
    except MemoryError as e:
        error_msg = f"Memory error reading file: {str(e)}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result
    except Exception as e:
        error_msg = f"Unexpected I/O error: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        result["error_message"] = error_msg
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result

    # Compute clone density
    clone_density, error = compute_ast_clone_density(code)

    if error:
        result["error_message"] = error
        result["status"] = "failed"
        log_parse_failure(failure_log_path, result)
        return result

    result["clone_density"] = clone_density
    result["status"] = "success"
    result["node_count"] = len(list(ast.walk(ast.parse(code))))

    logger.info(f"Successfully processed {file_path}: clone_density={clone_density:.4f}")
    return result

def process_directory_with_error_handling(
    directory: Path,
    failure_log_path: Optional[Path] = None
) -> List[Dict]:
    """Process all Python files in a directory with error handling.

    Args:
        directory: Root directory to search for Python files
        failure_log_path: Optional path to log parse failures

    Returns:
        List of result dictionaries for all processed files
    """
    logger = _get_logger()
    results = []

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return results

    if not directory.is_dir():
        logger.error(f"Not a directory: {directory}")
        return results

    logger.info(f"Processing directory: {directory}")

    for py_file in directory.rglob("*.py"):
        result = process_file_with_error_handling(py_file, failure_log_path)
        results.append(result)

    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = sum(1 for r in results if r["status"] == "failed")
    skip_count = sum(1 for r in results if r["status"] == "skipped")

    logger.info(
        f"Directory processing complete: {success_count} success, "
        f"{fail_count} failed, {skip_count} skipped"
    )

    return results

def validate_clone_density(density: Optional[float]) -> bool:
    """Validate that clone density is a valid number.

    Checks for:
    - None values
    - NaN values
    - Infinite values
    - Out of range values (< 0 or > 1)

    Args:
        density: Clone density value to validate

    Returns:
        True if valid, False otherwise
    """
    if density is None:
        return False

    import math
    if math.isnan(density):
        return False
    if math.isinf(density):
        return False
    if density < 0 or density > 1:
        return False

    return True
