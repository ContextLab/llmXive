"""
AST-based clone detection module for computing clone density in Python files.
Uses only Python standard library (ast module) - no external dependencies.
"""
import ast
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration for the ast_cloner module.

    Args:
        log_file: Optional path to log file
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('ast_cloner')
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

    return logger


def parse_python_file(file_path: Path) -> Optional[ast.AST]:
    """
    Parse a Python file and return its AST.

    Args:
        file_path: Path to the Python file

    Returns:
        AST object if successful, None if parsing fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
        return tree
    except SyntaxError as e:
        logging.getLogger('ast_cloner').warning(f"Syntax error in {file_path}: {e}")
        return None
    except Exception as e:
        logging.getLogger('ast_cloner').error(f"Failed to parse {file_path}: {e}")
        return None


def extract_function_nodes(tree: ast.AST) -> List[ast.FunctionDef]:
    """
    Extract all function definition nodes from an AST.

    Args:
        tree: AST object

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
    Extract all class definition nodes from an AST.

    Args:
        tree: AST object

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
    Compute a deterministic hash of an AST node based on its structure.

    Args:
        node: AST node to hash

    Returns:
        Hex string hash of the node structure
    """
    try:
        # Use ast.unparse if available (Python 3.9+), otherwise use ast.dump
        if hasattr(ast, 'unparse'):
            node_code = ast.unparse(node)
        else:
            node_code = ast.dump(node)
        return hashlib.sha256(node_code.encode('utf-8')).hexdigest()
    except Exception:
        # Fallback to dump for older Python versions
        node_code = ast.dump(node)
        return hashlib.sha256(node_code.encode('utf-8')).hexdigest()


def compute_clone_density(tree: ast.AST) -> Dict[str, Any]:
    """
    Compute clone density metrics for an AST.

    Clone density is calculated as:
    - Number of unique function hashes / Total number of functions
    - Number of unique class hashes / Total number of classes
    - Overall uniqueness ratio

    Args:
        tree: AST object

    Returns:
        Dictionary with clone density metrics
    """
    functions = extract_function_nodes(tree)
    classes = extract_class_nodes(tree)

    # Compute hashes for functions
    function_hashes = [compute_node_hash(func) for func in functions]
    unique_function_hashes = set(function_hashes)

    # Compute hashes for classes
    class_hashes = [compute_node_hash(cls) for cls in classes]
    unique_class_hashes = set(class_hashes)

    # Calculate clone density (1.0 = all unique, 0.0 = all duplicated)
    total_functions = len(functions)
    total_classes = len(classes)
    total_nodes = total_functions + total_classes
    unique_nodes = len(unique_function_hashes) + len(unique_class_hashes)

    if total_nodes == 0:
        clone_density = 1.0  # No code = fully unique (edge case)
    else:
        clone_density = unique_nodes / total_nodes

    return {
        'total_functions': total_functions,
        'unique_functions': len(unique_function_hashes),
        'total_classes': total_classes,
        'unique_classes': len(unique_class_hashes),
        'clone_density': round(clone_density, 6),
        'duplicate_functions': total_functions - len(unique_function_hashes),
        'duplicate_classes': total_classes - len(unique_class_hashes)
    }


def compute_clone_density_batch(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Compute clone density for multiple files.

    Args:
        file_paths: List of file paths to analyze

    Returns:
        List of dictionaries with clone density metrics per file
    """
    results = []
    logger = logging.getLogger('ast_cloner')

    for file_path in file_paths:
        tree = parse_python_file(file_path)
        if tree is None:
            results.append({
                'file_path': str(file_path),
                'clone_density': None,
                'total_functions': 0,
                'unique_functions': 0,
                'total_classes': 0,
                'unique_classes': 0,
                'error': 'parse_failed'
            })
        else:
            metrics = compute_clone_density(tree)
            metrics['file_path'] = str(file_path)
            results.append(metrics)
            logger.info(f"Processed {file_path}: clone_density={metrics['clone_density']}")

    return results


def save_clone_metrics(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save clone metrics results to a CSV file.

    Args:
        results: List of metric dictionaries
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'file_path', 'clone_density', 'total_functions', 'unique_functions',
        'total_classes', 'unique_classes', 'duplicate_functions', 'duplicate_classes',
        'error', 'timestamp'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for result in results:
            result['timestamp'] = datetime.now().isoformat()
            writer.writerow(result)

    logging.getLogger('ast_cloner').info(f"Saved clone metrics to {output_path}")


def main():
    """
    Main entry point for command-line usage.
    Parses --input and --output arguments to process files and save results.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Compute clone density for Python files using AST analysis'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input file or directory path (CSV with file_list column or directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output CSV path for clone metrics'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Optional log file path'
    )

    args = parser.parse_args()

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None
    logger = setup_logging(log_file)
    logger.info(f"Starting clone density computation")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")

    # Parse input
    input_path = Path(args.input)
    output_path = Path(args.output)

    file_paths = []

    if input_path.suffix == '.csv':
        # Read file list from CSV
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'file_path' in row:
                    file_paths.append(Path(row['file_path']))
                elif 'file_list' in row:
                    file_paths.append(Path(row['file_list']))
        logger.info(f"Loaded {len(file_paths)} files from CSV")
    elif input_path.is_dir():
        # Scan directory for Python files
        file_paths = list(input_path.rglob('*.py'))
        logger.info(f"Found {len(file_paths)} Python files in directory")
    elif input_path.is_file():
        # Single file
        file_paths = [input_path]
        logger.info(f"Processing single file: {input_path}")
    else:
        logger.error(f"Invalid input path: {input_path}")
        sys.exit(1)

    if not file_paths:
        logger.warning("No files to process")
        # Still create empty output file
        save_clone_metrics([], output_path)
        return

    # Compute clone density
    results = compute_clone_density_batch(file_paths)

    # Save results
    save_clone_metrics(results, output_path)

    logger.info(f"Clone density computation complete. Results saved to {output_path}")


if __name__ == '__main__':
    main()