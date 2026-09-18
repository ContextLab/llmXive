"""
Module for calculating code complexity metrics (Cyclomatic Complexity and LOC).
"""
import os
import json
import ast
import tokenize
import io
from pathlib import Path

def calculate_loc(code: str) -> int:
    """
    Calculate Lines of Code (LOC) for a given code string.
    Excludes blank lines and comments.
    """
    if not code:
        return 0
    
    try:
        # Tokenize the code
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
        loc = 0
        for tok in tokens:
            if tok.type == tokenize.NL:
                continue
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.NEWLINE:
                loc += 1
        return loc
    except Exception:
        # Fallback: simple line count minus blanks/comments
        lines = code.split('\n')
        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                count += 1
        return count

def calculate_cyclomatic_complexity(code: str) -> int:
    """
    Calculate Cyclomatic Complexity (CC) for a given code string.
    Based on decision points in the AST.
    """
    if not code:
        return 1
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If code is not valid Python (e.g., diff fragments), return base complexity
        return 1
    
    cc = 1  # Base complexity
    
    for node in ast.walk(tree):
        # Decision points that increment CC
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            cc += 1
        elif isinstance(node, ast.BoolOp):
            # Each 'and'/'or' adds a decision
            cc += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            # List/dict/set comprehensions with conditions
            cc += len(node.ifs)
        elif isinstance(node, ast.Assert):
            cc += 1
    
    return cc

def analyze_diff_complexity(diff_content: str) -> dict:
    """
    Analyze a PR diff content and return complexity metrics.
    
    Args:
        diff_content: The diff/patch string from a PR
        
    Returns:
        Dictionary with 'cyclomatic_complexity' and 'lines_of_code'
    """
    # Preprocess diff: extract only added lines (starting with '+')
    # This avoids counting removed lines or context lines
    added_lines = []
    for line in diff_content.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            # Remove the '+' prefix
            added_lines.append(line[1:])
    
    code_snippet = '\n'.join(added_lines)
    
    loc = calculate_loc(code_snippet)
    cc = calculate_cyclomatic_complexity(code_snippet)
    
    return {
        'cyclomatic_complexity': cc,
        'lines_of_code': loc,
        'raw_diff_length': len(diff_content)
    }

def compute_complexity_for_prs(prs: list) -> list:
    """
    Compute complexity metrics for a list of PR data dictionaries.
    
    Args:
        prs: List of PR dictionaries containing 'diff' or 'patch' fields
        
    Returns:
        List of dictionaries with pr_id and complexity metrics
    """
    results = []
    for pr in prs:
        pr_id = pr.get('pr_id', pr.get('id', 'unknown'))
        diff_content = pr.get('diff', pr.get('patch', ''))
        
        if not diff_content:
            # Try to reconstruct from files if available
            files = pr.get('files', [])
            if isinstance(files, list):
                patches = [f.get('patch', '') for f in files if isinstance(f, dict)]
                diff_content = '\n'.join(patches)
        
        metrics = analyze_diff_complexity(diff_content)
        results.append({
            'pr_id': pr_id,
            **metrics
        })
    
    return results

def main():
    """
    Main entry point for standalone execution.
    Reads from data/raw/ or data/processed/ and outputs complexity metrics.
    """
    logger = None
    try:
        from utils.logging import get_logger, setup_logging
        setup_logging()
        logger = get_logger(__name__)
    except ImportError:
        pass
    
    # Default paths
    project_root = Path(__file__).parent.parent
    input_file = project_root / 'data' / 'processed' / 'prs_labeled.csv'
    
    if logger:
        logger.info(f"Reading PR data from {input_file}")
    
    if not input_file.exists():
        if logger:
            logger.error(f"Input file not found: {input_file}")
        print(f"Error: Input file not found: {input_file}")
        return
    
    # Load PRs
    import csv
    prs = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            prs.append(row)
    
    if logger:
        logger.info(f"Loaded {len(prs)} PRs")
    
    # Compute complexity
    results = compute_complexity_for_prs(prs)
    
    if logger:
        logger.info(f"Computed complexity for {len(results)} PRs")
        logger.info("Complexity metrics calculation completed.")

if __name__ == '__main__':
    main()
