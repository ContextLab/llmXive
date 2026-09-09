import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from utils.config import get_project_root, get_data_dir
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog


def load_trajectories(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load trajectories from a JSONL file.

    Args:
        filepath: Path to the JSONL file. If None, uses the default path
                  from get_data_dir().

    Returns:
        List of trajectory dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If a line is not valid JSON.
    """
    if filepath is None:
        data_dir = get_data_dir()
        filepath = str(data_dir / "synthetic_benchmark" / "trajectories.jsonl")

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {filepath}")

    trajectories = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                trajectory = json.loads(line)
                trajectories.append(trajectory)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON on line {line_num} in {filepath}: {e.msg}",
                    e.doc,
                    e.pos
                )

    return trajectories


def validate_dependency_links(
    trajectories: List[Dict[str, Any]],
    min_dependency_ratio: float = 0.95
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that dependency links are present in trajectories.

    Checks that at least `min_dependency_ratio` of trajectories contain
    valid dependency links. A dependency link is considered valid if it
    exists in the trajectory's metadata or context fields.

    Args:
        trajectories: List of trajectory dictionaries.
        min_dependency_ratio: Minimum ratio of trajectories that must have
                              valid dependency links (default 0.95).

    Returns:
        Tuple of (passed: bool, details: dict).
        details contains:
            - total_trajectories: int
            - trajectories_with_links: int
            - ratio: float
            - failed_trajectory_ids: List[str] (IDs of trajectories without links)
    """
    if not trajectories:
        return False, {
            "total_trajectories": 0,
            "trajectories_with_links": 0,
            "ratio": 0.0,
            "failed_trajectory_ids": [],
            "error": "No trajectories provided"
        }

    total = len(trajectories)
    with_links = 0
    failed_ids = []

    for traj in trajectories:
        traj_id = traj.get("trajectory_id", "unknown")
        metadata = traj.get("metadata", {})
        context = traj.get("context", {})

        # Check for dependency links in various possible locations
        has_links = False

        # Check metadata for dependency_links field
        if "dependency_links" in metadata:
            links = metadata["dependency_links"]
            if isinstance(links, list) and len(links) > 0:
                has_links = True

        # Check for dependency_links in the top-level trajectory
        if "dependency_links" in traj:
            links = traj["dependency_links"]
            if isinstance(links, list) and len(links) > 0:
                has_links = True

        # Check context for dependency information
        if "dependency_links" in context:
            links = context["dependency_links"]
            if isinstance(links, list) and len(links) > 0:
                has_links = True

        if has_links:
            with_links += 1
        else:
            failed_ids.append(traj_id)

    ratio = with_links / total
    passed = ratio >= min_dependency_ratio

    return passed, {
        "total_trajectories": total,
        "trajectories_with_links": with_links,
        "ratio": ratio,
        "failed_trajectory_ids": failed_ids,
        "min_required_ratio": min_dependency_ratio
    }


def validate_benchmark(
    trajectories: List[Dict[str, Any]],
    min_dependency_ratio: float = 0.95,
    min_trajectories: int = 50
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the entire benchmark dataset.

    Performs comprehensive validation including:
    1. Minimum trajectory count check
    2. Dependency link ratio check

    Args:
        trajectories: List of trajectory dictionaries.
        min_dependency_ratio: Minimum ratio of trajectories with dependency links.
        min_trajectories: Minimum number of trajectories required.

    Returns:
        Tuple of (passed: bool, details: dict).
    """
    all_passed = True
    details = {
        "trajectory_count_valid": False,
        "dependency_links_valid": False,
        "overall_passed": False,
        "checks": {}
    }

    # Check minimum trajectory count
    traj_count = len(trajectories)
    count_valid = traj_count >= min_trajectories
    details["trajectory_count_valid"] = count_valid
    details["checks"]["min_trajectory_count"] = {
        "required": min_trajectories,
        "actual": traj_count,
        "passed": count_valid
    }

    if not count_valid:
        all_passed = False

    # Check dependency links
    dep_passed, dep_details = validate_dependency_links(
        trajectories, min_dependency_ratio
    )
    details["dependency_links_valid"] = dep_passed
    details["checks"]["dependency_links"] = dep_details

    if not dep_passed:
        all_passed = False

    details["overall_passed"] = all_passed

    return all_passed, details


def run_validation(
    filepath: Optional[str] = None,
    min_dependency_ratio: float = 0.95,
    min_trajectories: int = 50,
    verbose: bool = True
) -> bool:
    """
    Run the full validation pipeline on the benchmark dataset.

    Args:
        filepath: Path to the JSONL file (optional).
        min_dependency_ratio: Minimum ratio of trajectories with dependency links.
        min_trajectories: Minimum number of trajectories required.
        verbose: If True, print validation results.

    Returns:
        True if validation passes, False otherwise.
    """
    try:
        trajectories = load_trajectories(filepath)

        if verbose:
            print(f"Loaded {len(trajectories)} trajectories from {filepath or 'default path'}")

        passed, details = validate_benchmark(
            trajectories,
            min_dependency_ratio=min_dependency_ratio,
            min_trajectories=min_trajectories
        )

        if verbose:
            print("\n=== Validation Results ===")
            print(f"Overall Passed: {passed}")

            for check_name, check_details in details["checks"].items():
                print(f"\n{check_name}:")
                if "required" in check_details:
                    print(f"  Required: {check_details['required']}")
                if "actual" in check_details:
                    print(f"  Actual: {check_details['actual']}")
                print(f"  Passed: {check_details['passed']}")

                if check_name == "dependency_links" and not check_details["passed"]:
                    failed_ids = check_details.get("failed_trajectory_ids", [])
                    if failed_ids:
                        print(f"  Failed trajectory IDs (first 10): {failed_ids[:10]}")
                        if len(failed_ids) > 10:
                            print(f"  ... and {len(failed_ids) - 10} more")

        return passed

    except FileNotFoundError as e:
        if verbose:
            print(f"ERROR: {e}")
        return False
    except json.JSONDecodeError as e:
        if verbose:
            print(f"ERROR: Invalid JSON in trajectory file: {e}")
        return False
    except Exception as e:
        if verbose:
            print(f"ERROR: Unexpected error during validation: {e}")
        return False


def main():
    """
    Entry point for command-line execution.

    Usage:
        python -m data_generation.validator [--file PATH] [--ratio FLOAT] [--min-traj INT]

    Exit codes:
        0: Validation passed
        1: Validation failed
        2: Error during execution (e.g., file not found)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate dependency links in benchmark trajectories"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to the JSONL trajectory file (default: data/synthetic_benchmark/trajectories.jsonl)"
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.95,
        help="Minimum ratio of trajectories with dependency links (default: 0.95)"
    )
    parser.add_argument(
        "--min-traj",
        type=int,
        default=50,
        help="Minimum number of trajectories required (default: 50)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output"
    )

    args = parser.parse_args()

    verbose = not args.quiet
    result = run_validation(
        filepath=args.file,
        min_dependency_ratio=args.ratio,
        min_trajectories=args.min_traj,
        verbose=verbose
    )

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()