import argparse
import json
import math
import os
import random
import sys
import logging
import csv
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from sibling modules as per API surface
# Note: The API surface lists 'from utils.entropy import ...' and 'from utils.heuristics import ...'
# We need to import calculate_composite_density to verify density if needed, 
# though the task says we use density_value from metadata.
# We will import the config loader from the existing API surface if it exists, 
# but the API surface for simulate_agent doesn't list a config loader.
# We will implement load_simulation_config here as it is a requirement.

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TRAJECTORY_FILE = "data/raw/trajectories.json"
OUTPUT_FILE = "data/processed/simulation_logs.csv"
CONFIG_FILE = "code/config/simulation_config.json"
MEMORY_LIMIT_GB = 7.0
CHUNK_SIZE = 100  # Process 100 trajectories at a time before writing

def sigmoid(x: float) -> float:
    """Compute the sigmoid function."""
    if x >= 0:
        return 1 / (1 + math.exp(-x))
    else:
        # Avoid overflow for large negative x
        exp_x = math.exp(x)
        return exp_x / (1 + exp_x)

def load_simulation_config() -> Dict[str, Any]:
    """Load simulation configuration from code/config/simulation_config.json."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        logger.error(f"CONFIG_FILE_MISSING: {CONFIG_FILE}")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Validate required keys
        required_keys = ['alpha', 'threshold', 'seed', 'density_levels']
        for key in required_keys:
            if key not in config:
                logger.error(f"CONFIG_FILE_MISSING_KEY: {key}")
                sys.exit(1)
        
        if not isinstance(config['alpha'], (int, float)) or config['alpha'] <= 0:
            logger.error(f"CONFIG_INVALID_ALPHA: {config['alpha']}")
            sys.exit(1)
        
        if not isinstance(config['threshold'], (int, float)) or not (0 <= config['threshold'] <= 1):
            logger.error(f"CONFIG_INVALID_THRESHOLD: {config['threshold']}")
            sys.exit(1)
        
        return config
    except json.JSONDecodeError as e:
        logger.error(f"CONFIG_MALFORMED_JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CONFIG_LOAD_ERROR: {e}")
        sys.exit(1)

def heuristic_solver_success(density: float, alpha: float, threshold: float, rng: random.Random) -> bool:
    """
    Determine success probabilistically using the logistic function:
    P(retrieval) = sigmoid(α * (density - threshold))
    """
    p_retrieval = sigmoid(alpha * (density - threshold))
    return rng.random() < p_retrieval

def check_evidence_visibility(evidence_turn_index: int, requested_horizon: int, total_turns: int, is_last_turn: bool) -> bool:
    """
    Check if the critical evidence is visible within the requested horizon.
    Returns True if the evidence is retained, False otherwise.
    
    Logic:
    - If evidence is at the very last turn (T-1) and horizon is T (full history), it should be visible.
    - If evidence_turn_index < requested_horizon, it is visible (0-indexed turns 0 to horizon-1 are kept).
    - The 'is_last_turn' flag helps handle the edge case where evidence is at T-1.
    """
    # If the horizon is 0, nothing is visible (though horizon 1 to T is requested)
    if requested_horizon <= 0:
        return False
    
    # If the evidence is at the last turn and horizon equals total turns, it is visible.
    # Generally, if the index of the evidence is less than the horizon, it is visible.
    # Example: 5 turns (0,1,2,3,4). Horizon 5. Evidence at 4. 4 < 5 -> True.
    # Example: 5 turns. Horizon 4. Evidence at 4. 4 < 4 -> False.
    if evidence_turn_index < requested_horizon:
        return True
    
    return False

def get_memory_usage_gb() -> float:
    """
    Estimate current memory usage in GB.
    Uses resource module if available (Unix), otherwise returns 0.0 (mocked for safety in cross-platform).
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB. On macOS, it is in KB.
        return usage / (1024 * 1024) # Convert KB to GB
    except ImportError:
        # Fallback for Windows or if resource not available
        # We cannot reliably get memory on Windows without psutil, which might not be installed.
        # Return 0.0 to avoid crash, but the check in main will handle the limit if psutil is present.
        return 0.0

def load_trajectories_streaming() -> List[Dict[str, Any]]:
    """
    Load trajectories from data/raw/trajectories.json.
    Checks for existence and non-zero size.
    """
    path = Path(TRAJECTORY_FILE)
    if not path.exists():
        logger.error("Data Flow Violation: Trajectory generation not complete")
        sys.exit(1)
    
    if path.stat().st_size == 0:
        logger.error("Data Flow Violation: Trajectory file is empty")
        sys.exit(1)
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.error("Data Flow Violation: Trajectory file is not a JSON array")
            sys.exit(1)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Data Flow Violation: Invalid JSON in trajectory file: {e}")
        sys.exit(1)

