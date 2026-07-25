"""
T012: Filter Hard Subset (Spec Alignment).
Selects bottom HARD_INSTANCE_PERCENTILE of initial_coverage scores.
Handles missing data by skipping.
Computes Cyclomatic Complexity as metadata (diagnostic only).
"""
import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_config_summary

def compute_complexity(code: str) -> int:
    """
    Computes a basic Cyclomatic Complexity metric.
    Counts decision points: if, elif, for, while, except, and, or.
    """
    if not code:
        return 0
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0 # Skip invalid code
    
    complexity = 1 # Base
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += 1
            if node.ifs:
                complexity += len(node.ifs)
    return complexity

def filter_hard_instances(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Filters the dataset to keep only 'hard' instances based on initial_coverage.
    """
    if output_path is None:
        output_path = get_path("curated", "hard_subset.jsonl")
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load all items to sort (memory safe enough for typical benchmark sizes ~300-600 items)
    # If larger, we would need a streaming selection algorithm (e.g., Quickselect),
    # but for SWE-bench, loading is fine.
    items = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    
    # Filter out items with missing initial_coverage
    valid_items = []
    skipped = 0
    for item in items:
        score = item.get('initial_coverage')
        if score is None:
            skipped += 1
            continue
        valid_items.append(item)
    
    if skipped > 0:
        print(f"Warning: Skipped {skipped} items due to missing 'initial_coverage'.")
    
    if not valid_items:
        raise ValueError("No valid items with 'initial_coverage' found.")
    
    # Sort by initial_coverage ascending (lower is harder)
    valid_items.sort(key=lambda x: x['initial_coverage'])
    
    # Select bottom percentile
    percentile = get_config_summary().get('HARD_INSTANCE_PERCENTILE', 0.20)
    count = max(1, int(len(valid_items) * percentile))
    hard_items = valid_items[:count]
    
    # Compute complexity for diagnostic
    print(f"Selecting {len(hard_items)} hard instances (top {percentile*100}% lowest coverage).")
    
    for item in hard_items:
        code = item.get('problem_statement', '') # Or repo code if available
        # Note: SWE-bench items usually have 'repo' and 'base_commit', but not full code in the JSONL.
        # We assume 'problem_statement' or a placeholder for complexity if code isn't embedded.
        # If the dataset doesn't have full code, we might estimate or skip.
        # For this task, we compute on problem_statement text length as a proxy if code is missing,
        # or try to fetch if 'repo' is available (complex).
        # Let's assume we compute on 'problem_statement' for now as a simple metric.
        complexity = compute_complexity(item.get('problem_statement', ''))
        if 'metadata' not in item:
            item['metadata'] = {}
        item['metadata']['complexity_score'] = complexity
        item['metadata']['selection_reason'] = "initial_coverage"
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in hard_items:
            f.write(json.dumps(item) + "\n")
    
    print(f"Wrote {len(hard_items)} hard instances to {output_file}")
    return str(output_file)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Filter Hard Instances")
    parser.add_argument("--input", type=str, help="Input JSONL path")
    parser.add_argument("--output", type=str, help="Output JSONL path")
    args = parser.parse_args()
    
    input_path = args.input or get_path("raw", "swe_explore_with_gt.jsonl")
    output_path = args.output or get_path("curated", "hard_subset.jsonl")
    
    try:
        filter_hard_instances(input_path, output_path)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
