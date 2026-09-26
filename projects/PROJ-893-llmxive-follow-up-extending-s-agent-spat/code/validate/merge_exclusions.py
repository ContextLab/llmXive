"""
Merge exclusion logs from data extraction and solver execution.

This script combines:
1. data/results/exclusion_log.json (from T006b - extraction exclusions)
2. data/derived/solver_failures.json (from T012 - solver exclusions)

into a single categorized exclusion log at data/results/exclusion_log.json.

Categories:
- MissingData: Scenes excluded during extraction (malformed/missing)
- ConstraintError: Solver failed due to constraint satisfaction issues
- GeometricAmbiguity: Solver found multiple valid solutions or none
- BatchTimeout: Solver timed out before completion
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from config if available, otherwise use defaults
try:
    from config import Config
    DERIVED_PATH = getattr(Config, 'DATA_DERIVED', 'data/derived')
    RESULTS_PATH = getattr(Config, 'DATA_RESULTS', 'data/results')
except ImportError:
    DERIVED_PATH = 'data/derived'
    RESULTS_PATH = 'data/results'

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    path = Path(file_path)
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving {file_path}: {e}", file=sys.stderr)
        return False

def merge_exclusions(extraction_log_path: str, solver_failures_path: str, output_path: str) -> Dict[str, Any]:
    """
    Merge exclusion logs from extraction and solver stages.
    
    Args:
        extraction_log_path: Path to data/results/exclusion_log.json (from T006b)
        solver_failures_path: Path to data/derived/solver_failures.json (from T012)
        output_path: Path to write the merged exclusion log
        
    Returns:
        The merged exclusion log dictionary
    """
    # Load extraction exclusions
    extraction_data = load_json_file(extraction_log_path)
    if extraction_data is None:
        print(f"Warning: Extraction log not found at {extraction_log_path}. Starting with empty extraction exclusions.", file=sys.stderr)
        extraction_data = {
            "total_scenes": 0,
            "excluded_count": 0,
            "excluded_ids": []
        }
    
    # Load solver failures
    solver_data = load_json_file(solver_failures_path)
    if solver_data is None:
        print(f"Warning: Solver failures log not found at {solver_failures_path}. Starting with empty solver failures.", file=sys.stderr)
        solver_data = []
    
    # Ensure solver_data is a list
    if not isinstance(solver_data, list):
        # If it's a dict with a 'failures' key, extract it
        if isinstance(solver_data, dict) and 'failures' in solver_data:
            solver_data = solver_data['failures']
        else:
            # Convert dict to list if it contains failure objects keyed by scene_id
            if isinstance(solver_data, dict):
                solver_data = list(solver_data.values())
            else:
                solver_data = []
    
    # Initialize categorized exclusions
    categorized_exclusions = {
        "total_scenes_processed": extraction_data.get("total_scenes", 0),
        "excluded_count": 0,
        "excluded_ids": [],
        "categories": {
            "MissingData": {
                "count": 0,
                "ids": []
            },
            "ConstraintError": {
                "count": 0,
                "ids": []
            },
            "GeometricAmbiguity": {
                "count": 0,
                "ids": []
            },
            "BatchTimeout": {
                "count": 0,
                "ids": []
            },
            "UnexpectedSolverError": {
                "count": 0,
                "ids": []
            }
        }
    }
    
    # Process extraction exclusions (MissingData)
    extraction_excluded_ids = extraction_data.get("excluded_ids", [])
    if isinstance(extraction_excluded_ids, list):
        for scene_id in extraction_excluded_ids:
            categorized_exclusions["categories"]["MissingData"]["ids"].append(scene_id)
            categorized_exclusions["categories"]["MissingData"]["count"] += 1
            categorized_exclusions["excluded_ids"].append(scene_id)
    
    # Process solver failures
    for failure in solver_data:
        if not isinstance(failure, dict):
            continue
        
        scene_id = failure.get("scene_id")
        if not scene_id:
            continue
        
        # Avoid duplicate entries if a scene was already excluded in extraction
        if scene_id in categorized_exclusions["excluded_ids"]:
            continue
        
        error_type = failure.get("error_type", "UnexpectedSolverError")
        
        # Map error types to categories
        category_map = {
            "ConstraintError": "ConstraintError",
            "GeometricAmbiguity": "GeometricAmbiguity",
            "BatchTimeout": "BatchTimeout",
            "Timeout": "BatchTimeout",  # Alias
            "UnexpectedSolverError": "UnexpectedSolverError"
        }
        
        category = category_map.get(error_type, "UnexpectedSolverError")
        
        categorized_exclusions["categories"][category]["ids"].append(scene_id)
        categorized_exclusions["categories"][category]["count"] += 1
        categorized_exclusions["excluded_ids"].append(scene_id)
    
    # Calculate total excluded count
    categorized_exclusions["excluded_count"] = len(categorized_exclusions["excluded_ids"])
    
    # Add summary statistics
    categorized_exclusions["summary"] = {
        "total_excluded": categorized_exclusions["excluded_count"],
        "by_category": {
            cat: data["count"] 
            for cat, data in categorized_exclusions["categories"].items()
        }
    }
    
    # Save the merged exclusion log
    if not save_json_file(output_path, categorized_exclusions):
        raise RuntimeError(f"Failed to save merged exclusion log to {output_path}")
    
    return categorized_exclusions

def main():
    """Main entry point for the merge exclusions script."""
    parser = argparse.ArgumentParser(
        description="Merge exclusion logs from extraction and solver stages."
    )
    parser.add_argument(
        "--extraction-log",
        type=str,
        default=os.path.join(RESULTS_PATH, "exclusion_log.json"),
        help="Path to the extraction exclusion log (from T006b)"
    )
    parser.add_argument(
        "--solver-failures",
        type=str,
        default=os.path.join(DERIVED_PATH, "solver_failures.json"),
        help="Path to the solver failures log (from T012)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(RESULTS_PATH, "exclusion_log.json"),
        help="Path to write the merged exclusion log"
    )
    
    args = parser.parse_args()
    
    print(f"Merging exclusion logs...")
    print(f"  Extraction log: {args.extraction_log}")
    print(f"  Solver failures: {args.solver_failures}")
    print(f"  Output: {args.output}")
    
    try:
        result = merge_exclusions(
            extraction_log_path=args.extraction_log,
            solver_failures_path=args.solver_failures,
            output_path=args.output
        )
        
        print(f"Merge complete.")
        print(f"  Total excluded scenes: {result['excluded_count']}")
        print(f"  Categories:")
        for cat, data in result["categories"].items():
            if data["count"] > 0:
                print(f"    - {cat}: {data['count']}")
        
        # Verification: ensure output contains categorized error_type keys
        assert "categories" in result, "Missing 'categories' key in output"
        for cat in ["MissingData", "ConstraintError", "GeometricAmbiguity", "BatchTimeout"]:
            assert cat in result["categories"], f"Missing category '{cat}' in output"
            assert "count" in result["categories"][cat], f"Missing 'count' in category '{cat}'"
            assert "ids" in result["categories"][cat], f"Missing 'ids' in category '{cat}'"
        
        print("Verification passed: Output contains categorized error_type keys.")
        
    except Exception as e:
        print(f"Error during merge: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
