"""
Engine Runner for AgenticSTS Simulation.

This module provides the CLI interface and execution logic for re-simulating
trajectories with different memory strategies (dynamic, static, random) and
layer ablation configurations.

It acts as the execution engine for T008 (Ablation Study), T017 (Dynamic Simulation),
T019 (Static Baseline), and T020 (Random Baseline).
"""

import os
import sys
import json
import logging
import random
import hashlib
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from existing project modules
from parser import load_schema, validate_trajectory_against_schema
from simulator import run_dynamic_simulation, run_baseline_simulation, estimate_layer_tokens
from ablation import run_ablation_study, generate_ablation_config
from config import load_config_from_file, ensure_directories

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/engine_runner.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "trajectory.schema.yaml"

def load_test_set_ids(filepath: Optional[str] = None) -> List[str]:
    """
    Load trajectory IDs from the test set split.
    Falls back to a specific file if not provided, or scans processed directory.
    """
    if filepath is None:
        filepath = DATA_PROCESSED_DIR / "test_set.csv"
    
    path = Path(filepath)
    if not path.exists():
        logger.error(f"Test set file not found: {path}")
        return []
    
    try:
        import pandas as pd
        df = pd.read_csv(path)
        if 'trajectory_id' not in df.columns:
            logger.error("test_set.csv missing 'trajectory_id' column")
            return []
        return df['trajectory_id'].tolist()
    except Exception as e:
        logger.error(f"Failed to load test set IDs: {e}")
        return []