def run_simulation_batch(
    trajectories: List[Dict[str, Any]], 
    alpha: float, 
    threshold: float, 
    seed: int,
    start_idx: int
) -> List[Dict[str, Any]]:
    """
    Run simulation for a batch of trajectories.
    Returns a list of result dictionaries.
    """
    rng = random.Random(seed)
    results = []
    
    for i, traj in enumerate(trajectories):
        # Extract metadata
        evidence_turn = traj.get('evidence_turn_index')
        density_value = traj.get('density_value')
        total_turns = len(traj.get('turns', [])) # Assuming 'turns' is the list of turns
        is_last_turn = traj.get('is_last_turn', False)
        
        if evidence_turn is None or density_value is None:
            logger.warning(f"Trajectory {start_idx + i} missing metadata, skipping.")
            continue
        
        # Calculate H_min for logging only
        H_min_logged = math.ceil(density_value * 10)
        
        # Simulate for each horizon from 1 to total_turns
        for horizon in range(1, total_turns + 1):
            # Check visibility
            visible = check_evidence_visibility(evidence_turn, horizon, total_turns, is_last_turn)
            
            if not visible:
                # If evidence is not visible, success is impossible (0 probability)
                success = False
            else:
                # Use the heuristic solver
                success = heuristic_solver_success(density_value, alpha, threshold, rng)
            
            results.append({
                'trajectory_id': start_idx + i,
                'density_value': density_value,
                'requested_horizon': horizon,
                'H_min_logged': H_min_logged,
                'success': 1 if success else 0, # Binary 0/1 for CSV
                'evidence_turn_index': evidence_turn,
                'total_turns': total_turns
            })
    
    return results

def write_batch_to_file(batch_results: List[Dict[str, Any]], file_path: str, append: bool):
    """
    Write a batch of results to the CSV file.
    """
    fieldnames = ['trajectory_id', 'density_value', 'requested_horizon', 'H_min_logged', 'success', 'evidence_turn_index', 'total_turns']
    
    mode = 'a' if append else 'w'
    with open(file_path, mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        writer.writerows(batch_results)

def main():
    parser = argparse.ArgumentParser(description="Simulate agent with variable retention horizons")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    
    seed = args.seed
    logger.info(f"Starting simulation with seed {seed}")
    
    # Load config
    config = load_simulation_config()
    alpha = config['alpha']
    threshold = config['threshold']
    # The seed in config might be the default, but we use the CLI arg for reproducibility as per T014 req
    # "Accept a --seed argument passed from the pipeline"
    
    # Load trajectories
    trajectories = load_trajectories_streaming()
    total_trajectories = len(trajectories)
    logger.info(f"Loaded {total_trajectories} trajectories")
    
    # Ensure output directory exists
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Streaming simulation
    start_time = time.time()
    total_results = 0
    
    # Clear file first
    if output_path.exists():
        output_path.unlink()
    
    batch_results = []
    for i in range(0, total_trajectories, CHUNK_SIZE):
        batch = trajectories[i:i+CHUNK_SIZE]
        results = run_simulation_batch(batch, alpha, threshold, seed, i)
        batch_results.extend(results)
        
        # Write batch to file immediately to manage RAM
        if len(batch_results) >= CHUNK_SIZE * (total_trajectories // CHUNK_SIZE + 1): # Should not happen often
            write_batch_to_file(batch_results, str(output_path), append=True)
            total_results += len(batch_results)
            batch_results = []
    
    # Write remaining
    if batch_results:
        write_batch_to_file(batch_results, str(output_path), append=True)
        total_results += len(batch_results)
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Simulation completed in {duration:.2f} seconds")
    logger.info(f"Wrote {total_results} records to {OUTPUT_FILE}")
    
    # Memory check
    # Note: The task requires checking memory usage. 
    # Since we don't have psutil guaranteed, we use the resource module if available.
    # If not, we assume it's fine or log a warning.
    # The requirement says: "If Max RSS > 7168 (7 GB), exit with code 1".
    # We can only do this reliably if we have the data.
    try:
        import resource
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        usage_gb = usage_kb / (1024 * 1024)
        if usage_gb > MEMORY_LIMIT_GB:
            logger.error(f"MEMORY_LIMIT_EXCEEDED: {usage_gb:.2f} GB > {MEMORY_LIMIT_GB} GB")
            sys.exit(1)
        else:
            logger.info(f"Memory usage OK: {usage_gb:.2f} GB")
    except ImportError:
        logger.warning("Could not check memory usage (resource module not available on this platform)")
    
    # File size and chunking verification
    if output_path.exists():
        file_size = output_path.stat().st_size
        logger.info(f"Output file size: {file_size} bytes")
        # Verify line count
        with open(output_path, 'r') as f:
            line_count = sum(1 for _ in f)
        expected_lines = total_results + 1 # +1 for header
        if line_count != expected_lines:
            logger.error(f"File size & chunking verification failed: Expected {expected_lines} lines, got {line_count}")
            sys.exit(1)
        logger.info(f"Line count verified: {line_count}")
    else:
        logger.error("Output file not created")
        sys.exit(1)

if __name__ == "__main__":
    main()