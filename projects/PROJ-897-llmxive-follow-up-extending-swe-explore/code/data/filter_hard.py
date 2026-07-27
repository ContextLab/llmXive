"""
Filter hard instances based on initial coverage scores.
Implements Spec FR-001: Selection by coverage, not complexity.
"""
import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_config_summary, HARD_INSTANCE_PERCENTILE, COVERAGE_COLUMN_NAME, DATA_CURATED, DATA_RAW

def compute_complexity(source_code: str) -> int:
    """
    Compute cyclomatic complexity of Python source code.
    Uses a simple AST-based counting of decision points.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return 0
    
    complexity = 1  # Base complexity
    
    for node in ast.walk(tree):
        if isinstance(node, (
            ast.If, ast.While, ast.For, ast.ExceptHandler,
            ast.With, ast.Assert, ast.comprehension
        )):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    
    return complexity

def filter_hard_instances(
    input_file: Path,
    output_file: Optional[Path] = None,
    percentile: Optional[float] = None
) -> Path:
    """
    Filter the dataset to keep only the 'hard' instances.
    
    Hard instances are defined as those in the bottom `percentile`
    of `initial_coverage` scores (low coverage = hard).
    
    Args:
        input_file: Path to input JSONL file with coverage scores.
        output_file: Path to output JSONL file. Defaults to data/curated/hard_subset.jsonl.
        percentile: Percentile threshold (0.0 to 1.0). Defaults to config.HARD_INSTANCE_PERCENTILE.
        
    Returns:
        Path to output file.
        
    Raises:
        ValueError: If coverage column is missing or data is invalid.
    """
    if output_file is None:
        output_file = DATA_CURATED / "hard_subset.jsonl"
    
    if percentile is None:
        percentile = HARD_INSTANCE_PERCENTILE
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # First pass: collect all records and coverage scores
    records = []
    coverage_scores = []
    
    print(f"Reading input file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                record = json.loads(line)
                coverage = record.get(COVERAGE_COLUMN_NAME)
                
                if coverage is None:
                    print(f"Warning: Skipping record {record.get('instance_id', 'unknown')} - missing {COVERAGE_COLUMN_NAME}")
                    continue
                
                record['metadata'] = record.get('metadata', {})
                record['metadata']['complexity_score'] = compute_complexity(
                    record.get('source_code', '')
                )
                
                records.append(record)
                coverage_scores.append(coverage)
            except json.JSONDecodeError:
                continue
    
    if not records:
        raise ValueError("No valid records found in input file.")
    
    # Calculate threshold
    sorted_scores = sorted(coverage_scores)
    threshold_idx = int(len(sorted_scores) * percentile)
    if threshold_idx == 0:
        threshold_idx = 1  # Ensure at least one record
    
    threshold = sorted_scores[threshold_idx - 1]
    
    print(f"Coverage threshold for hard instances (bottom {percentile*100:.1f}%): {threshold}")
    
    # Second pass: filter records
    hard_records = [r for r in records if r.get(COVERAGE_COLUMN_NAME, float('inf')) <= threshold]
    
    print(f"Selected {len(hard_records)} hard instances out of {len(records)} total.")
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in hard_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"Hard subset saved to: {output_file}")
    return output_file

def main():
    """Entry point for the filter hard script."""
    print("Starting hard instance filtering...")
    
    input_file = DATA_RAW / "swe_explore_with_gt.jsonl"
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run derive_gt.py first.")
        sys.exit(1)
    
    try:
        output_path = filter_hard_instances(input_file)
        print(f"Filtering complete.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
