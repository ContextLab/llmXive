import logging
from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("tree_sitter_python not installed. Comment extraction will be limited.")

# Global parser instance to avoid re-initialization overhead
_parser: Optional[Parser] = None
_language: Optional[Language] = None

def _get_parser() -> Parser:
    """Initialize and return a singleton tree-sitter parser for Python."""
    global _parser, _language
    if not TREE_SITTER_AVAILABLE:
        raise RuntimeError("tree_sitter_python is not installed. Cannot initialize parser.")
    
    if _parser is None or _language is None:
        # Initialize the language and parser
        # tree_sitter_python provides a language() function that returns a Language instance
        # We need to wrap it in the tree_sitter.Language constructor if it's not already one
        # However, tree_sitter_python.language() usually returns the correct C object directly
        # or a wrapper that works with tree_sitter.Language.
        # Standard pattern for tree-sitter-python:
        try:
            # Attempt to get the language object
            lang_obj = tspython.language()
            # If it's already a Language instance, use it; otherwise wrap it.
            # In most recent versions, tspython.language() returns a Language instance.
            _language = lang_obj
        except Exception as e:
            # Fallback if the API is slightly different or requires a path
            # This block handles cases where the language object needs to be constructed from a .so
            # But typically tree_sitter_python.language() is sufficient.
            # If it fails here, we assume the library is incompatible.
            raise RuntimeError(f"Failed to initialize tree-sitter python language: {e}")
        
        _parser = Parser()
        _parser.set_language(_language)
    
    return _parser

def extract_comments_ast(source_code: str) -> List[Dict[str, Any]]:
    """
    Parse Python source code using tree-sitter to extract comments.
    
    This function isolates comments from string literals and handles syntax errors gracefully.
    It returns a list of dictionaries containing comment metadata.
    
    Args:
        source_code: The Python source code as a string.
        
    Returns:
        A list of dictionaries with keys: 'type', 'text', 'start_line', 'end_line', 'start_col', 'end_col'.
        Returns an empty list if no comments are found or if parsing fails.
    """
    if not source_code:
        return []
    
    if not TREE_SITTER_AVAILABLE:
        logging.error("tree_sitter_python not available. Cannot extract comments via AST.")
        return []

    try:
        parser = _get_parser()
        tree = parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node
        
        comments = []
        
        # Tree-sitter Python grammar typically identifies comments as a specific node type.
        # We traverse the tree to find 'comment' nodes.
        # Note: Depending on the specific tree-sitter grammar version, node type might vary slightly.
        # 'comment' is standard for Python.
        
        for child in root_node.walk():
            if child.type == "comment":
                comment_text = child.text.decode("utf8")
                # Strip the leading '#' if present, though usually the node includes it.
                # We keep the raw text as extracted by the parser.
                
                comments.append({
                    "type": child.type,
                    "text": comment_text,
                    "start_line": child.start_point[0],
                    "end_line": child.end_point[0],
                    "start_col": child.start_point[1],
                    "end_col": child.end_point[1]
                })
        
        return comments

    except Exception as e:
        # Handle syntax errors or other parsing issues gracefully
        logging.warning(f"Failed to parse source code for comments: {e}")
        return []

def extract_comments_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract comments from a specific Python file.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        List of comment dictionaries.
    """
    path = Path(file_path)
    if not path.exists():
        logging.warning(f"File not found: {file_path}")
        return []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            source_code = f.read()
        return extract_comments_ast(source_code)
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return []

def extract_comments_batch(file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract comments from a batch of files.
    
    Args:
        file_paths: List of file paths.
        
    Returns:
        Dictionary mapping file path to list of comments.
    """
    results = {}
    for fp in file_paths:
        comments = extract_comments_from_file(fp)
        results[fp] = comments
    return results

def run_extraction_pipeline(data_dir: str, output_path: str):
    """
    Run the comment extraction pipeline on all Python files in a directory.
    
    This function scans the provided directory for Python files, extracts comments
    using tree-sitter, and saves the results to a JSON file.
    
    Args:
        data_dir: Directory containing Python files to process.
        output_path: Path where the output JSON will be saved.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting comment extraction pipeline for {data_dir}")
    
    python_files = list(Path(data_dir).rglob("*.py"))
    
    if not python_files:
        logger.warning(f"No Python files found in {data_dir}")
        # Create empty output file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return
    
    logger.info(f"Found {len(python_files)} Python files")
    
    all_comments = []
    processed_count = 0
    error_count = 0
    
    for file_path in python_files:
        try:
            comments = extract_comments_from_file(str(file_path))
            all_comments.append({
                "file": str(file_path),
                "comments": comments
            })
            processed_count += 1
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            error_count += 1
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_comments, f, indent=2)
    
    logger.info(f"Extraction complete. Processed: {processed_count}, Errors: {error_count}")
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python extract.py <data_dir> <output_json>")
        sys.exit(1)
    
    data_dir_arg = sys.argv[1]
    output_path_arg = sys.argv[2]
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    run_extraction_pipeline(data_dir_arg, output_path_arg)
