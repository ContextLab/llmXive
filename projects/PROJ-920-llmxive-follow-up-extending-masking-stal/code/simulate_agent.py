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
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths (can be overridden via CLI)
DEFAULT_TRAJECTORY_FILE = "data/raw/trajectories.json"
DEFAULT_OUTPUT_FILE = "data/logs/simulation_results.csv"
CONFIG_FILE = "code/config/simulation_config.json"

# Memory and batching limits
MEMORY_LIMIT_GB = 7.0
CHUNK_SIZE = 100  # Number of trajectories processed per batch

def sigmoid(x: float) -> float:
    """Compute the sigmoid function."""
    if x >= 0:
        return 1 / (1 + math.exp(-x))
    else:
        exp_x = math.exp(x)
        return exp_x / (1 + exp_x)

def load_simulation_config() -> Dict[str, Any]:
    """Load simulation configuration from ``code/config/simulation_config.json``."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        logger.error(f"CONFIG_FILE_MISSING: {CONFIG_FILE}")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        required_keys = ['alpha', 'threshold', 'seed', 'density_levels']
        for key in required_keys:
            if key not in config:
                logger.error(f"CONFIG_FILE_MISSING_KEY: {key}")
                sys.exit(1)

        if not isinstance(config['alpha'], (int, float)) or config['alpha'] <= 0:
            logger.error(f"CONFIG_INVALID_ALPHA: {config['alpha']}")
            sys.exit(1)

        if not isinstance(config['threshold'], (int, float)):
            logger.error(f"CONFIG_INVALID_THRESHOLD: {config['threshold']}")
            sys.exit(1)

        return config
    except json.JSONDecodeError as e:
        logger.error(f"CONFIG_MALFORMED_JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CONFIG_LOAD_ERROR: {e}")
        sys.exit(1)

def heuristic_solver_success(density: float, alpha: float, threshold: float,
                            rng: random.Random) -> (bool, float):
    """
    Determine success probabilistically using the logistic function.
    Returns a tuple ``(success, retrieval_probability)``.
    """
    p_retrieval = sigmoid(alpha * (density - threshold))
    success = rng.random() < p_retrieval
    return success, p_retrieval

def check_evidence_visibility(evidence_turn_index: int, requested_horizon: int,
                              total_turns: int, is_last_turn: bool) -> bool:
    """
    Evidence is visible if its turn index is strictly less than the horizon.
    The ``is_last_turn`` flag does not affect visibility under the current
    definition because the horizon always counts from the most recent turn.
    """
    if requested_horizon <= 0:
        return False
    return evidence_turn_index < requested_horizon

def get_memory_usage_gb() -> float:
    """
    Estimate current memory usage in GB.
    Uses the ``resource`` module on Unix platforms; otherwise returns 0.0.
    """
    try:
        import resource
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # ``ru_maxrss`` is in kilobytes on Linux, bytes on macOS.
        # Convert to GB conservatively.
        return usage_kb / (1024 * 1024)
    except Exception:
        return 0.0

def load_trajectories_streaming(path: Path) -> List[Dict[str, Any]]:
    """
    Load trajectories from a JSON file.
    Performs basic existence and size checks.
    """
    if not path.exists():
        logger.error("Data Flow Violation: Trajectory generation not complete")
        sys.exit(1)

    if path.stat().st_size == 0:
        logger.error("Data Flow Violation: Trajectory file is empty")
        sys.exit(1)

    try:
        with open(path, 'r', encoding='utf-8') as f:
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
    Simulate a batch of trajectories.
    Returns a list of dictionaries matching ``contracts/simulation_log.schema.yaml``.
    """
    rng = random.Random(seed)
    batch_results: List[Dict[str, Any]] = []

    for i, traj in enumerate(trajectories):
        traj_id = traj.get('trajectory_id')
        evidence_turn = traj.get('critical_evidence_turn')
        density_value = traj.get('final_density')
        # ``is_last_turn`` flag is optional; default to False if missing.
        is_last_turn = traj.get('is_last_turn', False)

        # Guard against missing metadata.
        if traj_id is None or evidence_turn is None or density_value is None:
            logger.warning(f"Trajectory {start_idx + i} missing required metadata, skipping.")
            continue

        total_turns = 10  # Fixed by the generator.

        # Determine whether the entropy had to be clamped during generation.
        actual_entropy = traj.get('actual_entropy', 0.0)
        clamped_entropy = actual_entropy < 1e-6

        for horizon in range(1, total_turns + 1):
            visible = check_evidence_visibility(evidence_turn, horizon,
                                                total_turns, is_last_turn)

            # Compute evidence age relative to the current horizon.
            # Age is the number of turns the evidence has been retained.
            evidence_age = max(0, horizon - evidence_turn - 1)

            if not visible:
                success = False
                retrieval_prob = 0.0
            else:
                success, retrieval_prob = heuristic_solver_success(
                    density_value, alpha, threshold, rng
                )

            batch_results.append({
                'trajectory_id': traj_id,
                'density': float(density_value),
                'horizon': int(horizon),
                'evidence_age': int(evidence_age),
                'success': int(success),
                'retrieval_prob': float(retrieval_prob),
                'clamped_entropy': bool(clamped_entropy)
            })

    return batch_results

