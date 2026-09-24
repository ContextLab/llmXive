import os
import sys
import json
import time
import signal
import argparse
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local project structure
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config
from solver.csp_engine import CSPEngine, ConstraintSatisfactionError

class BatchTimeoutError(Exception):
    """Raised when the batch processing exceeds the global timeout."""
    pass

def load_constraints(input_path: str) -> List[Dict[str, Any]]:
    """Load constraints from a JSONL file."""
    constraints = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                constraints.append(json.loads(line))
    return constraints

def save_predictions(predictions: List[Dict[str, Any]], output_path: str) -> None:
    """Save predictions to a JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for pred in predictions:
            f.write(json.dumps(pred) + '\n')

def save_latency_log(latency_data: List[Dict[str, Any]], output_path: str) -> None:
    """Save latency log to a JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in latency_data:
            f.write(json.dumps(entry) + '\n')

def save_exclusion_log(failures: List[Dict[str, Any]], output_path: str) -> None:
    """Save solver failures to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2)

def run_batch_solver(
    constraints: List[Dict[str, Any]],
    predictions_path: str,
    latency_path: str,
    failures_path: str,
    batch_timeout_hours: float = 6.0,
    scene_soft_limit_seconds: float = 30.0
) -> None:
    """
    Execute the CSP solver on a batch of constraints.
    
    Args:
        constraints: List of scene constraint dictionaries.
        predictions_path: Output path for predictions.jsonl.
        latency_path: Output path for latency_log.jsonl.
        failures_path: Output path for solver_failures.json.
        batch_timeout_hours: Global timeout for the entire batch.
        scene_soft_limit_seconds: Warning threshold per scene.
    """
    start_time = time.time()
    engine = CSPEngine()
    
    predictions = []
    latency_log = []
    failures = []
    
    for idx, scene in enumerate(constraints):
        scene_id = scene.get('scene_id', f'unknown_{idx}')
        scene_start = time.time()
        
        # Check global timeout
        elapsed_total = time.time() - start_time
        if elapsed_total > (batch_timeout_hours * 3600):
            failures.append({
                "scene_id": scene_id,
                "error_type": "BatchTimeout",
                "message": f"Batch processing exceeded {batch_timeout_hours}h limit at scene {idx}"
            })
            # Log remaining IDs if needed, but we stop here
            break
        
        try:
            # Solve the scene
            result = engine.solve(scene)
            elapsed_scene = time.time() - scene_start
            
            # Record latency
            latency_log.append({
                "scene_id": scene_id,
                "latency_ms": elapsed_scene * 1000,
                "status": result.status
            })
            
            # Record prediction
            predictions.append({
                "scene_id": scene_id,
                "prediction": result.prediction,
                "status": result.status
            })
            
            if elapsed_scene > scene_soft_limit_seconds:
                print(f"WARNING: Scene {scene_id} took {elapsed_scene:.2f}s (limit: {scene_soft_limit_seconds}s)")
                
        except ConstraintSatisfactionError as e:
            elapsed_scene = time.time() - scene_start
            failures.append({
                "scene_id": scene_id,
                "error_type": "ConstraintError",
                "message": str(e)
            })
            # Log as a specific failure, not a prediction
            predictions.append({
                "scene_id": scene_id,
                "prediction": None,
                "status": "ConstraintError"
            })
            latency_log.append({
                "scene_id": scene_id,
                "latency_ms": elapsed_scene * 1000,
                "status": "ConstraintError"
            })
            
        except Exception as e:
            elapsed_scene = time.time() - scene_start
            failures.append({
                "scene_id": scene_id,
                "error_type": "UnexpectedSolverError",
                "message": f"{type(e).__name__}: {str(e)}"
            })
            predictions.append({
                "scene_id": scene_id,
                "prediction": None,
                "status": "Error"
            })
            latency_log.append({
                "scene_id": scene_id,
                "latency_ms": elapsed_scene * 1000,
                "status": "Error"
            })
    
    # Write outputs
    save_predictions(predictions, predictions_path)
    save_latency_log(latency_log, latency_path)
    save_exclusion_log(failures, failures_path)
    
    total_time = time.time() - start_time
    print(f"Batch processing complete. Total time: {total_time:.2f}s")
    print(f"Processed: {len(predictions)}, Failures: {len(failures)}")

def main():
    parser = argparse.ArgumentParser(description="Run the CSP solver on a batch of constraints.")
    parser.add_argument("--input", required=True, help="Path to constraints.jsonl")
    parser.add_argument("--output", required=True, help="Path for predictions.jsonl")
    parser.add_argument("--latency-log", required=True, help="Path for latency_log.jsonl")
    parser.add_argument("--exclusion-log", required=True, help="Path for solver_failures.json")
    parser.add_argument("--batch", action="store_true", help="Run in batch mode with timeouts")
    parser.add_argument("--timeout-hours", type=float, default=6.0, help="Batch timeout in hours")
    parser.add_argument("--scene-limit", type=float, default=30.0, help="Soft limit per scene in seconds")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)
        
    # Ensure output directories exist
    for path in [args.output, args.latency_log, args.exclusion_log]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
    print(f"Loading constraints from {args.input}...")
    constraints = load_constraints(args.input)
    print(f"Loaded {len(constraints)} scenes.")
    
    if args.batch:
        run_batch_solver(
            constraints=constraints,
            predictions_path=args.output,
            latency_path=args.latency_log,
            failures_path=args.exclusion_log,
            batch_timeout_hours=args.timeout_hours,
            scene_soft_limit_seconds=args.scene_limit
        )
    else:
        # Single scene mode (for testing)
        if len(constraints) != 1:
            print("ERROR: Single scene mode requires exactly one scene in input.")
            sys.exit(1)
        scene = constraints[0]
        engine = CSPEngine()
        result = engine.solve(scene)
        print(f"Scene {scene['scene_id']}: {result.prediction} ({result.status})")

if __name__ == "__main__":
    main()