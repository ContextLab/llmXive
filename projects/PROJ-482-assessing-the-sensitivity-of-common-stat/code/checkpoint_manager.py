"""
Checkpoint Manager for long-running simulations.

This module provides functionality to save partial results periodically during
simulation execution to prevent data loss in case of runner termination.

It integrates with the main pipeline to allow resumption from the last checkpoint.
"""
import os
import json
import logging
import pickle
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
from pathlib import Path

from config import SimulationConfig

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = "data/processed/checkpoints"
CHECKPOINT_INTERVAL = 100  # Save every 100 replicates per configuration
CHECKPOINT_FILE_PATTERN = "checkpoint_{scenario_id}_{timestamp}.pkl"
MANIFEST_FILE = "checkpoint_manifest.json"


def ensure_checkpoint_dir() -> str:
    """
    Ensure the checkpoint directory exists.
    
    Returns:
        str: Path to the checkpoint directory.
    """
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    return CHECKPOINT_DIR


def generate_scenario_id(config: Dict[str, Any]) -> str:
    """
    Generate a unique identifier for a simulation scenario.
    
    Args:
        config: Dictionary containing scenario parameters.
        
    Returns:
        str: Unique scenario ID string.
    """
    # Create a hash of the sorted configuration parameters
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:12]


def save_checkpoint(
    scenario_id: str,
    current_replicate: int,
    results: List[Dict[str, Any]],
    config: Dict[str, Any],
    status: str = "running"
) -> str:
    """
    Save a checkpoint of the current simulation state.
    
    Args:
        scenario_id: Unique identifier for the scenario.
        current_replicate: Current replicate count.
        results: List of results collected so far.
        config: Simulation configuration dictionary.
        status: Current status ('running', 'completed', 'failed').
        
    Returns:
        str: Path to the saved checkpoint file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_file = CHECKPOINT_FILE_PATTERN.format(
        scenario_id=scenario_id,
        timestamp=timestamp
    )
    checkpoint_path = os.path.join(CHECKPOINT_DIR, checkpoint_file)
    
    checkpoint_data = {
        "scenario_id": scenario_id,
        "config": config,
        "current_replicate": current_replicate,
        "results": results,
        "status": status,
        "timestamp": timestamp,
        "checksum": hashlib.md5(
            json.dumps(results, sort_keys=True).encode()
        ).hexdigest()
    }
    
    with open(checkpoint_path, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    
    logger.info(f"Checkpoint saved: {checkpoint_path} (replicate {current_replicate})")
    
    # Update manifest
    update_manifest(checkpoint_path, scenario_id, current_replicate, status)
    
    return checkpoint_path


def update_manifest(
    checkpoint_path: str,
    scenario_id: str,
    current_replicate: int,
    status: str
) -> None:
    """
    Update the checkpoint manifest file.
    
    Args:
        checkpoint_path: Path to the checkpoint file.
        scenario_id: Scenario identifier.
        current_replicate: Current replicate count.
        status: Current status.
    """
    manifest_path = os.path.join(CHECKPOINT_DIR, MANIFEST_FILE)
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {"checkpoints": []}
    
    # Remove existing entry for this scenario if present
    manifest["checkpoints"] = [
        cp for cp in manifest["checkpoints"]
        if cp.get("scenario_id") != scenario_id
    ]
    
    # Add current checkpoint
    manifest["checkpoints"].append({
        "scenario_id": scenario_id,
        "checkpoint_file": os.path.basename(checkpoint_path),
        "current_replicate": current_replicate,
        "status": status,
        "timestamp": datetime.now().isoformat()
    })
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_latest_checkpoint(scenario_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the most recent checkpoint for a given scenario.
    
    Args:
        scenario_id: Scenario identifier.
        
    Returns:
        Optional[Dict]: Checkpoint data if found, None otherwise.
    """
    manifest_path = os.path.join(CHECKPOINT_DIR, MANIFEST_FILE)
    
    if not os.path.exists(manifest_path):
        logger.warning("No checkpoint manifest found.")
        return None
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Find the latest checkpoint for this scenario
    scenario_checkpoints = [
        cp for cp in manifest["checkpoints"]
        if cp.get("scenario_id") == scenario_id
    ]
    
    if not scenario_checkpoints:
        logger.warning(f"No checkpoints found for scenario {scenario_id}")
        return None
    
    # Sort by timestamp to get the latest
    scenario_checkpoints.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )
    
    latest_checkpoint = scenario_checkpoints[0]
    checkpoint_file = latest_checkpoint["checkpoint_file"]
    checkpoint_path = os.path.join(CHECKPOINT_DIR, checkpoint_file)
    
    if not os.path.exists(checkpoint_path):
        logger.error(f"Checkpoint file not found: {checkpoint_path}")
        return None
    
    try:
        with open(checkpoint_path, 'rb') as f:
            checkpoint_data = pickle.load(f)
        
        # Verify checksum
        expected_checksum = checkpoint_data.get("checksum")
        actual_checksum = hashlib.md5(
            json.dumps(checkpoint_data.get("results", []), sort_keys=True).encode()
        ).hexdigest()
        
        if expected_checksum != actual_checksum:
            logger.error(f"Checksum mismatch for checkpoint {checkpoint_path}")
            return None
        
        logger.info(f"Loaded checkpoint: {checkpoint_path} (replicate {checkpoint_data['current_replicate']})")
        return checkpoint_data
        
    except Exception as e:
        logger.error(f"Failed to load checkpoint {checkpoint_path}: {e}")
        return None