def load_raw_trajectories(ids: List[str], schema_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load raw trajectory data for a given list of IDs.
    Reads from data/raw/agenticsts_trajectories.jsonl.
    """
    raw_file = DATA_RAW_DIR / "agenticsts_trajectories.jsonl"
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file missing: {raw_file}. Run T005b first.")
    
    if schema_path is None:
        schema_path = SCHEMA_PATH
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file missing: {schema_path}. Run T003a first.")
    
    schema = load_schema(schema_path)
    
    trajectories = []
    count = 0
    with open(raw_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Validate against schema
                if not validate_trajectory_against_schema(record, schema):
                    logger.warning(f"Trajectory {record.get('trajectory_id', 'unknown')} failed schema validation. Skipping.")
                    continue
                
                if record.get('trajectory_id') in ids:
                    trajectories.append(record)
                    count += 1
                    if len(trajectories) == len(ids):
                        break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON line in raw data: {e}")
                continue
    
    logger.info(f"Loaded {len(trajectories)} trajectories for processing.")
    return trajectories

def get_all_layers() -> List[str]:
    """
    Returns the list of all available memory layers as defined in the schema.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema missing: {SCHEMA_PATH}")
    
    schema = load_schema(SCHEMA_PATH)
    # The schema typically defines fields. We look for a 'layers' or specific context fields.
    # Based on typical AgenticSTS structure, layers are often: 'initial_state', 'observation', 'action', 'reward', 'thought'
    # We extract them dynamically from the schema definition if possible, or use a standard set.
    if 'properties' in schema:
        # Heuristic: look for properties that sound like context layers
        potential_layers = [k for k in schema['properties'].keys() 
                            if k in ['initial_state', 'observation', 'action', 'reward', 'thought', 'legal_moves', 'context']]
        if potential_layers:
            return potential_layers
    
    # Fallback standard set if schema doesn't explicitly list them in a way we can parse
    return ['initial_state', 'observation', 'action', 'reward', 'thought', 'legal_moves']

def estimate_tokens_for_trajectory(trajectory: Dict[str, Any]) -> int:
    """
    Estimate token count for a trajectory based on its content.
    """
    total = 0
    for layer in get_all_layers():
        content = trajectory.get(layer, "")
        if isinstance(content, str):
            total += estimate_layer_tokens(content)
        elif isinstance(content, list):
            total += sum(estimate_layer_tokens(str(item)) for item in content)
    return total

def run_static_baseline_simulation(ids: List[str], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run the Static All-Layers baseline.
    Retrieves ALL available memory layers for every turn.
    """
    logger.info(f"Starting Static Baseline Simulation for {len(ids)} trajectories.")
    
    trajectories = load_raw_trajectories(ids)
    if not trajectories:
        logger.warning("No trajectories found for static baseline.")
        return {"status": "empty", "results": []}
    
    results = []
    for traj in trajectories:
        start_time = time.time()
        # Simulate static: use all layers
        log_entry = run_baseline_simulation(
            trajectory=traj,
            mode="static",
            layers=get_all_layers()
        )
        end_time = time.time()
        
        log_entry['runtime_seconds'] = end_time - start_time
        log_entry['total_tokens'] = estimate_tokens_for_trajectory(traj)
        results.append(log_entry)
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "simulation_logs_static.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"mode": "static", "count": len(results), "results": results}, f, indent=2)
    
    logger.info(f"Static baseline complete. Output written to {output_path}")
    return {"status": "success", "count": len(results), "output": str(output_path)}

def run_random_baseline_simulation(ids: List[str], k: int = 2, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run the No-Store Random baseline.
    Selects exactly k=2 layers uniformly at random for every turn.
    """
    logger.info(f"Starting Random Baseline Simulation (k={k}) for {len(ids)} trajectories.")
    
    trajectories = load_raw_trajectories(ids)
    if not trajectories:
        logger.warning("No trajectories found for random baseline.")
        return {"status": "empty", "results": []}
    
    all_layers = get_all_layers()
    if len(all_layers) < k:
        logger.warning(f"Only {len(all_layers)} layers available, but k={k}. Adjusting k.")
        k = len(all_layers)
    
    results = []
    for traj in trajectories:
        start_time = time.time()
        # Select random k layers
        selected_layers = random.sample(all_layers, k)
        
        log_entry = run_baseline_simulation(
            trajectory=traj,
            mode="random",
            layers=selected_layers,
            seed=random.randint(0, 2**32-1)
        )
        end_time = time.time()
        
        log_entry['runtime_seconds'] = end_time - start_time
        log_entry['total_tokens'] = estimate_tokens_for_trajectory(traj)
        log_entry['selected_layers'] = selected_layers
        results.append(log_entry)
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "simulation_logs_random.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"mode": "random", "k": k, "count": len(results), "results": results}, f, indent=2)
    
    logger.info(f"Random baseline complete. Output written to {output_path}")
    return {"status": "success", "count": len(results), "output": str(output_path)}

def run_dynamic_simulation(ids: List[str], model_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run the Dynamic Policy simulation.
    Uses the trained model to select layers based on utility prediction.
    """
    logger.info(f"Starting Dynamic Simulation for {len(ids)} trajectories.")
    
    trajectories = load_raw_trajectories(ids)
    if not trajectories:
        logger.warning("No trajectories found for dynamic simulation.")
        return {"status": "empty", "results": []}
    
    # Default model path if not provided
    if model_path is None:
        model_path = PROJECT_ROOT / "models" / "layer_utility_classifier.pkl"
    
    if not model_path.exists():
        logger.warning(f"Model not found at {model_path}. Running without model (fallback to heuristic/static).")
        # Fallback behavior: could run static or random if model is missing
        # For this task, we assume the model exists or we handle the error
        raise FileNotFoundError(f"Model file missing: {model_path}. Run T009 first.")
    
    results = []
    for traj in trajectories:
        start_time = time.time()
        log_entry = run_dynamic_simulation(
            trajectory=traj,
            model_path=model_path
        )
        end_time = time.time()
        
        log_entry['runtime_seconds'] = end_time - start_time
        log_entry['total_tokens'] = estimate_tokens_for_trajectory(traj)
        results.append(log_entry)
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "simulation_logs_dynamic.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"mode": "dynamic", "count": len(results), "results": results}, f, indent=2)
    
    logger.info(f"Dynamic simulation complete. Output written to {output_path}")
    return {"status": "success", "count": len(results), "output": str(output_path)}

def run_ablation_experiment(ids: List[str], ablation_layer: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run ablation study for a specific layer on a set of trajectories.
    This is used by T008 to generate ground truth labels.
    """
    logger.info(f"Running ablation study for layer '{ablation_layer}' on {len(ids)} trajectories.")
    
    trajectories = load_raw_trajectories(ids)
    if not trajectories:
        logger.warning("No trajectories found for ablation study.")
        return {"status": "empty", "results": []}
    
    # Generate ablation config
    config = generate_ablation_config(ablation_layer=ablation_layer)
    
    results = []
    for traj in trajectories:
        start_time = time.time()
        # Run ablation simulation
        log_entry = run_ablation_study(
            trajectory=traj,
            config=config
        )
        end_time = time.time()
        
        log_entry['runtime_seconds'] = end_time - start_time
        log_entry['ablated_layer'] = ablation_layer
        results.append(log_entry)
    
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / f"ablation_results_{ablation_layer}.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({"layer": ablation_layer, "count": len(results), "results": results}, f, indent=2)
    
    logger.info(f"Ablation study for '{ablation_layer}' complete. Output written to {output_path}")
    return {"status": "success", "count": len(results), "output": str(output_path)}

def main():
    parser = argparse.ArgumentParser(description="Engine Runner for AgenticSTS Simulation")
    parser.add_argument('--mode', type=str, choices=['dynamic', 'static', 'random', 'ablation'], required=True,
                        help='Simulation mode')
    parser.add_argument('--ablate-layer', type=str, default=None,
                        help='Layer to ablate (required for ablation mode)')
    parser.add_argument('--k', type=int, default=2,
                        help='Number of random layers for random mode')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file path (optional)')
    parser.add_argument('--input-ids', type=str, default=None,
                        help='Path to CSV with trajectory IDs (optional, defaults to test_set.csv)')
    
    args = parser.parse_args()
    
    # Load IDs
    ids = load_test_set_ids(args.input_ids)
    if not ids:
        logger.error("No trajectory IDs found. Exiting.")
        sys.exit(1)
    
    try:
        if args.mode == 'static':
            result = run_static_baseline_simulation(ids, Path(args.output) if args.output else None)
        elif args.mode == 'random':
            result = run_random_baseline_simulation(ids, k=args.k, output_path=Path(args.output) if args.output else None)
        elif args.mode == 'dynamic':
            result = run_dynamic_simulation(ids, output_path=Path(args.output) if args.output else None)
        elif args.mode == 'ablation':
            if not args.ablate_layer:
                logger.error("--ablate-layer is required for ablation mode")
                sys.exit(1)
            result = run_ablation_experiment(ids, args.ablate_layer, Path(args.output) if args.output else None)
        else:
            logger.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
        
        if result.get('status') == 'success':
            print(json.dumps(result, indent=2))
            sys.exit(0)
        else:
            print(json.dumps(result, indent=2))
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()