def write_batch_to_file(batch_results: List[Dict[str, Any]],
                        file_path: Path,
                        append: bool):
    """
    Append a batch of simulation rows to the CSV file.
    """
    fieldnames = [
        'trajectory_id',
        'density',
        'horizon',
        'evidence_age',
        'success',
        'retrieval_prob',
        'clamped_entropy'
    ]
    mode = 'a' if append else 'w'
    with open(file_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        writer.writerows(batch_results)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate agent with variable retention horizons"
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        '--input',
        type=str,
        default=DEFAULT_TRAJECTORY_FILE,
        help="Path to the trajectories JSON file"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT_FILE,
        help="Path to write the simulation CSV file"
    )
    args = parser.parse_args()

    seed = args.seed
    trajectory_path = Path(args.input)
    output_path = Path(args.output)

    logger.info(f"Starting simulation (seed={seed})")
    logger.info(f"Loading trajectories from {trajectory_path}")

    # Load simulation configuration (alpha, threshold, etc.)
    config = load_simulation_config()
    alpha = config['alpha']
    threshold = config['threshold']

    # Load trajectories (streaming style)
    trajectories = load_trajectories_streaming(trajectory_path)
    total_trajectories = len(trajectories)
    logger.info(f"Loaded {total_trajectories} trajectories")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove any existing output file
    if output_path.exists():
        output_path.unlink()

    start_time = time.time()
    total_records = 0

    # Process in chunks to stay within the RAM budget
    first_batch = True
    for start_idx in range(0, total_trajectories, CHUNK_SIZE):
        batch = trajectories[start_idx:start_idx + CHUNK_SIZE]
        batch_results = run_simulation_batch(
            batch,
            alpha,
            threshold,
            seed,
            start_idx
        )
        write_batch_to_file(batch_results, output_path, append=not first_batch)
        first_batch = False
        total_records += len(batch_results)

    duration = time.time() - start_time
    logger.info(f"Simulation completed in {duration:.2f} seconds")
    logger.info(f"Wrote {total_records} records to {output_path}")

    # Memory usage check
    usage_gb = get_memory_usage_gb()
    if usage_gb > MEMORY_LIMIT_GB:
        logger.error(f"MEMORY_LIMIT_EXCEEDED: {usage_gb:.2f} GB > {MEMORY_LIMIT_GB} GB")
        sys.exit(1)
    else:
        logger.info(f"Memory usage OK: {usage_gb:.2f} GB")

    # Verify file size and line count
    if output_path.exists():
        file_size = output_path.stat().st_size
        logger.info(f"Output file size: {file_size} bytes")
        with open(output_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        expected_lines = total_records + 1  # +1 for header
        if line_count != expected_lines:
            logger.error(f"Line count mismatch: expected {expected_lines}, got {line_count}")
            sys.exit(1)
        logger.info(f"Line count verified: {line_count}")
    else:
        logger.error("Output file not created")
        sys.exit(1)

if __name__ == "__main__":
    main()
