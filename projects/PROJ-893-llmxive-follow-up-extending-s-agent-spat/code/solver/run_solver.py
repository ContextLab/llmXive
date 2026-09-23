"""
run_solver.py - Full batch execution logic for the symbolic CSP solver.

This script ingests extracted geometric constraints from `data/derived/constraints.jsonl`,
solves them using the CSP engine, and outputs predictions, latency logs, and failure logs.

Requirements:
1. Timeout Logic: Global batch timeout (BATCH_TIMEOUT_HOURS); per-scene soft limit.
2. Status Tracking: Enforce status ('No Solution', 'Ambiguous', 'Success').
3. Output Generation: predictions.jsonl, latency_log.jsonl, solver_failures.json.
4. Error Handling: Distinguish Timeout, ConstraintError, GeometricAmbiguity, UnexpectedSolverError.
5. Timing: Use time.perf_counter for millisecond precision.
"""

import os
import sys
import json
import time
import signal
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling module
from solver.csp_engine import CSPEngine, ConstraintSatisfactionError, CSPSolution, SolveResult

# Configuration constants
BATCH_TIMEOUT_HOURS = 6.0
SCENE_SOFT_LIMIT_SECONDS = 30.0
MAX_RETRIES = 1

class BatchTimeoutError(Exception):
    """Raised when the batch execution exceeds the global timeout."""
    pass

def load_constraints(input_path: str) -> List[Dict[str, Any]]:
    """Load constraints from a JSONL file."""
    constraints = []
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input constraints file not found: {input_path}")

    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                constraints.append(data)
            except json.JSONDecodeError as e:
                # Log malformed lines but continue or raise depending on strictness
                # For this task, we assume valid input based on T029 dry-run
                print(f"WARNING: Malformed JSON at line {line_num}: {e}", file=sys.stderr)
    return constraints

def save_predictions(predictions: List[Dict[str, Any]], output_path: str) -> None:
    """Save predictions to a JSONL file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for pred in predictions:
            f.write(json.dumps(pred) + '\n')

def save_latency_log(latency_logs: List[Dict[str, Any]], output_path: str) -> None:
    """Save latency logs to a JSONL file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for log in latency_logs:
            f.write(json.dumps(log) + '\n')

