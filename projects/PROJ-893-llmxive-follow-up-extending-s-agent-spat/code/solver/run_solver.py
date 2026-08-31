import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from solver.csp_engine import CSPEngine, SolveResult

def load_constraints(constraints_path: Path) -> List[Dict[str, Any]]:
    """Load constraints from the extracted JSONL file."""
    if not constraints_path.exists():
        raise FileNotFoundError(f"Constraints file not found: {constraints_path}")
    
    constraints = []
    with open(constraints_path, 'r') as f:
        for line in f:
            if line.strip():
                constraints.append(json.loads(line))
    return constraints

def save_predictions(predictions: List[Dict[str, Any]], output_path: Path) -> None:
    """Save predictions to a JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for pred in predictions:
            f.write(json.dumps(pred) + '\n')

def save_latency_log(latency_log: List[Dict[str, Any]], output_path: Path) -> None:
    """Save latency logs to a JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for entry in latency_log:
            f.write(json.dumps(entry) + '\n')

def save_exclusion_log(exclusion_data: Dict[str, Any], output_path: Path) -> None:
    """Save exclusion log to a JSON file with counts and IDs."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)

def run_batch_solver(
    constraints: List[Dict[str, Any]],
    engine: CSPEngine
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run the solver on a batch of constraints.
    Returns: (predictions, latency_log, excluded_scenes)
    """
    predictions = []
    latency_log = []
    excluded_scenes = []

    for scene in constraints:
        scene_id = scene.get('scene_id', 'unknown')
        
        # Measure latency
        start_time = time.perf_counter()
        
        try:
            result = engine.solve(scene)
            end_time = time.perf_counter()
            latency = end_time - start_time

            if result.success:
                predictions.append({
                    'scene_id': scene_id,
                    'prediction': result.solution,
                    'status': 'success'
                })
                latency_log.append({
                    'scene_id': scene_id,
                    'latency_seconds': latency,
                    'status': 'success'
                })
            else:
                # Solver ran but found no solution (valid exclusion)
                excluded_scenes.append({
                    'scene_id': scene_id,
                    'reason': 'No solution found by CSP',
                    'details': result.error_message
                })
                latency_log.append({
                    'scene_id': scene_id,
                    'latency_seconds': latency,
                    'status': 'no_solution'
                })
        
        except Exception as e:
            end_time = time.perf_counter()
            latency = end_time - start_time
            
            # Critical error (malformed input, etc.)
            excluded_scenes.append({
                'scene_id': scene_id,
                'reason': 'Critical Error',
                'error': str(e)
            })
            latency_log.append({
                'scene_id': scene_id,
                'latency_seconds': latency,
                'status': 'error'
            })

    return predictions, latency_log, excluded_scenes

def main():
    """Main entry point for the solver pipeline."""
    config = Config()
    
    # Paths
    constraints_path = config.DERIVED_DATA_DIR / 'constraints.jsonl'
    predictions_path = config.DERIVED_DATA_DIR / 'predictions.jsonl'
    latency_log_path = config.DERIVED_DATA_DIR / 'latency_log.jsonl'
    exclusion_log_path = config.RESULTS_DIR / 'exclusion_log.json'

    print(f"Loading constraints from {constraints_path}...")
    constraints = load_constraints(constraints_path)
    print(f"Loaded {len(constraints)} scenes.")

    # Initialize solver engine
    engine = CSPEngine()

    print("Running batch solver...")
    predictions, latency_log, excluded_scenes = run_batch_solver(constraints, engine)

    # Save outputs
    save_predictions(predictions, predictions_path)
    save_latency_log(latency_log, latency_log_path)

    # Generate exclusion log
    exclusion_data = {
        'total_scenes_processed': len(constraints),
        'valid_scenes': len(predictions),
        'excluded_scenes': len(excluded_scenes),
        'exclusion_details': excluded_scenes
    }
    
    save_exclusion_log(exclusion_data, exclusion_log_path)
    
    print(f"Solver completed.")
    print(f"  - Predictions saved to: {predictions_path}")
    print(f"  - Latency log saved to: {latency_log_path}")
    print(f"  - Exclusion log saved to: {exclusion_log_path}")
    print(f"  - Total processed: {len(constraints)}, Valid: {len(predictions)}, Excluded: {len(excluded_scenes)}")

if __name__ == '__main__':
    main()