"""
run_solver.py

Executes the CSP solver on the full batch of scenes.
Handles timeouts, logging, and status tracking as per T012 requirements.
"""
import os
import sys
import json
import time
import signal
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from solver.csp_engine import CSPEngine, ConstraintSatisfactionError, CSPSolution, SolveResult

# Configuration Constants
BATCH_TIMEOUT_HOURS = 6
SCENE_SOFT_LIMIT_SECONDS = 30.0  # Warning threshold per scene
MAX_RETRIES = 0  # No retries for solver logic

class BatchTimeoutError(Exception):
    """Raised when the global batch timeout is exceeded."""
    pass

def load_constraints(input_path: str) -> List[Dict[str, Any]]:
    """
    Load constraints from a JSONL file.
    """
    constraints = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                constraints.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping malformed JSON at line {line_num}: {e}", file=sys.stderr)
    return constraints

def save_predictions(predictions: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save predictions to a JSONL file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for pred in predictions:
            f.write(json.dumps(pred) + '\n')

def save_latency_log(latency_log: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save latency log to a JSONL file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in latency_log:
            f.write(json.dumps(entry) + '\n')

def save_exclusion_log(failures: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save solver failures (exclusions) to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2)

def save_wall_clock_time(start: float, end: float, output_path: str) -> None:
    """
    Save wall clock time statistics to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "start_time": start,
        "end_time": end,
        "total_duration_seconds": end - start
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def run_batch_solver(
    constraints: List[Dict[str, Any]],
    predictions_path: str,
    latency_log_path: str,
    failures_path: str,
    wall_clock_path: str
) -> None:
    """
    Run the solver on the entire batch of constraints.
    """
    start_time = time.perf_counter()
    batch_deadline = start_time + (BATCH_TIMEOUT_HOURS * 3600)

    engine = CSPEngine()
    
    predictions = []
    latency_log = []
    failures = []

    processed_count = 0

    print(f"Starting batch solver with {len(constraints)} scenes.")
    print(f"Batch timeout set to {BATCH_TIMEOUT_HOURS} hours.")

    for scene_data in constraints:
        # Check global batch timeout before processing a new scene
        current_time = time.perf_counter()
        if current_time >= batch_deadline:
            remaining_ids = [c.get('scene_id', 'unknown') for c in constraints[processed_count:]]
            timeout_failure = {
                "remaining_scene_ids": remaining_ids,
                "error_type": "BatchTimeout",
                "message": f"Global batch timeout exceeded after {processed_count} scenes.",
                "timestamp": current_time
            }
            failures.append(timeout_failure)
            print(f"Batch Timeout: Stopping after {processed_count} scenes. Remaining: {len(remaining_ids)}")
            break

        scene_id = scene_data.get('scene_id', 'unknown')
        constraints_list = scene_data.get('constraints', [])
        
        if not constraints_list:
            # Handle empty constraints gracefully
            pred_entry = {
                "scene_id": scene_id,
                "prediction": None,
                "status": "No Constraints"
            }
            latency_entry = {
                "scene_id": scene_id,
                "latency_ms": 0.0,
                "status": "No Constraints"
            }
            predictions.append(pred_entry)
            latency_log.append(latency_entry)
            processed_count += 1
            continue

        scene_start = time.perf_counter()
        status = "Success"
        prediction_value = None
        error_type = None
        error_message = None

        try:
            result: SolveResult = engine.solve(constraints_list)
            prediction_value = result.prediction
            status = result.status
            
            if status == "No Solution":
                error_type = "ConstraintError"
                error_message = "ConstraintSatisfactionError: No solution found."
            elif status == "Ambiguous":
                error_type = "GeometricAmbiguity"
                error_message = "GeometricAmbiguity: Multiple solutions found."

        except ConstraintSatisfactionError as e:
            status = "Failed"
            error_type = "ConstraintError"
            error_message = str(e)
        except RuntimeError as e:
            status = "Failed"
            error_type = "UnexpectedSolverError"
            error_message = f"RuntimeError: {str(e)}"
        except ValueError as e:
            # Catch general ValueErrors that aren't ConstraintSatisfactionError
            if isinstance(e, ConstraintSatisfactionError):
                raise # Re-raise if it's our specific subclass
            status = "Failed"
            error_type = "ConstraintError"
            error_message = f"ValueError: {str(e)}"
        except Exception as e:
            status = "Failed"
            error_type = "UnexpectedSolverError"
            error_message = f"Unexpected Error: {type(e).__name__}: {str(e)}"

        scene_end = time.perf_counter()
        latency_ms = (scene_end - scene_start) * 1000.0

        # Log warning if soft limit exceeded
        if latency_ms > (SCENE_SOFT_LIMIT_SECONDS * 1000):
            print(f"Warning: Scene {scene_id} took {latency_ms:.2f}ms (limit: {SCENE_SOFT_LIMIT_SECONDS*1000}ms)")

        # Record prediction
        pred_entry = {
            "scene_id": scene_id,
            "prediction": prediction_value,
            "status": status
        }
        predictions.append(pred_entry)

        # Record latency
        latency_entry = {
            "scene_id": scene_id,
            "latency_ms": latency_ms,
            "status": status
        }
        latency_log.append(latency_entry)

        # Record failure if applicable
        if status == "Failed":
            failure_entry = {
                "scene_id": scene_id,
                "error_type": error_type,
                "message": error_message
            }
            failures.append(failure_entry)

        processed_count += 1

    end_time = time.perf_counter()

    # Write outputs
    save_predictions(predictions, predictions_path)
    save_latency_log(latency_log, latency_log_path)
    save_exclusion_log(failures, failures_path)
    save_wall_clock_time(start_time, end_time, wall_clock_path)

    print(f"Batch solver completed. Processed: {processed_count}, Failed: {len(failures)}")
    print(f"Total duration: {end_time - start_time:.2f} seconds")

def main():
    parser = argparse.ArgumentParser(description="Run CSP solver on a batch of scenes.")
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input constraints JSONL file.')
    parser.add_argument('--output', type=str, required=True,
                        help='Path to output predictions JSONL file.')
    parser.add_argument('--latency-log', type=str, required=True,
                        help='Path to output latency log JSONL file.')
    parser.add_argument('--exclusion-log', type=str, required=True,
                        help='Path to output solver failures JSON file.')
    parser.add_argument('--wall-clock-log', type=str, default=None,
                        help='Path to output wall clock time JSON file. Defaults to data/results/wall_clock_time.json if not provided.')
    
    args = parser.parse_args()

    # Determine wall clock log path
    wall_clock_path = args.wall_clock_log
    if not wall_clock_path:
        wall_clock_path = str(Config.DATA_RESULTS / "wall_clock_time.json")

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        constraints = load_constraints(args.input)
        if not constraints:
            print("Warning: No valid constraints found in input file.", file=sys.stderr)
            # Still create empty output files to satisfy schema checks
            save_predictions([], args.output)
            save_latency_log([], args.latency_log)
            save_exclusion_log([], args.exclusion_log)
            save_wall_clock_time(time.perf_counter(), time.perf_counter(), wall_clock_path)
            return

        run_batch_solver(
            constraints=constraints,
            predictions_path=args.output,
            latency_log_path=args.latency_log,
            failures_path=args.exclusion_log,
            wall_clock_path=wall_clock_path
        )
    except Exception as e:
        print(f"Fatal error during batch execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()