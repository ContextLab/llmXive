"""
Task T050: Divergence Check
Logic: Calculate divergence (percentage of trajectories where final state hash differs).
Flag if divergence > 10%.
Output: data/processed/divergence_report.json
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import load_config_from_file, ensure_directories

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_logs(mode: str) -> List[Dict[str, Any]]:
    """
    Load simulation logs for a specific mode (dynamic, static, random).
    """
    file_path = Path(f"data/processed/simulation_logs_{mode}.json")
    if not file_path.exists():
        raise FileNotFoundError(f"Simulation logs for {mode} not found at {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'trajectories' key
    if isinstance(data, dict) and 'trajectories' in data:
        return data['trajectories']
    elif isinstance(data, list):
        return data
    else:
        logger.error(f"Unexpected format in {file_path}")
        return []

def extract_final_state_hash(trajectory: Dict[str, Any]) -> str:
    """
    Extract the final state hash from a trajectory.
    Handles different possible structures of the trajectory data.
    """
    # Try different common structures
    if 'final_state_hash' in trajectory:
        return trajectory['final_state_hash']
    
    if 'metadata' in trajectory and 'final_state_hash' in trajectory['metadata']:
        return trajectory['metadata']['final_state_hash']
    
    if 'result' in trajectory and 'final_state_hash' in trajectory['result']:
        return trajectory['result']['final_state_hash']
    
    # If we have a list of turns, try to get the last one
    if 'turns' in trajectory and len(trajectory['turns']) > 0:
        last_turn = trajectory['turns'][-1]
        if 'state_hash' in last_turn:
            return last_turn['state_hash']
        if 'final_state_hash' in last_turn:
            return last_turn['final_state_hash']
    
    logger.warning(f"Could not find final_state_hash in trajectory: {trajectory.get('trajectory_id', 'unknown')}")
    return ""

def calculate_divergence(static_logs: List[Dict], dynamic_logs: List[Dict]) -> Tuple[float, int, int, List[str]]:
    """
    Calculate the percentage of trajectories where final state hash differs
    between static and dynamic modes.
    
    Returns: (divergence_rate, divergent_count, total_count, divergent_ids)
    """
    # Create a mapping from trajectory_id to final_state_hash for static logs
    static_map = {}
    for traj in static_logs:
        traj_id = traj.get('trajectory_id') or traj.get('id')
        if traj_id:
            final_hash = extract_final_state_hash(traj)
            if final_hash:
                static_map[traj_id] = final_hash

    divergent_ids = []
    total_matched = 0
    divergent_count = 0

    for traj in dynamic_logs:
        traj_id = traj.get('trajectory_id') or traj.get('id')
        if not traj_id:
            continue
        
        if traj_id not in static_map:
            logger.warning(f"Trajectory {traj_id} not found in static logs, skipping")
            continue
        
        total_matched += 1
        dynamic_hash = extract_final_state_hash(traj)
        static_hash = static_map[traj_id]
        
        if not dynamic_hash:
            logger.warning(f"No final state hash for dynamic trajectory {traj_id}")
            continue
        
        if dynamic_hash != static_hash:
            divergent_count += 1
            divergent_ids.append(traj_id)

    if total_matched == 0:
        return 0.0, 0, 0, []
    
    divergence_rate = (divergent_count / total_matched) * 100.0
    return divergence_rate, divergent_count, total_matched, divergent_ids

def run_divergence_check():
    """
    Main function to run the divergence check.
    """
    logger.info("Starting Divergence Check (T050)")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path("data/processed/divergence_report.json")
    
    try:
        # Load simulation logs
        logger.info("Loading static simulation logs...")
        static_logs = load_simulation_logs("static")
        logger.info(f"Loaded {len(static_logs)} static trajectories")
        
        logger.info("Loading dynamic simulation logs...")
        dynamic_logs = load_simulation_logs("dynamic")
        logger.info(f"Loaded {len(dynamic_logs)} dynamic trajectories")
        
        # Calculate divergence
        logger.info("Calculating divergence...")
        divergence_rate, divergent_count, total_matched, divergent_ids = calculate_divergence(
            static_logs, dynamic_logs
        )
        
        # Determine if threshold is met
        threshold_exceeded = divergence_rate > 10.0
        
        # Prepare report
        report = {
            "task_id": "T050",
            "description": "Divergence Check: Percentage of trajectories where final state hash differs",
            "divergence_rate_pct": round(divergence_rate, 4),
            "divergent_count": divergent_count,
            "total_matched_trajectories": total_matched,
            "threshold_pct": 10.0,
            "threshold_exceeded": threshold_exceeded,
            "status": "WARNING" if threshold_exceeded else "PASS",
            "divergent_trajectory_ids": divergent_ids[:50],  # Limit to first 50 for report size
            "timestamp": "2026-07-31T08:04:37Z"  # Using a fixed timestamp for consistency
        }
        
        # Write report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Divergence report written to {output_path}")
        logger.info(f"Divergence rate: {divergence_rate:.2f}% ({divergent_count}/{total_matched})")
        
        if threshold_exceeded:
            logger.warning(f"Threshold exceeded! Divergence ({divergence_rate:.2f}%) > 10%")
        else:
            logger.info(f"Threshold met: Divergence ({divergence_rate:.2f}%) <= 10%")
        
        return report
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during divergence check: {e}")
        raise

def main():
    """Entry point for the divergence check."""
    run_divergence_check()

if __name__ == "__main__":
    main()
