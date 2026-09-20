"""
Solver runner script for the CSP Engine.
Handles batch processing, timeout logic, and output generation.
"""
import os
import sys
import json
import time
import signal
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure code directory is in path for imports
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "code"))

from solver.csp_engine import CSPEngine, SolveResult, ConstraintSatisfactionError
from config import Config

class BatchTimeoutError(Exception):
    """Raised when the global batch timeout is reached."""
    pass

def load_constraints(input_path: str) -> List[Dict[str, Any]]:
    """Load constraints from a JSONL file."""
    constraints = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                constraints.append(json.loads(line))
    return constraints

def save_predictions(output_path: str, results: List[Dict[str, Any]]):
    """Save predictions to a JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')

def save_latency_log(output_path: str, results: List[Dict[str, Any]]):
    """Save latency logs to a JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result) + '\n')

def save_exclusion_log(output_path: str, failures: List[Dict[str, Any]]):
    """Save solver failures to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(failures, f, indent=2)

def run_batch_solver(input_path: str, output_path: str, latency_path: str, exclusion_path: str):
    """Run the CSP solver on a batch of constraints."""
    config = Config()
    logger = config.logger
    
    batch_timeout_hours = config.BATCH_TIMEOUT_HOURS
    scene_soft_limit_seconds = config.SCENE_SOFT_LIMIT_SECONDS

    start_time = time.time()
    constraints = load_constraints(input_path)
    predictions = []
    latency_logs = []
    failures = []

    logger.info(f"Processing {len(constraints)} scenes...")

    for scene in constraints:
        # Check batch timeout
        if time.time() - start_time > batch_timeout_hours * 3600:
            logger.warning("Batch timeout reached. Stopping processing.")
            failures.append({
                "scene_id": scene.get("scene_id", "unknown"),
                "error_type": "BatchTimeout",
                "message": "Global batch timeout reached"
            })
            # Log remaining scenes as skipped
            remaining_scenes = [c.get("scene_id") for c in constraints[constraints.index(scene):]]
            if remaining_scenes:
                logger.warning(f"Skipped {len(remaining_scenes)} scenes due to timeout.")
            break

        scene_id = scene.get("scene_id", "unknown")
        scene_start = time.time()
        
        try:
            engine = CSPEngine()
            result = engine.solve(scene)
            
            latency_ms = (time.time() - scene_start) * 1000
            
            # Log soft limit warning
            if latency_ms / 1000 > scene_soft_limit_seconds:
                logger.warning(f"Scene {scene_id} exceeded soft limit ({latency_ms/1000:.2f}s)")

            predictions.append({
                "scene_id": scene_id,
                "prediction": result.prediction,
                "status": result.status
            })
            latency_logs.append({
                "scene_id": scene_id,
                "latency_ms": latency_ms,
                "status": result.status
            })

        except ConstraintSatisfactionError as e:
            logger.warning(f"Scene {scene_id} failed constraint satisfaction: {e}")
            failures.append({
                "scene_id": scene_id,
                "error_type": "ConstraintError",
                "message": str(e)
            })
            predictions.append({
                "scene_id": scene_id,
                "prediction": None,
                "status": "No Solution"
            })
            latency_logs.append({
                "scene_id": scene_id,
                "latency_ms": (time.time() - scene_start) * 1000,
                "status": "No Solution"
            })
        except Exception as e:
            logger.error(f"Unexpected error for scene {scene_id}: {e}")
            failures.append({
                "scene_id": scene_id,
                "error_type": "UnexpectedSolverError",
                "message": str(e)
            })
            predictions.append({
                "scene_id": scene_id,
                "prediction": None,
                "status": "Error"
            })
            latency_logs.append({
                "scene_id": scene_id,
                "latency_ms": (time.time() - scene_start) * 1000,
                "status": "Error"
            })

    save_predictions(output_path, predictions)
    save_latency_log(latency_path, latency_logs)
    save_exclusion_log(exclusion_path, failures)
    
    logger.info(f"Solver completed. Processed {len(predictions)} scenes.")
    logger.info(f"Failures logged: {len(failures)}")

def main():
    parser = argparse.ArgumentParser(description="Run CSP solver on extracted constraints")
    parser.add_argument("--input", type=str, required=True, help="Path to constraints.jsonl")
    parser.add_argument("--output", type=str, required=True, help="Path to output predictions.jsonl")
    parser.add_argument("--latency-log", type=str, required=True, help="Path to latency_log.jsonl")
    parser.add_argument("--exclusion-log", type=str, required=True, help="Path to solver_failures.json")
    args = parser.parse_args()

    run_batch_solver(args.input, args.output, args.latency_log, args.exclusion_log)

if __name__ == "__main__":
    main()
