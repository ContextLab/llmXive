import os
import sys
import json
import time
import signal
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import config
from solver.csp_engine import CSPEngine, SolveResult

class ConstraintSatisfactionError(Exception):
    """Custom exception for constraint satisfaction failures (T028a)."""
    pass

def load_constraints(input_path: Path) -> List[Dict[str, Any]]:
    """Load constraints from JSONL file."""
    constraints = []
    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                constraints.append(json.loads(line))
    return constraints

def save_predictions(results: List[SolveResult], output_path: Path):
    """Save predictions to JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for r in results:
            f.write(json.dumps({
                "scene_id": r.scene_id,
                "prediction": r.solution,
                "status": r.status,
                "latency_ms": r.latency_ms
            }) + '\n')

def save_latency_log(results: List[SolveResult], output_path: Path):
    """Save latency log to JSONL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for r in results:
            f.write(json.dumps({
                "scene_id": r.scene_id,
                "latency_ms": r.latency_ms
            }) + '\n')

def save_exclusion_log(failures: List[Dict[str, Any]], output_path: Path):
    """Save solver failures to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"failures": failures}, f, indent=2)

def run_batch_solver(constraints: List[Dict[str, Any]], batch_timeout: float, per_scene_timeout: float) -> tuple:
    """
    Run solver on a batch of constraints.
    Returns (results, failures).
    """
    engine = CSPEngine(timeout_seconds=per_scene_timeout)
    results = []
    failures = []
    start_batch = time.time()

    for scene in constraints:
        # Check batch timeout
        if time.time() - start_batch > batch_timeout:
            print(f"Batch timeout reached ({batch_timeout}s). Stopping.")
            break

        scene_id = scene.get('scene_id', 'unknown')
        scene_constraints = scene.get('constraints', [])

        try:
            result = engine.solve(scene_id, scene_constraints)
            results.append(result)
            if result.status == "Error":
                failures.append({"scene_id": scene_id, "error": "Solver Error"})
        except ConstraintSatisfactionError as e:
            # T028b: Catch ConstraintSatisfactionError using the format from T028a
            # Addressing Edge Case: "insufficient constraints"
            error_type = type(e).__name__
            log_entry = {
                "scene_id": scene_id,
                "error_type": error_type,
                "message": str(e)
            }
            failures.append(log_entry)
            # Record a failed result to maintain alignment with input count
            results.append(SolveResult(scene_id, None, "Error", 0))
        except Exception as e:
            # Fallback for other unexpected errors
            error_type = type(e).__name__
            log_entry = {
                "scene_id": scene_id,
                "error_type": error_type,
                "message": str(e)
            }
            failures.append(log_entry)
            results.append(SolveResult(scene_id, None, "Error", 0))

    return results, failures

def main():
    parser = argparse.ArgumentParser(description="Run CSP solver batch")
    parser.add_argument("--input", type=str, required=True, help="Input constraints JSONL")
    parser.add_argument("--output", type=str, required=True, help="Output predictions JSONL")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Use config with tolerant attribute access
    derived_path = getattr(config, 'DATA_DERIVED', getattr(config, 'DERIVED_PATH', Path('data/derived')))
    
    latency_log_path = derived_path / "latency_log.jsonl"
    solver_failures_path = derived_path / "solver_failures.json"

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    constraints = load_constraints(input_path)
    results, failures = run_batch_solver(
        constraints,
        batch_timeout=getattr(config, 'TIMEOUT_BATCH', 21600),
        per_scene_timeout=getattr(config, 'TIMEOUT_PER_SCENE', 60)
    )

    save_predictions(results, output_path)
    save_latency_log(results, latency_log_path)
    save_exclusion_log(failures, solver_failures_path)

    print(f"Solver completed. {len(results)} scenes processed.")

if __name__ == "__main__":
    main()