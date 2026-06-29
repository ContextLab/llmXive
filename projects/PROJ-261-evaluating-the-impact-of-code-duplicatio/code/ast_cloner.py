import ast
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def parse_python_file(file_path: str | Path) -> Optional[ast.Module]:
    """
    Parse a Python file and return its AST.
    Handles syntax errors gracefully.
    
    Args:
        file_path: Path to Python file
    
    Returns:
        AST Module or None if parsing fails
    """
    file_path = Path(file_path)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        return ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return None

def extract_function_nodes(tree: ast.Module) -> List[ast.FunctionDef]:
    """
    Extract all function definitions from AST.
    
    Args:
        tree: AST Module
    
    Returns:
        List of FunctionDef nodes
    """
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node)
    return functions

def extract_class_nodes(tree: ast.Module) -> List[ast.ClassDef]:
    """
    Extract all class definitions from AST.
    
    Args:
        tree: AST Module
    
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
    Compute a hash for an AST node based on its structure.
    
    Args:
        node: AST node to hash
    
    Returns:
        SHA-256 hash string
    """
    try:
        node_str = ast.dump(node)
        import hashlib
        return hashlib.sha256(node_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute node hash: {e}")
        return ""

def compute_clone_density(file_path: str | Path) -> Tuple[Optional[float], Optional[str]]:
    """
    Compute clone density for a Python file.
    Clone density = (number of duplicate AST nodes) / (total number of AST nodes)
    
    Args:
        file_path: Path to Python file
    
    Returns:
        Tuple of (clone_density, error_message)
    """
    file_path = Path(file_path)
    
    try:
        tree = parse_python_file(file_path)
        if tree is None:
            return None, f"Failed to parse {file_path}"
        
        # Extract all function and class nodes
        functions = extract_function_nodes(tree)
        classes = extract_class_nodes(tree)
        all_nodes = functions + classes
        
        if not all_nodes:
            return 0.0, None
        
        # Compute hashes for all nodes
        node_hashes = [compute_node_hash(node) for node in all_nodes]
        node_hashes = [h for h in node_hashes if h]  # Filter empty hashes
        
        if not node_hashes:
            return 0.0, None
        
        # Count duplicates
        from collections import Counter
        hash_counts = Counter(node_hashes)
        duplicate_count = sum(count - 1 for count in hash_counts.values() if count > 1)
        
        # Clone density = duplicates / total
        clone_density = duplicate_count / len(node_hashes)
        
        return clone_density, None
        
    except Exception as e:
        logger.error(f"Failed to compute clone density for {file_path}: {e}")
        return None, str(e)

def compute_clone_density_batch(file_paths: List[str | Path]) -> List[Dict[str, Any]]:
    """
    Compute clone density for multiple files.
    
    Args:
        file_paths: List of file paths
    
    Returns:
        List of dictionaries with file_path and clone_density
    """
    results = []
    for file_path in file_paths:
        clone_density, error = compute_clone_density(file_path)
        
        if error:
            logger.warning(f"Error processing {file_path}: {error}")
            results.append({
                'file_path': str(file_path),
                'clone_density': None,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
        else:
            results.append({
                'file_path': str(file_path),
                'clone_density': clone_density,
                'error': None,
                'timestamp': datetime.now().isoformat()
            })
    
    return results

def save_clone_metrics(metrics: List[Dict[str, Any]], output_path: str | Path):
    """
    Save clone metrics to CSV file.
    
    Args:
        metrics: List of metric dictionaries
        output_path: Path to save CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'clone_density', 'error', 'timestamp'])
            writer.writeheader()
            writer.writerows(metrics)
        logger.info(f"Saved {len(metrics)} clone metrics to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save clone metrics to {output_path}: {e}")
        raise

def main():
    """Main entry point for AST cloner."""
    logging.basicConfig(level=logging.INFO)
    
    # Test with sample files
    test_files = [
        "test_file1.py",
        "test_file2.py"
    ]
    
    metrics = compute_clone_density_batch(test_files)
    save_clone_metrics(metrics, "data/processed/clone_metrics.csv")
    print(f"Computed clone density for {len(metrics)} files")

if __name__ == "__main__":
    main()
