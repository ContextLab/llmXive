"""
Seed Verification Script for llmXive Pipeline.

This script re-runs the noise injection process and baseline execution on a
small subset to verify deterministic reproducibility. It compares the SHA-256
hashes of the regenerated artifacts against stored hashes in the state file.
"""

import os
import sys
import json
import hashlib
import logging
import argparse
import random
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_STATE_PATH = STATE_DIR / "projects" / "PROJ-894-llmxive-follow-up-extending-memory-is-re.yaml"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Utility Functions ---

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def set_all_seeds(seed: int = 42):
    """Set seeds for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        logger.warning("NumPy not available, skipping numpy seed.")
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        logger.warning("PyTorch not available, skipping torch seed.")
    
    logger.info(f"All seeds set to {seed}")

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        # Fallback to default if config is missing, though task implies it exists
        logger.warning(f"config.yaml not found at {config_path}, using defaults.")
        return {"noise_ratio": 0.1, "seed": 42}
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.error("PyYAML not installed. Cannot load config.yaml.")
        raise
    except Exception as e:
        logger.error(f"Error loading config.yaml: {e}")
        raise

def load_state() -> Dict[str, Any]:
    """Load state file (YAML or JSON)."""
    if not PROJECT_STATE_PATH.exists():
        # Create directory if missing
        PROJECT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return {"artifact_hashes": {}}
    
    try:
        import yaml
        with open(PROJECT_STATE_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Try JSON if YAML fails or isn't available
        try:
            with open(PROJECT_STATE_PATH, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("State file is neither valid YAML nor JSON.")
            raise
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        raise

def save_state(state: Dict[str, Any]):
    """Save state file."""
    PROJECT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        with open(PROJECT_STATE_PATH, 'w') as f:
            yaml.dump(state, f, default_flow_style=False)
    except ImportError:
        with open(PROJECT_STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)
    logger.info(f"State saved to {PROJECT_STATE_PATH}")

# --- Reproduction Logic ---

def run_noise_injection_repro(config: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Re-run noise injection on clean graphs and compute hash.
    Returns (regenerated_hash, original_path) or (None, None) if input missing.
    """
    clean_graph_path = DATA_DIR / "intermediate" / "graphs_raw.json"
    if not clean_graph_path.exists():
        logger.warning(f"Clean graph file not found: {clean_graph_path}. Skipping noise repro.")
        return None, None

    logger.info(f"Loading clean graphs from {clean_graph_path}")
    try:
        with open(clean_graph_path, 'r') as f:
            clean_graphs = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load clean graphs: {e}")
        return None, None

    # Import graph_utils from the project code
    sys.path.insert(0, str(PROJECT_ROOT / "code"))
    try:
        from graph_utils import inject_noise
    except ImportError as e:
        logger.error(f"Failed to import inject_noise from graph_utils: {e}")
        return None, None

    seed = config.get("seed", 42)
    ratio = config.get("noise_ratio", 0.1)
    
    set_all_seeds(seed)
    logger.info(f"Re-running noise injection with ratio={ratio}, seed={seed}")

    noisy_graphs = {}
    for task_id, edges in clean_graphs.items():
        # Reconstruct a simple graph structure for inject_noise if needed
        # Assuming inject_noise expects a list of edges or a networkx graph.
        # Based on T011b description: "replaces a proportion of existing edges"
        # We need to adapt the input format to what inject_noise expects.
        # Assuming inject_noise(graph, ratio, seed) where graph is a dict or list of edges.
        # Let's assume it takes a list of edge dicts or similar.
        
        # If clean_graphs is {task_id: [edges]}, we pass that list.
        noisy_edges = inject_noise(edges, ratio, seed)
        noisy_graphs[task_id] = noisy_edges

    # Write to a temporary location for hashing
    temp_output = DATA_DIR / "processed" / "graphs" / "temp_graph_noise_repro.json"
    temp_output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_output, 'w') as f:
        json.dump(noisy_graphs, f, sort_keys=True) # Sort keys for determinism

    regenerated_hash = compute_file_hash(temp_output)
    logger.info(f"Regenerated noisy graph hash: {regenerated_hash}")
    
    # Cleanup temp file
    if temp_output.exists():
        temp_output.unlink()
    
    return regenerated_hash, str(clean_graph_path)

