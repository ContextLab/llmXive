import os
import sys
import json
import logging
import argparse
import random
import hashlib
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config_from_file, ensure_directories
from simulator import load_raw_trajectory, estimate_layer_tokens, calculate_total_tokens

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_test_set_ids() -> list:
    """
    Loads the list of trajectory IDs from the test set CSV.
    Expects data/processed/test_set.csv to exist with a 'trajectory_id' column.
    """
    import pandas as pd
    test_set_path = PROJECT_ROOT / "data" / "processed" / "test_set.csv"
    
    if not test_set_path.exists():
        raise FileNotFoundError(f"Test set file not found: {test_set_path}. "
                                "Ensure T014a (splitter) has run successfully.")
    
    try:
        df = pd.read_csv(test_set_path)
        if 'trajectory_id' not in df.columns:
            raise ValueError("Test set CSV is missing required 'trajectory_id' column.")
        
        ids = df['trajectory_id'].tolist()
        logger.info(f"Loaded {len(ids)} trajectory IDs from test set.")
        return ids
    except Exception as e:
        logger.error(f"Failed to load test set IDs: {e}")
        raise

def run_random_baseline_simulation(config: dict, trajectory_ids: list, k: int = 2):
    """
    Executes the 'No-Store Random' baseline.
    Logic: Select exactly k=2 layers uniformly at random from the available set for every turn.
    Output: data/processed/simulation_logs_random.json
    """
    raw_data_path = PROJECT_ROOT / "data" / "raw" / "agenticsts_trajectories.jsonl"
    output_path = PROJECT_ROOT / "data" / "processed" / "simulation_logs_random.json"
    
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw trajectory data not found: {raw_data_path}. "
                                "Ensure T005b (data ingest) has run successfully.")

    ensure_directories([output_path.parent])

    results = []
    
    # Load raw data once if possible, or stream if large (assuming manageable size for now based on context)
    # We will load line by line to handle potential large files efficiently
    raw_trajectories = {}
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Assuming 'trajectory_id' is the key
                tid = data.get('trajectory_id')
                if tid:
                    raw_trajectories[tid] = data
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSON line in raw data.")
                continue

    if not raw_trajectories:
        raise ValueError("No valid trajectories found in raw data file.")

    for tid in trajectory_ids:
        if tid not in raw_trajectories:
            logger.warning(f"Trajectory ID {tid} not found in raw data. Skipping.")
            continue

        traj_data = raw_trajectories[tid]
        trajectory_log = {
            "trajectory_id": tid,
            "baseline_type": "random",
            "k": k,
            "turns": []
        }

        # Extract turns from the trajectory data
        # Assuming the structure has a 'turns' or similar list. 
        # If the schema varies, we adapt to the 'turns' key if present, else iterate structure.
        turns = traj_data.get('turns', [])
        
        # If the data structure is flat or different, we need to handle it.
        # Based on typical AgenticSTS, it's a list of turns.
        if not isinstance(turns, list):
            # Fallback: if turns is not a list, maybe the whole object is one turn?
            # For now, assume standard structure. If empty, we log.
            logger.warning(f"Trajectory {tid} has no 'turns' list. Skipping turns processing.")
            continue

        total_tokens_used = 0

        for turn_idx, turn_data in enumerate(turns):
            # Get available layers for this turn
            # Assuming 'legal_moves' or 'available_layers' exists in turn_data or root
            # Based on T006a output 'metrics_with_moves.csv', we expect 'legal_moves'
            available_layers = turn_data.get('available_layers', [])
            
            # If available_layers is missing, try to derive from 'legal_moves' if present
            if not available_layers and 'legal_moves' in turn_data:
                available_layers = turn_data['legal_moves']
            
            if not available_layers:
                logger.warning(f"Turn {turn_idx} in trajectory {tid} has no available layers.")
                continue

            # Random Selection Logic: Select exactly k uniformly at random
            # If available layers < k, select all (or handle as error? Task says "select exactly k")
            # We will select min(k, len(available)) to avoid crash, but log if count mismatch.
            if len(available_layers) < k:
                logger.warning(f"Turn {turn_idx} in trajectory {tid} has only {len(available_layers)} layers, "
                               f"requesting {k}. Selecting all.")
                selected_layers = available_layers
            else:
                selected_layers = random.sample(available_layers, k)

            # Estimate tokens for selected layers
            # We need a way to estimate tokens. If raw data has 'tokens' field, use it.
            # Otherwise, we might need a heuristic or the engine_runner estimate.
            # For this baseline, we assume the raw data or a helper function can estimate.
            # Since we don't have the engine running here, we estimate based on available data.
            # If 'tokens' is in turn_data for each layer, sum them.
            # If not, we use a placeholder estimate or the simulator's estimate function if it can handle mock data.
            
            # Let's assume the raw data contains 'layer_tokens' or similar, or we estimate 50 tokens per layer as a baseline
            # if specific counts aren't available in the raw JSONL for this task.
            # However, T019 and T017 rely on this. Let's try to use the simulator's estimate if possible.
            # But simulator expects full trajectory context.
            # Simple heuristic: count characters * 0.5 or assume fixed if not present.
            # To be safe and consistent with T019/T017, we will sum the 'tokens' field if present in the selected layers data.
            
            turn_token_count = 0
            for layer in selected_layers:
                # If layer is a dict with 'tokens', use it. If string, estimate.
                if isinstance(layer, dict) and 'tokens' in layer:
                    turn_token_count += layer['tokens']
                elif isinstance(layer, str):
                    # Heuristic: 1 token ~ 4 chars
                    turn_token_count += int(len(layer) / 4)
                else:
                    turn_token_count += 50 # Default estimate

            total_tokens_used += turn_token_count

            turn_log = {
                "turn_index": turn_idx,
                "available_layers_count": len(available_layers),
                "selected_layers": selected_layers,
                "k_selected": len(selected_layers),
                "estimated_tokens": turn_token_count
            }
            trajectory_log["turns"].append(turn_log)

        trajectory_log["total_tokens"] = total_tokens_used
        results.append(trajectory_log)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Random baseline simulation complete. Output written to {output_path}")
    return results

def main():
    """
    Entry point for the random baseline execution.
    """
    config = load_config_from_file()
    if not config:
        # Default config if file missing, though T004 should have created it
        config = {"K_RANDOM_BASELINE": 2}
    
    k = config.get("K_RANDOM_BASELINE", 2)
    
    try:
        trajectory_ids = load_test_set_ids()
        run_random_baseline_simulation(config, trajectory_ids, k)
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during random baseline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
