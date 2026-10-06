import logging
from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path
import tree_sitter_python as tspython
import tree_sitter as ts

from utils import configure_logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Initialize Tree-sitter parser once
_parser = ts.Parser()
_parser.set_language(tspython.language())

def extract_comments_ast(source_code: str) -> List[Dict[str, Any]]:
    """
    Parse Python source code using tree-sitter and extract comments.
    Handles empty files and syntax errors gracefully.

    Args:
        source_code (str): The Python source code to parse.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing comment text,
                             start line, end line, and type.
    """
    if not source_code or not source_code.strip():
        return []

    try:
        tree = _parser.parse(bytes(source_code, "utf8"))
    except Exception as e:
        logger.warning(f"Tree-sitter parse error: {e}. Skipping file.")
        return []

    comments = []
    root_node = tree.root_node

    # Tree-sitter Python grammar nodes for comments
    # We traverse the tree looking for 'comment' nodes
    for node in root_node.walk():
        if node.type == "comment":
            comment_text = node.text.decode("utf8").strip()
            # Remove the '#' prefix if present, though usually text includes it
            if comment_text.startswith("#"):
                comment_text = comment_text[1:].strip()
            
            comments.append({
                "text": comment_text,
                "start_line": node.start_point[0] + 1, # 1-based
                "end_line": node.end_point[0] + 1,
                "type": "line_comment"
            })
    
    # Note: Tree-sitter Python doesn't typically expose docstrings as 'comment' nodes
    # but as 'string' nodes. If docstrings are required, we would need to traverse
    # 'simple_statement' -> 'expression_statement' -> 'string' and check if it's a docstring.
    # For now, sticking to explicit comments as per strict interpretation of 'comment' nodes.
    
    return comments

def extract_comments_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read a Python file and extract comments using AST.

    Args:
        file_path (str): Path to the Python file.

    Returns:
        List[Dict[str, Any]]: List of extracted comments.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    return extract_comments_ast(source_code)

def extract_comments_batch(file_paths: List[str], output_dir: str = "data/processed") -> int:
    """
    Extract comments from a batch of files and save to a single JSON file.

    Args:
        file_paths (List[str]): List of file paths to process.
        output_dir (str): Directory to save the output JSON.

    Returns:
        int: Number of files successfully processed.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / "comments.json"

    all_comments = []
    processed_count = 0

    for file_path in file_paths:
        comments = extract_comments_from_file(file_path)
        if comments:
            # Annotate with source file
            for c in comments:
                c["source_file"] = str(file_path)
            all_comments.extend(comments)
            processed_count += 1
        else:
            logger.debug(f"No comments found in {file_path}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_comments, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(all_comments)} comments from {processed_count} files to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write output file {output_file}: {e}")
        return 0

    return processed_count

def run_extraction_pipeline(repos_dir: str = "data/raw", output_dir: str = "data/processed") -> None:
    """
    Main pipeline function to find all Python files in cloned repos and extract comments.

    Args:
        repos_dir (str): Base directory containing cloned repositories.
        output_dir (str): Directory to save the output JSON.
    """
    logger.info(f"Starting comment extraction pipeline for {repos_dir}")
    python_files = []

    repos_path = Path(repos_dir)
    if not repos_path.exists():
        logger.error(f"Repository directory not found: {repos_dir}")
        return

    # Walk through all cloned repos to find .py files
    for repo in repos_path.iterdir():
        if repo.is_dir():
            for py_file in repo.rglob("*.py"):
                python_files.append(str(py_file))

    logger.info(f"Found {len(python_files)} Python files to process.")
    
    if not python_files:
        logger.warning("No Python files found in the repository directory.")
        # Create an empty output file to satisfy the requirement of producing the artifact
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(output_dir) / "comments.json", "w") as f:
            json.dump([], f)
        return

    # Process in batches to avoid memory issues if list is huge
    # For simplicity, we pass the whole list to the batch function which iterates
    # In a real heavy load scenario, we might chunk this list.
    extract_comments_batch(python_files, output_dir)

def main():
    """Entry point for script execution."""
    configure_logging()
    # Default paths can be overridden by environment variables or arguments in a more complex setup
    run_extraction_pipeline()

if __name__ == "__main__":
    main()
