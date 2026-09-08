"""
Validator module for checking dependency links in generated trajectories.

This module provides validation logic to ensure that synthetic trajectories
contain properly annotated dependency links, where information required at
a given step is available from a prior step (typically >10 steps back).
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import project utilities
from utils.config import get_project_root, get_data_dir
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog


def load_trajectories(
    file_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load trajectories from a JSONL file.

    Args:
        file_path: Path to the JSONL file. If None, uses the default path
                   from project configuration.

    Returns:
        List of trajectory dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if file_path is None:
        data_dir = get_data_dir()
        file_path = str(data_dir / "synthetic_benchmark" / "trajectories.jsonl")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {file_path}")

    trajectories = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                traj = json.loads(line)
                trajectories.append(traj)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num} in {file_path}",
                    e.doc, e.pos
                )

    return trajectories


def validate_dependency_links(
    trajectory: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that a trajectory contains properly annotated dependency links.

    A valid dependency link must:
    1. Exist for steps that require information from prior steps
    2. Reference a valid prior step index (step_idx > 10)
    3. Have a valid 'source_step' that is less than the current step

    Args:
        trajectory: A single trajectory dictionary from the benchmark.

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    steps = trajectory.get("steps", [])

    if not steps:
        errors.append("Trajectory has no steps")
        return False, errors

    for step_idx, step in enumerate(steps):
        step_id = step.get("id", step_idx)
        dependencies = step.get("dependencies", [])

        for dep in dependencies:
            source_step = dep.get("source_step")
            dep_type = dep.get("type", "unknown")

            # Check if source_step is a valid integer
            if not isinstance(source_step, int):
                errors.append(
                    f"Step {step_id}: Invalid source_step type "
                    f"(expected int, got {type(source_step).__name__})"
                )
                continue

            # Check if source_step is within valid range
            if source_step < 0 or source_step >= step_idx:
                errors.append(
                    f"Step {step_id}: source_step {source_step} is out of "
                    f"range for step index {step_idx}"
                )
                continue

            # Check if dependency is from sufficiently prior step (>10 indices prior)
            # This is the key requirement for long-horizon context testing
            if step_idx - source_step <= 10:
                errors.append(
                    f"Step {step_id}: Dependency from step {source_step} is "
                    f"only {step_idx - source_step} steps back (requires >10)"
                )

    return len(errors) == 0, errors


def validate_benchmark(
    file_path: Optional[str] = None,
    min_success_rate: float = 0.95
) -> Dict[str, Any]:
    """
    Validate an entire benchmark file for dependency link compliance.

    Args:
        file_path: Path to the JSONL file. If None, uses default path.
        min_success_rate: Minimum required success rate (default 0.95 for 95%)

    Returns:
        Dictionary containing validation results:
        - total_trajectories: Number of trajectories checked
        - valid_trajectories: Number of trajectories passing validation
        - success_rate: Ratio of valid trajectories
        - errors_by_trajectory: List of errors for each invalid trajectory
        - passed: True if success_rate >= min_success_rate

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    trajectories = load_trajectories(file_path)

    if not trajectories:
        return {
            "total_trajectories": 0,
            "valid_trajectories": 0,
            "success_rate": 0.0,
            "errors_by_trajectory": [],
            "passed": False,
            "message": "No trajectories found in file"
        }

    valid_count = 0
    all_errors = []

    for idx, traj in enumerate(trajectories):
        traj_id = traj.get("id", f"trajectory_{idx}")
        is_valid, errors = validate_dependency_links(traj)

        if is_valid:
            valid_count += 1
        else:
            all_errors.append({
                "trajectory_id": traj_id,
                "errors": errors
            })

    success_rate = valid_count / len(trajectories)
    passed = success_rate >= min_success_rate

    return {
        "total_trajectories": len(trajectories),
        "valid_trajectories": valid_count,
        "success_rate": success_rate,
        "errors_by_trajectory": all_errors,
        "passed": passed,
        "min_success_rate_required": min_success_rate
    }


def run_validation(
    file_path: Optional[str] = None,
    min_success_rate: float = 0.95,
    output_log: bool = True
) -> Dict[str, Any]:
    """
    Run validation and optionally log results.

    This is the main entry point for the validator.

    Args:
        file_path: Path to the JSONL file to validate.
        min_success_rate: Minimum required success rate.
        output_log: Whether to write results to the execution log.

    Returns:
        Validation results dictionary.
    """
    try:
        results = validate_benchmark(file_path, min_success_rate)

        if output_log:
            # Log the validation result
            log_entry = TrajectoryExecutionLog(
                task_name="dependency_link_validation",
                status="passed" if results["passed"] else "failed",
                metrics={
                    "total_trajectories": results["total_trajectories"],
                    "valid_trajectories": results["valid_trajectories"],
                    "success_rate": results["success_rate"],
                    "min_success_rate_required": results["min_success_rate_required"]
                },
                details={
                    "file_path": file_path or str(get_data_dir() / "synthetic_benchmark" / "trajectories.jsonl"),
                    "errors": results["errors_by_trajectory"]
                }
            )
            log_entry.save()

        return results

    except Exception as e:
        error_result = {
            "total_trajectories": 0,
            "valid_trajectories": 0,
            "success_rate": 0.0,
            "passed": False,
            "error": str(e)
        }

        if output_log:
            log_entry = TrajectoryExecutionLog(
                task_name="dependency_link_validation",
                status="error",
                metrics={"error": str(e)},
                details={"file_path": file_path}
            )
            log_entry.save()

        raise


def main():
    """
    Command-line entry point for the validator.

    Usage:
        python -m code.data_generation.validator [--file PATH] [--min-rate RATE]

    Examples:
        python -m code.data_generation.validator
        python -m code.data_generation.validator --file data/synthetic_benchmark/trajectories.jsonl --min-rate 0.90
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate dependency links in synthetic trajectories"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to the JSONL file (default: data/synthetic_benchmark/trajectories.jsonl)"
    )
    parser.add_argument(
        "--min-rate",
        type=float,
        default=0.95,
        help="Minimum required success rate (default: 0.95)"
    )

    args = parser.parse_args()

    print(f"Validating trajectories from: {args.file or 'default path'}")
    print(f"Minimum success rate required: {args.min_rate:.2%}")
    print("-" * 50)

    try:
        results = run_validation(
            file_path=args.file,
            min_success_rate=args.min_rate,
            output_log=True
        )

        print(f"Total trajectories: {results['total_trajectories']}")
        print(f"Valid trajectories: {results['valid_trajectories']}")
        print(f"Success rate: {results['success_rate']:.2%}")
        print(f"Required rate: {results['min_success_rate_required']:.2%}")
        print(f"Validation {'PASSED' if results['passed'] else 'FAILED'}")

        if not results["passed"]:
            print("\nErrors encountered:")
            for err_entry in results["errors_by_trajectory"]:
                print(f"  Trajectory {err_entry['trajectory_id']}:")
                for err in err_entry["errors"]:
                    print(f"    - {err}")
            sys.exit(1)
        else:
            print("\nAll dependency links validated successfully.")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"Validation failed with error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