def should_save_checkpoint(current_replicate: int) -> bool:
    """
    Determine if a checkpoint should be saved based on replicate count.
    
    Args:
        current_replicate: Current replicate count.
        
    Returns:
        bool: True if checkpoint should be saved.
    """
    return current_replicate > 0 and current_replicate % CHECKPOINT_INTERVAL == 0


def get_resume_scenario_ids() -> List[str]:
    """
    Get list of scenario IDs that have incomplete checkpoints.
    
    Returns:
        List[str]: List of scenario IDs with checkpoints in 'running' status.
    """
    manifest_path = os.path.join(CHECKPOINT_DIR, MANIFEST_FILE)
    
    if not os.path.exists(manifest_path):
        return []
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    running_scenarios = [
        cp["scenario_id"]
        for cp in manifest["checkpoints"]
        if cp.get("status") == "running"
    ]
    
    return running_scenarios


def cleanup_old_checkpoints(keep_count: int = 3) -> None:
    """
    Remove old checkpoint files, keeping only the most recent ones per scenario.
    
    Args:
        keep_count: Number of checkpoints to keep per scenario.
    """
    manifest_path = os.path.join(CHECKPOINT_DIR, MANIFEST_FILE)
    
    if not os.path.exists(manifest_path):
        return
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Group checkpoints by scenario_id
    scenario_checkpoints: Dict[str, List[Dict]] = {}
    for cp in manifest["checkpoints"]:
        sid = cp["scenario_id"]
        if sid not in scenario_checkpoints:
            scenario_checkpoints[sid] = []
        scenario_checkpoints[sid].append(cp)
    
    # Sort and remove old checkpoints
    for sid, checkpoints in scenario_checkpoints.items():
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        
        for old_cp in checkpoints[keep_count:]:
            old_path = os.path.join(CHECKPOINT_DIR, old_cp["checkpoint_file"])
            if os.path.exists(old_path):
                os.remove(old_path)
                logger.info(f"Removed old checkpoint: {old_path}")
    
    # Update manifest
    manifest["checkpoints"] = [
        cp for cp in manifest["checkpoints"]
        if cp["scenario_id"] not in scenario_checkpoints or
           any(
               cp["checkpoint_file"] == kept["checkpoint_file"]
               for kept in scenario_checkpoints[cp["scenario_id"]][:keep_count]
           )
    ]
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def main():
    """
    Command-line interface for checkpoint management.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Checkpoint Manager")
    parser.add_argument(
        "--action",
        choices=["list", "cleanup", "load"],
        default="list",
        help="Action to perform"
    )
    parser.add_argument(
        "--scenario-id",
        type=str,
        help="Scenario ID for load action"
    )
    parser.add_argument(
        "--keep-count",
        type=int,
        default=3,
        help="Number of checkpoints to keep per scenario (for cleanup)"
    )
    
    args = parser.parse_args()
    
    if args.action == "list":
        scenarios = get_resume_scenario_ids()
        if scenarios:
            print("Scenarios with active checkpoints:")
            for sid in scenarios:
                print(f"  - {sid}")
        else:
            print("No active checkpoints found.")
            
    elif args.action == "cleanup":
        cleanup_old_checkpoints(keep_count=args.keep_count)
        print(f"Cleanup complete. Kept {args.keep_count} checkpoints per scenario.")
        
    elif args.action == "load":
        if not args.scenario_id:
            print("Error: --scenario-id required for load action")
            return
        
        data = load_latest_checkpoint(args.scenario_id)
        if data:
            print(f"Loaded checkpoint for scenario {args.scenario_id}")
            print(f"  Replicate: {data['current_replicate']}")
            print(f"  Status: {data['status']}")
            print(f"  Results count: {len(data['results'])}")
        else:
            print(f"No checkpoint found for scenario {args.scenario_id}")


if __name__ == "__main__":
    main()
