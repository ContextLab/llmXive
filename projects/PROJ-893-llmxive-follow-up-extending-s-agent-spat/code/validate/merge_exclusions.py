import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import Config

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {file_path}: {e}")
        sys.exit(1)

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    ensure_directory(file_path)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved exclusion log to: {file_path}")

def ensure_directory(file_path: str) -> None:
    """Ensure the directory for a file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def merge_exclusions(extraction_log_path: str, solver_failures_path: str, output_path: str) -> Dict[str, Any]:
    """
    Merge exclusion logs from extraction (T006b) and solver failures (T012-exec).
    
    Logic:
    1. Load extraction log (MissingData exclusions).
    2. Load solver failures (ConstraintError, GeometricAmbiguity, BatchTimeout, etc.).
    3. Aggregate counts and IDs by category.
    4. Calculate totals and summary statistics.
    """
    
    # Load inputs
    extraction_log = load_json_file(extraction_log_path)
    solver_failures = load_json_file(solver_failures_path)
    
    # Initialize merged structure with all possible categories
    merged_categories = {
        "MissingData": {"count": 0, "ids": []},
        "ConstraintError": {"count": 0, "ids": []},
        "GeometricAmbiguity": {"count": 0, "ids": []},
        "BatchTimeout": {"count": 0, "ids": []},
        "UnexpectedSolverError": {"count": 0, "ids": []}
    }
    
    total_scenes_processed = extraction_log.get("total_scenes_processed", 0)
    
    # 1. Process Extraction Log (MissingData)
    # The extraction log might have a 'categories' key or flat 'excluded_ids'
    if "categories" in extraction_log and "MissingData" in extraction_log["categories"]:
        cat_data = extraction_log["categories"]["MissingData"]
        merged_categories["MissingData"]["count"] = cat_data.get("count", 0)
        merged_categories["MissingData"]["ids"] = list(cat_data.get("ids", []))
    elif "excluded_ids" in extraction_log:
        # Fallback if structure is flat
        merged_categories["MissingData"]["count"] = len(extraction_log["excluded_ids"])
        merged_categories["MissingData"]["ids"] = list(extraction_log["excluded_ids"])
    
    # 2. Process Solver Failures
    # solver_failures is expected to be a list of failure objects or a dict with 'failures'
    solver_failures_list = []
    if isinstance(solver_failures, list):
        solver_failures_list = solver_failures
    elif isinstance(solver_failures, dict) and "failures" in solver_failures:
        solver_failures_list = solver_failures["failures"]
    
    for failure in solver_failures_list:
        error_type = failure.get("error_type", "UnexpectedSolverError")
        scene_id = failure.get("scene_id")
        
        if error_type in merged_categories:
            merged_categories[error_type]["ids"].append(scene_id)
        else:
            # Map unknown errors to UnexpectedSolverError
            merged_categories["UnexpectedSolverError"]["ids"].append(scene_id)
    
    # Update counts based on IDs
    for cat_key in merged_categories:
        # Deduplicate IDs just in case
        unique_ids = list(set(merged_categories[cat_key]["ids"]))
        merged_categories[cat_key]["ids"] = unique_ids
        merged_categories[cat_key]["count"] = len(unique_ids)
    
    # Calculate totals
    total_excluded = sum(cat["count"] for cat in merged_categories.values())
    all_excluded_ids = []
    for cat in merged_categories.values():
        all_excluded_ids.extend(cat["ids"])
    
    # Build summary
    summary_by_category = {k: v["count"] for k, v in merged_categories.items()}
    
    final_output = {
        "total_scenes_processed": total_scenes_processed,
        "excluded_count": total_excluded,
        "excluded_ids": list(set(all_excluded_ids)), # Ensure uniqueness across sources
        "categories": merged_categories,
        "summary": {
            "total_excluded": total_excluded,
            "by_category": summary_by_category
        }
    }
    
    return final_output

def main():
    parser = argparse.ArgumentParser(description="Merge exclusion logs from extraction and solver stages.")
    parser.add_argument(
        "--extraction-log",
        type=str,
        default="data/results/exclusion_log.json",
        help="Path to the extraction log (T006b output)"
    )
    parser.add_argument(
        "--solver-failures",
        type=str,
        default="data/derived/solver_failures.json",
        help="Path to the solver failures log (T012-exec output)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/exclusion_log.json",
        help="Path to the merged output exclusion log"
    )
    
    args = parser.parse_args()
    
    # Check input file existence explicitly before processing
    if not os.path.exists(args.extraction_log):
        print(f"ERROR: Extraction log not found: {args.extraction_log}")
        sys.exit(1)
    if not os.path.exists(args.solver_failures):
        print(f"ERROR: Solver failures log not found: {args.solver_failures}")
        sys.exit(1)
        
    print(f"Merging exclusions from:")
    print(f"  Extraction: {args.extraction_log}")
    print(f"  Solver: {args.solver_failures}")
    
    result = merge_exclusions(args.extraction_log, args.solver_failures, args.output)
    save_json_file(args.output, result)
    
    # Verification print
    print(f"Merged exclusion log created with {result['excluded_count']} total exclusions.")
    print(f"Categories: {result['summary']['by_category']}")

if __name__ == "__main__":
    main()