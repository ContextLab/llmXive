import os
import json
import ast
import tokenize
import io
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.logging import get_logger, setup_logging
from utils.config import get_path

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        logger.warning("psutil not installed, returning 0 for memory usage")
        return 0.0

def check_memory_and_fallback(threshold_mb: float = 6000) -> bool:
    """
    Check if memory usage exceeds threshold and trigger fallback.
    Returns True if fallback should be triggered.
    """
    current_memory = get_memory_usage_mb()
    if current_memory > threshold_mb:
        logger.warning(f"Memory usage {current_memory:.2f}MB exceeds threshold {threshold_mb}MB, triggering fallback")
        return True
    return False

def calculate_loc(code_text: str) -> int:
    """Calculate Lines of Code (LOC) for a code snippet."""
    if not code_text:
        return 0
    
    lines = code_text.split('\n')
    # Count non-empty, non-comment lines
    loc = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            loc += 1
    return loc

def calculate_cyclomatic_complexity(code_text: str) -> int:
    """
    Calculate Cyclomatic Complexity for a code snippet.
    Uses AST-based analysis for Python code.
    """
    if not code_text:
        return 0
    
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        # If parsing fails, use a simple heuristic
        return max(1, code_text.count('\n') // 10)
    
    complexity = 1  # Base complexity
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                           ast.With, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    
    return complexity

def analyze_diff_complexity(diff_text: str) -> float:
    """
    Analyze complexity of a PR diff.
    Returns a normalized complexity score.
    """
    if not diff_text:
        return 0.0
    
    # Extract added lines from diff
    added_lines = []
    for line in diff_text.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])  # Remove the '+' prefix
    
    added_code = '\n'.join(added_lines)
    
    if not added_code.strip():
        return 0.0
    
    # Calculate complexity metrics
    loc = calculate_loc(added_code)
    cyclomatic = calculate_cyclomatic_complexity(added_code)
    
    # Normalize and combine metrics
    # Simple weighted combination: 0.4 * LOC + 0.6 * Cyclomatic
    # Normalize LOC to 0-1 range (assuming max 100 lines)
    normalized_loc = min(loc / 100.0, 1.0)
    normalized_cyclomatic = min(cyclomatic / 10.0, 1.0)
    
    complexity_score = 0.4 * normalized_loc + 0.6 * normalized_cyclomatic
    return float(complexity_score)

def compute_complexity_for_prs(prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compute complexity scores for a list of PRs.
    Returns list of dicts with pr_id and complexity_score.
    """
    results = []
    
    for pr in prs:
        pr_id = pr.get('pr_id')
        if pr_id is None:
            continue
        
        diff_text = pr.get('diff', '')
        if not diff_text:
            # Try to get diff from raw data
            raw_data = pr.get('raw', {})
            diff_text = raw_data.get('diff', '')
        
        complexity_score = analyze_diff_complexity(diff_text)
        
        results.append({
            'pr_id': int(pr_id),
            'complexity_score': float(complexity_score)
        })
    
    return results

def main():
    """Main entry point for complexity analysis."""
    setup_logging()
    
    # Load labeled PRs
    labeled_prs_path = get_path("processed", "prs_labeled.csv")
    if not labeled_prs_path.exists():
        logger.error(f"Labeled PRs file not found: {labeled_prs_path}")
        return
    
    with open(labeled_prs_path, 'r') as f:
        reader = csv.DictReader(f)
        prs = list(reader)
    
    logger.info(f"Loaded {len(prs)} PRs for complexity analysis")
    
    # Check memory before processing
    if check_memory_and_fallback():
        logger.warning("Memory threshold exceeded, using simplified analysis")
        # In a real implementation, we would use a simplified analysis here
    
    # Compute complexity
    results = compute_complexity_for_prs(prs)
    
    # Save results
    output_path = get_path("processed", "complexity_scores.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pr_id', 'complexity_score'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved complexity scores for {len(results)} PRs to {output_path}")

if __name__ == "__main__":
    main()