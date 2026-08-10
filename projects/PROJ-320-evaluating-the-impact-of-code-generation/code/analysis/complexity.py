import os
import json
import ast
import tokenize
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys
import resource

# Import utilities from the project's utility modules
from utils.seeds import set_global_seed
from utils.logging import get_logger
from utils.config import get_config_summary

logger = get_logger(__name__)

# Constants
MEMORY_THRESHOLD_BYTES = 6 * 1024 * 1024 * 1024  # 6GB
FALLBACK_THRESHOLD_BYTES = MEMORY_THRESHOLD_BYTES * 0.9  # Trigger fallback at 90% of threshold for safety

def calculate_loc(source_code: str) -> int:
    """
    Calculate Lines of Code (LOC) for a given source code string.
    Counts non-empty, non-comment lines.
    """
    if not source_code:
        return 0
    
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source_code).readline))
        loc = 0
        for tok in tokens:
            if tok.type == tokenize.NL or tok.type == tokenize.NEWLINE:
                loc += 1
            # Count actual code lines by skipping comments and whitespace-only lines
            # A more robust approach: count lines that are not empty and not purely comments
        # Fallback to simple line counting if tokenization fails or is too slow
        lines = source_code.splitlines()
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        return len(code_lines)
    except Exception as e:
        logger.warning(f"Tokenization failed for LOC calculation: {e}. Using fallback.")
        lines = source_code.splitlines()
        return len([l for l in lines if l.strip() and not l.strip().startswith('#')])

def calculate_cyclomatic_complexity(source_code: str) -> int:
    """
    Calculate Cyclomatic Complexity (CC) for a given source code string.
    Based on decision points in the AST.
    """
    if not source_code:
        return 1  # Base complexity
    
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        logger.warning("Syntax error in source code. Returning base complexity.")
        return 1
    
    complexity = 1  # Base complexity
    
    for node in ast.walk(tree):
        # Count decision points
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += 1
            if node.ifs:
                complexity += len(node.ifs)
    
    return complexity

def analyze_diff_complexity(diff_text: str) -> Dict[str, Any]:
    """
    Analyze complexity of a code diff.
    Extracts added code blocks and calculates metrics.
    """
    if not diff_text:
        return {"loc": 0, "cyclomatic_complexity": 1, "status": "empty"}
    
    added_lines = []
    for line in diff_text.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])  # Remove the '+'
    
    added_code = '\n'.join(added_lines)
    
    if not added_code.strip():
        return {"loc": 0, "cyclomatic_complexity": 1, "status": "no_added_code"}
    
    loc = calculate_loc(added_code)
    cc = calculate_cyclomatic_complexity(added_code)
    
    return {
        "loc": loc,
        "cyclomatic_complexity": cc,
        "status": "analyzed",
        "added_code_sample": added_code[:200] if len(added_code) > 200 else added_code
    }

def compute_complexity_for_prs(pr_data_list: List[Dict[str, Any]], use_fallback: bool = False) -> List[Dict[str, Any]]:
    """
    Compute complexity metrics for a list of PRs.
    Implements fallback logic if memory usage exceeds threshold (Assumption 3).
    
    Args:
        pr_data_list: List of PR dictionaries containing 'diff' or 'patch' data.
        use_fallback: If True, forces fallback to standard metrics regardless of memory.
        
    Returns:
        List of dictionaries with PR ID and complexity scores.
    """
    results = []
    
    # Check memory usage at start
    try:
        current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024  # Convert KB to bytes
        logger.info(f"Current memory usage: {current_memory / (1024*1024):.2f} MB")
    except Exception:
        current_memory = 0
        logger.warning("Could not determine current memory usage.")
    
    fallback_triggered = False
    
    for pr in pr_data_list:
        pr_id = pr.get('id', pr.get('number', 'unknown'))
        
        # Check memory before processing each PR
        if not fallback_triggered:
            try:
                current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
                if current_memory > FALLBACK_THRESHOLD_BYTES or use_fallback:
                    logger.warning(f"Memory threshold exceeded ({current_memory / (1024*1024*1024):.2f} GB). "
                                 "Switching to simplified metrics (Assumption 3).")
                    fallback_triggered = True
            except Exception:
                pass
        
        diff_text = pr.get('diff') or pr.get('patch') or ""
        
        if fallback_triggered:
            # Simplified metrics: just count lines and assume base complexity
            lines = diff_text.splitlines()
            added_lines = [l for l in lines if l.startswith('+') and not l.startswith('+++')]
            loc = len([l for l in added_lines if l.strip()])
            # Fallback: assume complexity proportional to LOC, capped at a reasonable value
            cc = min(loc, 10) if loc > 0 else 1
            
            results.append({
                "pr_id": pr_id,
                "complexity_score": cc,
                "loc": loc,
                "cc": cc,
                "method": "fallback_simplified",
                "status": "success"
            })
            logger.debug(f"PR {pr_id}: Fallback metrics applied (LOC={loc}, CC={cc})")
        else:
            # Full analysis
            analysis = analyze_diff_complexity(diff_text)
            
            # Compute a weighted complexity score
            # Score = CC * (1 + 0.1 * (LOC / 100)) to penalize large files
            if analysis["loc"] > 0:
                complexity_score = analysis["cyclomatic_complexity"] * (1 + 0.1 * (analysis["loc"] / 100))
            else:
                complexity_score = 1.0
            
            results.append({
                "pr_id": pr_id,
                "complexity_score": round(complexity_score, 2),
                "loc": analysis["loc"],
                "cc": analysis["cyclomatic_complexity"],
                "method": "full_ast_analysis",
                "status": "success"
            })
            logger.debug(f"PR {pr_id}: Full analysis (LOC={analysis['loc']}, CC={analysis['cyclomatic_complexity']}, Score={complexity_score:.2f})")
    
    if fallback_triggered:
        logger.warning(f"Full pipeline switched to fallback mode for {len(pr_data_list)} PRs due to memory constraints.")
    
    return results

def main():
    """
    Main entry point for complexity analysis.
    Reads PR data from data/processed/, computes complexity, and saves results.
    """
    # Set up paths
    data_dir = Path("data/processed")
    output_dir = Path("data/processed")
    
    # Find input files
    labeled_file = data_dir / "prs_labeled.csv"
    if not labeled_file.exists():
        logger.error(f"Labeled dataset not found at {labeled_file}. Cannot proceed.")
        return
    
    # Load PR data (simplified CSV loading for demonstration)
    import pandas as pd
    try:
        df = pd.read_csv(labeled_file)
        logger.info(f"Loaded {len(df)} PRs from {labeled_file}")
    except Exception as e:
        logger.error(f"Failed to load PR data: {e}")
        return
    
    # Convert to list of dicts for processing
    pr_data_list = df.to_dict('records')
    
    # Compute complexity
    results = compute_complexity_for_prs(pr_data_list)
    
    # Save results
    output_file = output_dir / "complexity_scores.csv"
    try:
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False)
        logger.info(f"Saved complexity scores to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return
    
    # Summary
    avg_score = result_df['complexity_score'].mean()
    logger.info(f"Average complexity score: {avg_score:.2f}")
    logger.info(f"PRs processed: {len(results)}")

if __name__ == "__main__":
    main()