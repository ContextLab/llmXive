"""
AST-based clone detection module for computing clone density in Python files.

Uses the built-in ast module to parse Python files and compute clone density
metrics. Handles syntax errors gracefully by logging them and continuing
with other files.
"""
import ast
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import get_clone_thresholds, get_random_seed
from parse_failure_logger import log_parse_failure

# Configure module logger
logger = logging.getLogger(__name__)


def parse_python_file(file_path: Path) -> Optional[ast.AST]:
    """
    Parse a Python file and return its AST.
    
    Args:
        file_path: Path to the Python file to parse
        
    Returns:
        AST object if parsing succeeds, None if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        tree = ast.parse(source_code, filename=str(file_path))
        return tree
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        log_parse_failure(
            file_path=str(file_path),
            error_type="SyntaxError",
            error_message=str(e),
            line_number=e.lineno,
            timestamp=datetime.now().isoformat()
        )
        return None
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        log_parse_failure(
            file_path=str(file_path),
            error_type=type(e).__name__,
            error_message=str(e),
            line_number=None,
            timestamp=datetime.now().isoformat()
        )
        return None


def extract_function_nodes(tree: ast.AST) -> List[ast.FunctionDef]:
    """
    Extract all function definitions from an AST.
    
    Args:
        tree: AST object from parsed Python file
        
    Returns:
        List of FunctionDef nodes
    """
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node)
    return functions


def extract_class_nodes(tree: ast.AST) -> List[ast.ClassDef]:
    """
    Extract all class definitions from an AST.
    
    Args:
        tree: AST object from parsed Python file
        
    Returns:
        List of ClassDef nodes
    """
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node)
    return classes


def compute_node_hash(node: ast.AST) -> str:
    """
    Compute a simple hash for an AST node based on its type and structure.
    
    Args:
        node: AST node to hash
        
    Returns:
        String hash of the node
    """
    node_type = type(node).__name__
    if isinstance(node, ast.FunctionDef):
        # Include function name and number of arguments
        hash_input = f"{node_type}:{node.name}:{len(node.args.args)}"
    elif isinstance(node, ast.ClassDef):
        # Include class name and number of bases
        hash_input = f"{node_type}:{node.name}:{len(node.bases)}"
    elif isinstance(node, ast.Assign):
        # Include number of targets and value type
        hash_input = f"{node_type}:{len(node.targets)}:{type(node.value).__name__}"
    else:
        # Generic hash for other node types
        hash_input = node_type
    
    # Simple hash computation (not cryptographically secure, suitable for clone detection)
    return hex(abs(hash(hash_input)) % (2**32))[2:].zfill(8)


def compute_clone_density(file_path: Path) -> Dict[str, Any]:
    """
    Compute clone density for a Python file.
    
    Clone density is defined as the ratio of duplicate code nodes to total
    code nodes in the file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary with clone density metrics
    """
    tree = parse_python_file(file_path)
    if tree is None:
        return {
            "file_path": str(file_path),
            "clone_density": None,
            "total_nodes": 0,
            "duplicate_nodes": 0,
            "parse_error": True,
            "timestamp": datetime.now().isoformat()
        }
    
    # Extract all relevant nodes
    all_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Assign)):
            all_nodes.append(node)
    
    total_nodes = len(all_nodes)
    if total_nodes == 0:
        return {
            "file_path": str(file_path),
            "clone_density": 0.0,
            "total_nodes": 0,
            "duplicate_nodes": 0,
            "parse_error": False,
            "timestamp": datetime.now().isoformat()
        }
    
    # Compute hashes for all nodes
    node_hashes = [compute_node_hash(node) for node in all_nodes]
    
    # Count duplicates
    hash_counts = {}
    for h in node_hashes:
        hash_counts[h] = hash_counts.get(h, 0) + 1
    
    duplicate_nodes = sum(count - 1 for count in hash_counts.values() if count > 1)
    
    # Clone density = duplicates / total (0 if no duplicates)
    clone_density = duplicate_nodes / total_nodes if total_nodes > 0 else 0.0
    
    return {
        "file_path": str(file_path),
        "clone_density": clone_density,
        "total_nodes": total_nodes,
        "duplicate_nodes": duplicate_nodes,
        "parse_error": False,
        "timestamp": datetime.now().isoformat()
    }


def compute_clone_density_batch(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Compute clone density for multiple Python files.
    
    Args:
        file_paths: List of paths to Python files
        
    Returns:
        List of clone density dictionaries
    """
    results = []
    for file_path in file_paths:
        result = compute_clone_density(file_path)
        results.append(result)
    return results


def save_clone_metrics(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save clone density metrics to a CSV file.
    
    Args:
        metrics: List of clone density dictionaries
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "file_path", "clone_density", "total_nodes", 
        "duplicate_nodes", "parse_error", "timestamp"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)
    
    logger.info(f"Saved {len(metrics)} clone metrics to {output_path}")


def main() -> None:
    """Main entry point for AST cloner script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Default to data directory if no arguments
    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    else:
        input_dir = Path("data/raw")
    
    output_path = Path("data/processed/clone_metrics.csv")
    
    # Find all Python files
    python_files = list(input_dir.rglob("*.py"))
    logger.info(f"Found {len(python_files)} Python files in {input_dir}")
    
    # Compute clone density for all files
    metrics = compute_clone_density_batch(python_files)
    
    # Save results
    save_clone_metrics(metrics, output_path)
    
    # Print summary
    valid_metrics = [m for m in metrics if not m["parse_error"]]
    if valid_metrics:
        avg_density = sum(m["clone_density"] for m in valid_metrics) / len(valid_metrics)
        logger.info(f"Average clone density: {avg_density:.4f}")
        logger.info(f"Files with parse errors: {sum(1 for m in metrics if m['parse_error'])}")


if __name__ == "__main__":
    main()
