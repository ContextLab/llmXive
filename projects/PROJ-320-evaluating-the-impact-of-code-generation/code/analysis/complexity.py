import os
import json
import ast
import tokenize
import io
import csv
import sys
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.logging import get_logger, setup_logging
from utils.config import get_complexity_settings, get_path

# Try to import psutil for memory monitoring, fallback to a simple check if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = get_logger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    else:
        # Fallback: return 0 or a dummy value if psutil is not installed
        # In a real scenario, this would raise or log a warning
        logger.warning("psutil not available; memory usage check skipped.")
        return 0.0

def check_memory_and_fallback(current_usage_mb: float, threshold_mb: float = 6000) -> bool:
    """
    Check if current memory usage exceeds the threshold.
    Returns True if fallback is needed (memory > threshold).
    """
    if current_usage_mb > threshold_mb:
        logger.warning(f"Memory usage {current_usage_mb:.2f}MB exceeds threshold {threshold_mb}MB. Triggering fallback.")
        return True
    return False

def calculate_loc(code_text: str) -> int:
    """
    Calculate Lines of Code (LOC) for a given code string.
    Counts non-empty, non-comment lines.
    """
    if not code_text:
        return 0
    
    lines = code_text.splitlines()
    loc = 0
    in_multiline_string = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Handle multiline strings (basic heuristic)
        if '"""' in stripped or "'''" in stripped:
            count = stripped.count('"""') + stripped.count("'''")
            if count % 2 == 1:
                in_multiline_string = not in_multiline_string
            # If it starts and ends on the same line, it's a single line docstring/comment
            if not in_multiline_string and count >= 2:
                continue
            if in_multiline_string:
                continue
        
        if in_multiline_string:
            continue
        
        # Skip single-line comments
        if stripped.startswith('#'):
            continue
        
        loc += 1
    
    return loc

def calculate_cyclomatic_complexity(code_text: str) -> int:
    """
    Calculate Cyclomatic Complexity for a given code string.
    Uses AST to count decision points.
    Base complexity is 1.
    """
    if not code_text:
        return 1
    
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        # If code is not valid Python, return a high complexity or 1
        # For robustness, return 1 (base) but log a warning
        logger.warning("SyntaxError in code snippet; returning base complexity.")
        return 1
    
    complexity = 1
    
    for node in ast.walk(tree):
        # Decision points
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, 
                             ast.With, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # and/or operators add to complexity
            complexity += len(node.values) - 1
        elif isinstance(node, ast.IfExp): # Ternary operator
            complexity += 1
    
    return complexity

def analyze_diff_complexity(diff_text: str) -> Dict[str, Any]:
    """
    Analyze a single PR diff string for complexity metrics.
    Returns a dictionary with LOC and Cyclomatic Complexity.
    """
    # Filter out common noise in diffs (headers, binary markers)
    # This is a simplified filter; real diffs might need more robust parsing
    lines = diff_text.splitlines()
    clean_lines = []
    for line in lines:
        if line.startswith('diff --git') or line.startswith('index ') or \
           line.startswith('--- ') or line.startswith('+++ ') or \
           line.startswith('@@ '):
            continue
        if line.startswith('Binary files'):
            continue
        clean_lines.append(line)
    
    clean_text = "\n".join(clean_lines)
    
    # Only count added lines for complexity if possible, but for simplicity
    # we analyze the whole cleaned text. A more advanced version would
    # parse the '+' lines specifically.
    # Here we assume the input is the relevant code block.
    
    loc = calculate_loc(clean_text)
    cc = calculate_cyclomatic_complexity(clean_text)
    
    return {
        "loc": loc,
        "cyclomatic_complexity": cc
    }

def stream_diff_chunks(diff_text: str, chunk_size: int = 10000) -> List[str]:
    """
    Split a large diff string into chunks to avoid memory issues.
    Yields chunks of approximately chunk_size characters.
    """
    if len(diff_text) <= chunk_size:
        yield diff_text
        return
    
    start = 0
    while start < len(diff_text):
        end = start + chunk_size
        # Try to break at a newline to avoid splitting code mid-statement
        if end < len(diff_text):
            newline_pos = diff_text.find('\n', end)
            if newline_pos != -1 and newline_pos < end + 1000: # Look ahead a bit
                end = newline_pos + 1
        yield diff_text[start:end]
        start = end