def save_exclusion_log(failures: List[Dict[str, Any]], output_path: str) -> None:
    """Save solver failures to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2)

def run_batch_solver(
    constraints: List[Dict[str, Any]],
    predictions_out: str,
    latency_out: str,
    failures_out: str
) -> None:
    """
    Execute the CSP solver on a batch of constraints.

    Args:
        constraints: List of constraint dictionaries.
        predictions_out: Path for predictions.jsonl.
        latency_out: Path for latency_log.jsonl.
        failures_out: Path for solver_failures.json.
    """
    engine = CSPEngine()
    predictions = []
    latency_logs = []
    failures = []

    start_time = time.perf_counter()
    batch_deadline = start_time + (BATCH_TIMEOUT_HOURS * 3600)

    scene_count = len(constraints)
    processed_count = 0

    for scene in constraints:
        # Check global batch timeout
        current_time = time.perf_counter()
        if current_time > batch_deadline:
            remaining_ids = [c.get('scene_id', 'unknown') for c in constraints[processed_count:]]
            print(f"BATCH TIMEOUT: Reached {BATCH_TIMEOUT_HOURS}h limit. Stopping.", file=sys.stderr)
            # Log remaining as failures
            for scene_id in remaining_ids:
                failures.append({
                    "scene_id": scene_id,
                    "error_type": "BatchTimeout",
                    "message": "Global batch timeout exceeded."
                })
            break

        scene_id = scene.get('scene_id', 'unknown')
        scene_constraints = scene.get('constraints', [])

        if not scene_constraints:
            # No constraints to solve -> Ambiguous or No Solution?
            # Spec says: Status tracking ('No Solution', 'Ambiguous', 'Success')
            # If no constraints, it's likely ambiguous or invalid.
            # We'll treat empty constraints as "No Solution" for safety, or "Ambiguous"
            # Let's follow T028: "No Solution" for ambiguous inputs.
            pred = {
                "scene_id": scene_id,
                "prediction": None,
                "status": "Ambiguous"
            }
            predictions.append(pred)
            latency_logs.append({
                "scene_id": scene_id,
                "latency_ms": 0.0,
                "status": "Ambiguous"
            })
            processed_count += 1
            continue

        scene_start = time.perf_counter()
        status = "Unknown"
        prediction_value = None
        error_type = None
        error_msg = None

        try:
            # Solve with per-scene timeout signal
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Scene {scene_id} timed out after {SCENE_SOFT_LIMIT_SECONDS}s")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(SCENE_SOFT_LIMIT_SECONDS))

            try:
                result: SolveResult = engine.solve(scene_constraints)
                status = result.status
                if result.solution:
                    prediction_value = result.solution.prediction
                else:
                    prediction_value = None
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            if status == "Success":
                status = "Success"
            elif status == "No Solution":
                status = "No Solution"
            elif status == "Ambiguous":
                status = "Ambiguous"
            else:
                # Fallback for unexpected status
                status = "No Solution"

        except TimeoutError as te:
            status = "Timeout"
            error_type = "Timeout"
            error_msg = str(te)
        except ConstraintSatisfactionError as cse:
            # T028: Distinct subclass of ValueError
            status = "No Solution" # Or Ambiguous depending on CSE type
            error_type = "ConstraintError"
            error_msg = str(cse)
        except ValueError as ve:
            status = "No Solution"
            error_type = "ConstraintError"
            error_msg = str(ve)
        except RuntimeError as re:
            status = "No Solution"
            error_type = "UnexpectedSolverError"
            error_msg = str(re)
        except Exception as e:
            status = "No Solution"
            error_type = "UnexpectedSolverError"
            error_msg = f"Unhandled exception: {type(e).__name__}: {str(e)}"

        scene_end = time.perf_counter()
        latency_ms = (scene_end - scene_start) * 1000

        # Record prediction
        pred_record = {
            "scene_id": scene_id,
            "prediction": prediction_value,
            "status": status
        }
        predictions.append(pred_record)

        # Record latency
        latency_record = {
            "scene_id": scene_id,
            "latency_ms": latency_ms,
            "status": status
        }
        latency_logs.append(latency_record)

        # Record failure if applicable
        if error_type:
            failures.append({
                "scene_id": scene_id,
                "error_type": error_type,
                "message": error_msg
            })

        processed_count += 1
        if processed_count % 100 == 0:
            print(f"Processed {processed_count}/{scene_count} scenes...", file=sys.stderr)

    # Save outputs
    save_predictions(predictions, predictions_out)
    save_latency_log(latency_logs, latency_out)
    save_exclusion_log(failures, failures_out)

    print(f"Solver completed. Processed {processed_count}/{scene_count} scenes.", file=sys.stderr)
    print(f"Predictions saved to: {predictions_out}", file=sys.stderr)
    print(f"Latency log saved to: {latency_out}", file=sys.stderr)
    print(f"Failures saved to: {failures_out}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Run the symbolic CSP solver on extracted constraints.")
    parser.add_argument("--input", required=True, help="Path to input constraints JSONL file.")
    parser.add_argument("--output", required=True, help="Path to output predictions JSONL file.")
    parser.add_argument("--latency-log", required=True, help="Path to output latency log JSONL file.")
    parser.add_argument("--exclusion-log", required=True, help="Path to output solver failures JSON file.")

    args = parser.parse_args()

    try:
        constraints = load_constraints(args.input)
        run_batch_solver(
            constraints=constraints,
            predictions_out=args.output,
            latency_out=args.latency_log,
            failures_out=args.exclusion_log
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()