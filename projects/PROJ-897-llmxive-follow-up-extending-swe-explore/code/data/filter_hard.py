import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_path, HARD_INSTANCE_PERCENTILE, COVERAGE_COLUMN_NAME, DATA_CURATED, DATA_RAW

def compute_complexity(code: str) -> int:
    """
    Compute the cyclomatic complexity of a Python code snippet.
    Returns the number of decision points + 1.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # If code is invalid, return a high complexity or 0 depending on policy.
        # Here we return 0 to avoid crashing, but in a real scenario this might be an error.
        return 0

    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # And/Or add to complexity
            complexity += len(node.values) - 1
    return complexity

def filter_hard_instances(
    input_path: Path,
    output_path: Path,
    percentile: Optional[float] = None,
    coverage_column: str = 'initial_coverage'
) -> List[Dict[str, Any]]:
    """
    Reads a JSONL file, filters for the bottom `percentile` of `coverage_column`.
    Calculates cyclomatic complexity as supplementary metadata.
    Writes the filtered subset to `output_path`.
    Returns the list of filtered records.
    """
    if percentile is None:
        raise ValueError("HARD_INSTANCE_PERCENTILE must be set to filter the hard subset.")

    # Load all records
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                sys.stderr.write(f"Warning: Skipping invalid JSON line in {input_path}\n")
                continue

    if not records:
        raise ValueError(f"No records found in {input_path}")

    # Check if coverage column exists
    if coverage_column not in records[0]:
        raise KeyError(f"Coverage column '{coverage_column}' not found in dataset. Available keys: {list(records[0].keys())}")

    # Sort by coverage column (ascending, assuming lower coverage = harder)
    records.sort(key=lambda x: x.get(coverage_column, 0.0))

    # Calculate cutoff index
    cutoff_index = max(1, int(len(records) * (percentile / 100.0)))
    hard_records = records[:cutoff_index]

    # Enrich with complexity metadata
    enriched_records = []
    for rec in hard_records:
        enriched_rec = dict(rec)
        code = rec.get('code', '')
        if code:
            enriched_rec['cyclomatic_complexity'] = compute_complexity(code)
        else:
            enriched_rec['cyclomatic_complexity'] = 0
        enriched_records.append(enriched_rec)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in enriched_records:
            f.write(json.dumps(rec) + '\n')

    return enriched_records

def main() -> int:
    """
    Main entry point for T012: Filter Hard Subset.
    Reads from data/raw/swe_explore_with_gt.jsonl (or coverage file if specified),
    filters based on HARD_INSTANCE_PERCENTILE, and writes to data/curated/hard_subset.jsonl.
    """
    # Determine input path
    # Priority: T011 output (with GT) -> T011b output (with coverage proxy)
    input_path_raw_gt = get_path(DATA_RAW, 'swe_explore_with_gt.jsonl')
    input_path_coverage = get_path(DATA_RAW, 'swe_explore_with_coverage.jsonl')

    if input_path_raw_gt.exists():
        input_path = input_path_raw_gt
    elif input_path_coverage.exists():
        input_path = input_path_coverage
    else:
        raise FileNotFoundError(
            f"Input file not found. Expected either {input_path_raw_gt} or {input_path_coverage}. "
            "Ensure T011 or T011b has run successfully."
        )

    output_path = get_path(DATA_CURATED, 'hard_subset.jsonl')

    # Get config values
    percentile = HARD_INSTANCE_PERCENTILE
    coverage_col = COVERAGE_COLUMN_NAME

    if percentile is None:
        # Fallback for safety if config is None, though spec says it should be set
        sys.stderr.write("Error: HARD_INSTANCE_PERCENTILE is None. Cannot filter hard subset.\n")
        return 1

    print(f"Filtering hard subset: {percentile}% lowest {coverage_col} from {input_path}")

    try:
        filtered_records = filter_hard_instances(
            input_path,
            output_path,
            percentile=percentile,
            coverage_column=coverage_col
        )
        print(f"Successfully filtered {len(filtered_records)} hard instances to {output_path}")
        return 0
    except Exception as e:
        sys.stderr.write(f"Error filtering hard subset: {e}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())