"""
Merge exclusion logs from data extraction (T006b) and solver execution (T012)
into a final categorized exclusion log.

This script aggregates:
1. Exclusions from T006b (data/results/exclusion_log.json) - primarily "MissingData"
2. Exclusions from T012 (data/derived/solver_failures.json) - categorized by error_type

The final output is written to data/results/exclusion_log.json with a unified
categorization structure.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to load {file_path}: {e}")
        return None


def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save data to a JSON file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"SUCCESS: Written {file_path}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to write {file_path}: {e}")
        return False


def merge_exclusions(
    extraction_log_path: Path,
    solver_failures_path: Path,
    output_path: Path
) -> bool:
    """
    Merge exclusion logs from extraction and solver stages.

    Args:
        extraction_log_path: Path to T006b output (data/results/exclusion_log.json)
        solver_failures_path: Path to T012 output (data/derived/solver_failures.json)
        output_path: Path for the final merged exclusion log

    Returns:
        True if merge was successful, False otherwise
    """
    # Load extraction exclusions (T006b)
    extraction_data = load_json_file(extraction_log_path)
    if extraction_data is None:
        print("ERROR: Could not load extraction exclusion log. Aborting.")
        return False

    # Load solver failures (T012)
    solver_failures = load_json_file(solver_failures_path)
    if solver_failures is None:
        # Solver failures file might be empty or missing if all scenes succeeded
        # This is acceptable - we proceed with just extraction exclusions
        print("WARNING: Solver failures file not found or empty. Proceeding with extraction exclusions only.")
        solver_failures = []

    # Initialize categories
    categories = {
        "MissingData": {"count": 0, "ids": []},
        "ConstraintError": {"count": 0, "ids": []},
        "GeometricAmbiguity": {"count": 0, "ids": []},
        "BatchTimeout": {"count": 0, "ids": []},
        "UnexpectedSolverError": {"count": 0, "ids": []}
    }

    # Process extraction exclusions (T006b)
    # These are primarily "MissingData" but the source file might have categories
    if "categories" in extraction_data:
        # Source already has categorized data
        for category_name, cat_data in extraction_data["categories"].items():
            if category_name in categories:
                categories[category_name]["count"] += cat_data.get("count", 0)
                categories[category_name]["ids"].extend(cat_data.get("ids", []))
            else:
                # Unknown category from extraction - treat as MissingData
                categories["MissingData"]["count"] += cat_data.get("count", 0)
                categories["MissingData"]["ids"].extend(cat_data.get("ids", []))
    else:
        # Fallback: treat all extraction exclusions as MissingData
        excluded_ids = extraction_data.get("excluded_ids", [])
        categories["MissingData"]["count"] += len(excluded_ids)
        categories["MissingData"]["ids"].extend(excluded_ids)

    # Process solver failures (T012)
    # solver_failures is expected to be a list of dicts with 'scene_id' and 'error_type'
    if isinstance(solver_failures, list):
        for failure in solver_failures:
            scene_id = failure.get("scene_id")
            error_type = failure.get("error_type")

            if not scene_id:
                print(f"WARNING: Skipping solver failure without scene_id: {failure}")
                continue

            # Map error_type to category
            if error_type in categories:
                categories[error_type]["count"] += 1
                categories[error_type]["ids"].append(scene_id)
            else:
                # Unknown error type - treat as UnexpectedSolverError
                categories["UnexpectedSolverError"]["count"] += 1
                categories["UnexpectedSolverError"]["ids"].append(scene_id)
    elif isinstance(solver_failures, dict):
        # Handle case where solver_failures is a dict with 'failures' key
        failures_list = solver_failures.get("failures", [])
        if failures_list:
            for failure in failures_list:
                scene_id = failure.get("scene_id")
                error_type = failure.get("error_type")

                if not scene_id:
                    print(f"WARNING: Skipping solver failure without scene_id: {failure}")
                    continue

                if error_type in categories:
                    categories[error_type]["count"] += 1
                    categories[error_type]["ids"].append(scene_id)
                else:
                    categories["UnexpectedSolverError"]["count"] += 1
                    categories["UnexpectedSolverError"]["ids"].append(scene_id)

    # Calculate totals
    total_excluded = sum(cat["count"] for cat in categories.values())
    all_excluded_ids = []
    for cat in categories.values():
        all_excluded_ids.extend(cat["ids"])

    # Remove duplicates (though there shouldn't be any between stages)
    all_excluded_ids = list(set(all_excluded_ids))

    # Build final output structure
    final_log = {
        "total_scenes_processed": 1000,  # From T006b sample size
        "excluded_count": total_excluded,
        "excluded_ids": sorted(all_excluded_ids),
        "categories": categories,
        "summary": {
            "total_excluded": total_excluded,
            "by_category": {
                cat_name: cat_data["count"]
                for cat_name, cat_data in categories.items()
            }
        },
        "sources": {
            "extraction_log": str(extraction_log_path),
            "solver_failures": str(solver_failures_path),
            "merged_at": str(Path(__file__).parent)  # Placeholder for timestamp if needed
        }
    }

    # Save output
    return save_json_file(output_path, final_log)


def main():
    """Main entry point for the merge exclusions script."""
    parser = argparse.ArgumentParser(
        description="Merge exclusion logs from extraction and solver stages"
    )
    parser.add_argument(
        "--extraction-log",
        type=Path,
        default=DATA_RESULTS_DIR / "exclusion_log.json",
        help="Path to T006b exclusion log (default: data/results/exclusion_log.json)"
    )
    parser.add_argument(
        "--solver-failures",
        type=Path,
        default=DATA_DERIVED_DIR / "solver_failures.json",
        help="Path to T012 solver failures (default: data/derived/solver_failures.json)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_RESULTS_DIR / "exclusion_log.json",
        help="Path for the merged exclusion log (default: data/results/exclusion_log.json)"
    )

    args = parser.parse_args()

    print(f"Loading extraction log from: {args.extraction_log}")
    print(f"Loading solver failures from: {args.solver_failures}")
    print(f"Writing merged log to: {args.output}")

    success = merge_exclusions(args.extraction_log, args.solver_failures, args.output)

    if not success:
        print("ERROR: Merge failed. Check logs above.")
        sys.exit(1)
    else:
        print("SUCCESS: Exclusion logs merged successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()