"""
Comment extraction module using tree-sitter.
Parses Python files to isolate comments, handling empty files and syntax errors.
Saves extracted comments to data/processed/comments.json.
"""
import logging
from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

# Initialize tree-sitter parser
PY_LANGUAGE = Language(tspython.language())
PARSER = Parser(PY_LANGUAGE)

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def extract_comments_ast(source_code: str, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse Python source code using tree-sitter and extract all comment nodes.
    
    Args:
        source_code: The raw source code string.
        file_path: Optional path to the file for logging purposes.
        
    Returns:
        A list of dictionaries containing comment text and metadata.
    """
    comments = []
    if not source_code or not source_code.strip():
        logger.debug(f"Empty or whitespace-only source in {file_path or 'unknown'}")
        return comments

    try:
        tree = PARSER.parse(bytes(source_code, "utf8"))
    except Exception as e:
        logger.warning(f"Failed to parse {file_path or 'unknown'}: {e}. Skipping.")
        return comments

    root_node = tree.root_node

    # Tree-sitter Python grammar node type for comments
    comment_type = "comment"

    def traverse(node):
        if node.type == comment_type:
            comment_text = node.text.decode('utf8').strip()
            start_point = node.start_point  # (row, col)
            comments.append({
                "text": comment_text,
                "start_line": start_point[0] + 1,  # 1-based index
                "start_col": start_point[1]
            })
        
        for child in node.children:
            traverse(child)

    traverse(root_node)
    return comments

def extract_comments_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Read a Python file and extract comments using tree-sitter.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        List of extracted comments.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return []

    return extract_comments_ast(source_code, file_path)

def extract_comments_batch(file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract comments from a list of file paths.
    
    Args:
        file_paths: List of paths to Python files.
        
    Returns:
        Dictionary mapping file path to list of comments.
    """
    results = {}
    for f_path in file_paths:
        comments = extract_comments_from_file(f_path)
        results[f_path] = comments
        if comments:
            logger.info(f"Extracted {len(comments)} comments from {f_path}")
        else:
            logger.debug(f"No comments found in {f_path}")
    return results

def run_extraction_pipeline(repo_paths: List[str], output_path: str) -> None:
    """
    Run the full extraction pipeline on a list of repository paths.
    Scans for .py files, extracts comments, and saves to a single JSON file.
    
    Args:
        repo_paths: List of root paths (repositories) to scan.
        output_path: Path to the output JSON file.
    """
    py_files = []
    for repo_root in repo_paths:
        root = Path(repo_root)
        if not root.exists():
            logger.warning(f"Repository path does not exist: {repo_root}")
            continue
        
        # Recursively find all .py files
        found = list(root.rglob("*.py"))
        py_files.extend([str(p) for p in found])

    logger.info(f"Found {len(py_files)} Python files across {len(repo_paths)} repositories.")
    
    if not py_files:
        logger.warning("No Python files found to process.")
        # Ensure output directory exists even if empty
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return

    # Process in batches to avoid memory issues if list is huge
    batch_size = 100
    all_results = {}
    
    for i in range(0, len(py_files), batch_size):
        batch = py_files[i:i+batch_size]
        batch_results = extract_comments_batch(batch)
        all_results.update(batch_results)
    
    # Flatten results for JSON output: list of {file, comments}
    output_data = []
    total_comments = 0
    for file_path, comments in all_results.items():
        output_data.append({
            "file_path": file_path,
            "comments": comments
        })
        total_comments += len(comments)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Extraction complete. Total comments extracted: {total_comments}")
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Entry point for the extraction script.
    Expects repository paths as arguments or uses a default if none provided.
    """
    import sys
    # Default to data/raw if no arguments, but check if it exists
    default_repos = ["data/raw"]
    if not os.path.exists("data/raw"):
        logger.error("Default data/raw directory not found. Please provide repository paths.")
        sys.exit(1)

    repos_to_process = sys.argv[1:] if len(sys.argv) > 1 else default_repos
    output_file = "data/processed/comments.json"

    logger.info(f"Starting extraction pipeline for: {repos_to_process}")
    run_extraction_pipeline(repos_to_process, output_file)

if __name__ == "__main__":
    main()