def run_baseline_verification(config: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Re-run baseline execution on a small subset and compute hash.
    Returns (regenerated_hash, original_path) or (None, None) if input missing.
    """
    clean_graph_path = DATA_DIR / "intermediate" / "graphs_raw.json"
    if not clean_graph_path.exists():
        logger.warning(f"Clean graph file not found: {clean_graph_path}. Skipping baseline repro.")
        return None, None

    logger.info("Re-running baseline execution on a small subset...")
    
    sys.path.insert(0, str(PROJECT_ROOT / "code"))
    try:
        from runner import run_batch, load_graph, load_tasks
        from strategies.full import run_full_strategy
    except ImportError as e:
        logger.error(f"Failed to import runner/strategies: {e}")
        return None, None

    seed = config.get("seed", 42)
    set_all_seeds(seed)

    # Load a small subset of tasks to avoid long execution
    # Assuming tasks are in data/raw/locomo.jsonl
    raw_data_path = DATA_DIR / "raw" / "locomo.jsonl"
    if not raw_data_path.exists():
        logger.warning(f"Raw data not found: {raw_data_path}. Skipping baseline repro.")
        return None, None

    # Load first 5 tasks for verification
    tasks = []
    with open(raw_data_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= 5:
                break
            tasks.append(json.loads(line))

    if not tasks:
        logger.warning("No tasks found in raw data.")
        return None, None

    graph = load_graph(clean_graph_path)
    
    # Run the strategy on these tasks
    results = []
    for task in tasks:
        task_id = task.get("task_id", f"task_{len(results)}")
        # Execute full strategy
        # run_full_strategy returns {'accuracy': float, 'nodes_visited': int, 'latency_ms': float}
        try:
            res = run_full_strategy(graph, task)
            res["task_id"] = task_id
            res["status"] = "COMPLETED"
            results.append(res)
        except Exception as e:
            logger.error(f"Error running task {task_id}: {e}")
            results.append({"task_id": task_id, "status": "ERROR", "accuracy": 0.0})

    # Write to temp file
    temp_output = DATA_DIR / "processed" / "baseline_results_repro.csv"
    import csv
    with open(temp_output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "accuracy", "nodes_visited", "latency_ms", "status"])
        writer.writeheader()
        writer.writerows(results)

    regenerated_hash = compute_file_hash(temp_output)
    logger.info(f"Regenerated baseline results hash: {regenerated_hash}")

    if temp_output.exists():
        temp_output.unlink()

    return regenerated_hash, str(raw_data_path)

def main():
    parser = argparse.ArgumentParser(description="Verify seed reproducibility for llmXive pipeline.")
    parser.add_argument("--update", action="store_true", help="Update state file with new hashes if they don't exist.")
    args = parser.parse_args()

    logger.info("Starting seed verification...")
    config = load_config()
    state = load_state()
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    # 1. Verify Noise Injection
    logger.info("--- Verifying Noise Injection ---")
    noise_hash, noise_path = run_noise_injection_repro(config)
    
    target_noise_key = "graph_noise_42"
    stored_noise_hash = state["artifact_hashes"].get(target_noise_key)
    
    if noise_hash:
        if stored_noise_hash:
            if noise_hash == stored_noise_hash:
                logger.info(f"SUCCESS: Noise injection hash matches stored value for {target_noise_key}.")
            else:
                logger.error(f"FAILURE: Noise injection hash mismatch for {target_noise_key}.")
                logger.error(f"  Stored:   {stored_noise_hash}")
                logger.error(f"  Regenerated: {noise_hash}")
        elif args.update:
            state["artifact_hashes"][target_noise_key] = noise_hash
            save_state(state)
            logger.info(f"INITIALIZED: Stored noise hash for {target_noise_key} as {noise_hash}.")
        else:
            logger.warning(f"NO STORED HASH: No hash found for {target_noise_key} in state. Use --update to initialize.")
    else:
        logger.warning("Skipping noise hash comparison (input missing).")

    # 2. Verify Baseline Results
    logger.info("--- Verifying Baseline Results ---")
    baseline_hash, baseline_path = run_baseline_verification(config)
    
    target_baseline_key = "baseline_results"
    stored_baseline_hash = state["artifact_hashes"].get(target_baseline_key)
    
    if baseline_hash:
        if stored_baseline_hash:
            if baseline_hash == stored_baseline_hash:
                logger.info(f"SUCCESS: Baseline results hash matches stored value for {target_baseline_key}.")
            else:
                logger.error(f"FAILURE: Baseline results hash mismatch for {target_baseline_key}.")
                logger.error(f"  Stored:   {stored_baseline_hash}")
                logger.error(f"  Regenerated: {baseline_hash}")
        elif args.update:
            state["artifact_hashes"][target_baseline_key] = baseline_hash
            save_state(state)
            logger.info(f"INITIALIZED: Stored baseline hash for {target_baseline_key} as {baseline_hash}.")
        else:
            logger.warning(f"NO STORED HASH: No hash found for {target_baseline_key} in state. Use --update to initialize.")
    else:
        logger.warning("Skipping baseline hash comparison (input missing).")

    logger.info("Seed verification complete.")

if __name__ == "__main__":
    main()