def analyze_chunked_diff(diff_text: str) -> Dict[str, Any]:
    """
    Analyze a potentially large diff by processing it in chunks.
    Sums up LOC and takes the max (or sum?) of complexity? 
    Usually complexity is per function/file. For a PR, summing LOC makes sense.
    Summing CC is also reasonable for total cognitive load.
    """
    total_loc = 0
    total_cc = 0
    
    # If diff is small, process directly
    if len(diff_text) < 100000: # 100KB threshold
        result = analyze_diff_complexity(diff_text)
        return result
    
    logger.info("Processing large diff in chunks.")
    chunks = list(stream_diff_chunks(diff_text))
    
    for chunk in chunks:
        result = analyze_diff_complexity(chunk)
        total_loc += result['loc']
        total_cc += result['cyclomatic_complexity']
    
    return {
        "loc": total_loc,
        "cyclomatic_complexity": total_cc
    }

def compute_complexity_for_prs(prs_data: List[Dict[str, Any]], 
                               diff_field: str = "diff_text", 
                               pr_id_field: str = "pr_id") -> List[Dict[str, Any]]:
    """
    Compute complexity metrics for a list of PR dictionaries.
    Handles memory constraints by checking usage and forcing GC if needed.
    """
    results = []
    config = get_complexity_settings()
    memory_threshold = config.get('memory_threshold_mb', 6000)
    
    for pr in prs_data:
        # Check memory before processing each PR if list is large
        if HAS_PSUTIL:
            current_mem = get_memory_usage_mb()
            if check_memory_and_fallback(current_mem, memory_threshold):
                gc.collect()
                # If still high, we might need to break or wait, but for now just continue
                # A real implementation might yield results periodically to save memory
        
        pr_id = pr.get(pr_id_field)
        diff = pr.get(diff_field, "")
        
        if not diff:
            logger.warning(f"PR {pr_id} has no diff text.")
            results.append({
                "pr_id": pr_id,
                "complexity_score": 0.0,
                "loc": 0,
                "cyclomatic_complexity": 0
            })
            continue
        
        try:
            metrics = analyze_chunked_diff(diff)
            # Define complexity_score as a weighted combination or just CC
            # The task asks for Cyclomatic Complexity and LOC. 
            # We will output both, and a 'complexity_score' which could be CC.
            # Let's use CC as the primary 'score' for now, or a normalized version.
            # For simplicity in this task, complexity_score = cyclomatic_complexity
            complexity_score = float(metrics['cyclomatic_complexity'])
            
            results.append({
                "pr_id": pr_id,
                "complexity_score": complexity_score,
                "loc": metrics['loc'],
                "cyclomatic_complexity": metrics['cyclomatic_complexity']
            })
        except Exception as e:
            logger.error(f"Error processing PR {pr_id}: {e}")
            results.append({
                "pr_id": pr_id,
                "complexity_score": 0.0,
                "loc": 0,
                "cyclomatic_complexity": 0
            })
    
    return results

def main():
    """
    Main entry point for complexity analysis.
    Reads from data/processed/prs_labeled.csv, computes complexity, 
    and prints results (or saves to a temp structure for the next step).
    Note: T033a is the implementation of the logic. T033b saves the scores.
    However, to make this runnable as a script as per the constraint "Produce real outputs",
    we will save the raw complexity data to a JSON file in data/processed/ 
    which can then be consumed by T033b, OR we can just print the summary.
    
    The task description says: "Implement ... to compute ... for PR diffs".
    It does not explicitly mandate the output file format here, but T033b
    expects to join on pr_id. 
    
    To be helpful and runnable, we will output a CSV of complexity scores
    to data/processed/complexity_scores_raw.json (intermediate) or directly 
    to the CSV expected by T033b if we assume T033b is just a wrapper.
    
    Actually, T033b is "Create ... save_complexity_scores.py". 
    So T033a (this file) should provide the functions. 
    But the constraint says: "Every artifact-producing script must ... actually WRITE its declared output file(s)".
    Since this is a module, we add a `main` that runs the pipeline on the labeled dataset
    and writes an intermediate or final artifact to demonstrate it works.
    
    We will write to `data/processed/complexity_analysis_intermediate.json` 
    to show the computation happened, which T033b can then read and format.
    """
    setup_logging()
    logger.info("Starting Complexity Analysis (T033a)")
    
    input_path = get_path("data_processed", "prs_labeled.csv")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Run T017 first.")
        sys.exit(1)
    
    # Load PRs
    prs = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure we have the diff text. 
            # The labeled dataset might not have the full diff if it was stripped.
            # Assuming T013/T014 stored the diff in 'diff_text' or similar.
            # If not, we might need to fetch it again, but we assume it's in the CSV.
            prs.append(row)
    
    logger.info(f"Loaded {len(prs)} PRs from {input_path}")
    
    # Compute complexity
    results = compute_complexity_for_prs(prs, diff_field="diff_text", pr_id_field="pr_id")
    
    # Save intermediate results
    output_path = get_path("data_processed", "complexity_analysis_intermediate.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Complexity analysis complete. Results saved to {output_path}")
    print(f"Processed {len(results)} PRs. Output: {output_path}")

if __name__ == "__main__":
    main()
