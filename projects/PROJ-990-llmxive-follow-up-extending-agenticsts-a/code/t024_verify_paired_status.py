"""
Task T024: Verify Paired Status.

Ensures Dynamic and Static logs share identical trajectory_id and initial_state_hash.
Writes data/processed/paired_status.json.

Dependencies:
  - data/processed/simulation_logs_dynamic.json (from T017)
  - data/processed/simulation_logs_static.json (from T019)
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_logs(file_path: Path) -> List[Dict[str, Any]]:
    """Load simulation logs from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Simulation log file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle if data is a list or a dict with a specific key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Common patterns in simulation logs
        if 'logs' in data:
            return data['logs']
        elif 'results' in data:
            return data['results']
        elif 'simulations' in data:
            return data['simulations']
        else:
            # If it's a single object, wrap it
            return [data]
    else:
        raise ValueError(f"Unexpected data format in {file_path}: {type(data)}")

def extract_key_pairs(logs: List[Dict[str, Any]]) -> Set[Tuple[str, str]]:
    """
    Extract (trajectory_id, initial_state_hash) pairs from logs.
    Handles various potential field names.
    """
    pairs = set()
    for entry in logs:
        if not isinstance(entry, dict):
            continue
        
        # Try to find trajectory_id
        traj_id = None
        for key in ['trajectory_id', 'traj_id', 'id', 'trajectory']:
            if key in entry:
                traj_id = str(entry[key])
                break
        
        # Try to find initial_state_hash
        state_hash = None
        for key in ['initial_state_hash', 'initial_hash', 'state_hash', 'start_hash', 'initial_state']:
            if key in entry:
                state_hash = str(entry[key])
                break
        
        if traj_id is not None and state_hash is not None:
            pairs.add((traj_id, state_hash))
    
    return pairs

def verify_paired_status(
    dynamic_logs_path: Path,
    static_logs_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Verify that Dynamic and Static logs share identical trajectory_id and initial_state_hash.
    
    Returns a dict with:
      - is_paired: bool
      - valid_trajectory_ids: List[str]
      - excluded_trajectory_ids: List[str]
    """
    logger.info(f"Loading dynamic logs from: {dynamic_logs_path}")
    dynamic_logs = load_simulation_logs(dynamic_logs_path)
    logger.info(f"Loaded {len(dynamic_logs)} dynamic log entries.")

    logger.info(f"Loading static logs from: {static_logs_path}")
    static_logs = load_simulation_logs(static_logs_path)
    logger.info(f"Loaded {len(static_logs)} static log entries.")

    dynamic_pairs = extract_key_pairs(dynamic_logs)
    static_pairs = extract_key_pairs(static_logs)

    logger.info(f"Found {len(dynamic_pairs)} unique (traj_id, hash) pairs in dynamic logs.")
    logger.info(f"Found {len(static_pairs)} unique (traj_id, hash) pairs in static logs.")

    # Identify valid pairs (present in both)
    valid_pairs = dynamic_pairs.intersection(static_pairs)
    
    # Identify excluded pairs (present in one but not the other)
    # We consider a trajectory "excluded" if it doesn't have a matching pair in the other set
    all_pairs = dynamic_pairs.union(static_pairs)
    excluded_pairs = all_pairs - valid_pairs

    # Extract trajectory IDs
    valid_traj_ids = sorted([pid for pid, _ in valid_pairs])
    excluded_traj_ids = sorted(list(set([pid for pid, _ in excluded_pairs])))

    is_paired = len(valid_pairs) > 0 and len(excluded_pairs) == 0
    
    # If there are excluded pairs, it's not fully paired
    if excluded_pairs:
        is_paired = False
        logger.warning(f"Found {len(excluded_pairs)} mismatched entries. Pipeline is not fully paired.")
    else:
        logger.info("Verification successful: All entries are paired.")

    result = {
        "is_paired": is_paired,
        "valid_trajectory_ids": valid_traj_ids,
        "excluded_trajectory_ids": excluded_traj_ids,
        "statistics": {
            "total_dynamic_entries": len(dynamic_logs),
            "total_static_entries": len(static_logs),
            "valid_pairs_count": len(valid_pairs),
            "excluded_pairs_count": len(excluded_pairs)
        }
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Paired status report written to: {output_path}")
    return result

def main():
    """Main entry point for T024."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    
    dynamic_logs_path = data_processed_dir / "simulation_logs_dynamic.json"
    static_logs_path = data_processed_dir / "simulation_logs_static.json"
    output_path = data_processed_dir / "paired_status.json"

    try:
        result = verify_paired_status(dynamic_logs_path, static_logs_path, output_path)
        
        if result["is_paired"]:
            logger.info("T024 PASSED: Dynamic and Static logs are fully paired.")
        else:
            logger.warning(f"T024 COMPLETED with exclusions: {len(result['excluded_trajectory_ids'])} trajectories excluded.")
        
        return 0
    except FileNotFoundError as e:
        logger.error(f"T024 FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"T024 FAILED with unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
