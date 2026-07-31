"""
T017: Execute Dynamic Simulation on the test set.

This script orchestrates the dynamic simulation phase for the test set.
It loads the test split, the trained utility classifier, and the fallback
configuration (if any), then runs the simulator for each trajectory.

Output: data/processed/simulation_logs_dynamic.json
"""
import os
import sys
import json
import logging
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to ensure imports work in various execution contexts
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config_from_file, ensure_directories
from simulator import run_dynamic_simulation, load_raw_trajectory
from splitter import load_processed_data

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'processed' / 'simulation_run.log')
    ]
)
logger = logging.getLogger(__name__)

CONFIG_PATH = project_root / 'code' / 'config.json'
MODEL_PATH = project_root / 'models' / 'layer_utility_classifier.pkl'
FALLBACK_FLAG_PATH = project_root / 'data' / 'processed' / 'fallback_flag.json'
TEST_SET_PATH = project_root / 'data' / 'processed' / 'test_set.csv'
RAW_DATA_DIR = project_root / 'data' / 'raw'
OUTPUT_PATH = project_root / 'data' / 'processed' / 'simulation_logs_dynamic.json'

def load_fallback_flag() -> Optional[Dict[str, Any]]:
    """Load fallback flag if it exists, otherwise return None."""
    if FALLBACK_FLAG_PATH.exists():
        try:
            with open(FALLBACK_FLAG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load fallback flag: {e}")
    return None

def load_test_set() -> List[Dict[str, Any]]:
    """Load the test set from the processed CSV."""
    if not TEST_SET_PATH.exists():
        raise FileNotFoundError(f"Test set not found at {TEST_SET_PATH}. "
                                "Please ensure T014a (splitter) has run successfully.")
    
    logger.info(f"Loading test set from {TEST_SET_PATH}")
    try:
        df = load_processed_data(TEST_SET_PATH)
        if df is None or df.empty:
            raise ValueError("Test set is empty. Cannot proceed with simulation.")
        
        # Convert dataframe to list of dicts for processing
        records = df.to_dict('records')
        logger.info(f"Loaded {len(records)} test trajectories.")
        return records
    except Exception as e:
        logger.error(f"Failed to load test set: {e}")
        raise

def load_model() -> Any:
    """Load the trained utility classifier."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. "
                                "Please ensure T009 (classifier training) has run successfully.")
    
    logger.info(f"Loading model from {MODEL_PATH}")
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_raw_trajectories(trajectory_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Load raw trajectory data for the given IDs from data/raw/.
    Returns a mapping of trajectory_id -> raw_trajectory_data.
    """
    trajectories = {}
    raw_files = list(RAW_DATA_DIR.glob("*.jsonl")) + list(RAW_DATA_DIR.glob("*.json"))
    
    if not raw_files:
        raise FileNotFoundError(f"No raw trajectory files found in {RAW_DATA_DIR}")
    
    logger.info(f"Scanning {len(raw_files)} raw files for {len(trajectory_ids)} trajectories...")
    
    # We expect the raw data to contain the full trajectory history.
    # We will iterate through files to find the requested IDs.
    # This assumes a flat structure where trajectories are in the raw files.
    
    # For efficiency, we might want to index, but for a test set (usually small)
    # a linear scan or loading relevant chunks is acceptable.
    # Given the parser T006a produced metrics_with_moves.csv, we assume the raw data
    # is still needed for the "Current Objective" or full context simulation.
    
    # Simple approach: Load all relevant raw data into memory if small, 
    # or stream if large. Assuming test set is small.
    
    all_raw_data = []
    for f_path in raw_files:
        try:
            if f_path.suffix == '.jsonl':
                with open(f_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            all_raw_data.append(json.loads(line))
            elif f_path.suffix == '.json':
                with open(f_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_raw_data.extend(data)
                    else:
                        all_raw_data.append(data)
        except Exception as e:
            logger.warning(f"Skipping file {f_path} due to error: {e}")
    
    # Map IDs to data
    for item in all_raw_data:
        tid = item.get('trajectory_id') or item.get('id')
        if tid in trajectory_ids:
            trajectories[tid] = item
            if len(trajectories) == len(trajectory_ids):
                break
    
    missing = set(trajectory_ids) - set(trajectories.keys())
    if missing:
        logger.warning(f"Missing raw data for trajectories: {missing}")
    
    return trajectories

def main():
    logger.info("Starting T017: Dynamic Simulation Execution")
    
    # 1. Ensure directories
    ensure_directories()
    
    # 2. Load Config
    try:
        config = load_config_from_file(CONFIG_PATH)
    except FileNotFoundError:
        logger.warning(f"Config file {CONFIG_PATH} not found. Using defaults.")
        config = {}
    
    # 3. Load Dependencies
    fallback_flag = load_fallback_flag()
    test_records = load_test_set()
    model = load_model()
    
    # Extract IDs for raw data lookup
    test_ids = [r.get('trajectory_id') for r in test_records if r.get('trajectory_id')]
    raw_trajectories = load_raw_trajectories(test_ids)
    
    simulation_results = []
    start_time = time.time()
    
    logger.info(f"Running dynamic simulation on {len(test_records)} trajectories...")
    
    for i, record in enumerate(test_records):
        tid = record.get('trajectory_id')
        if not tid:
            logger.warning(f"Skipping record {i}: missing trajectory_id")
            continue
        
        raw_data = raw_trajectories.get(tid)
        if not raw_data:
            logger.warning(f"Skipping {tid}: raw data not found.")
            continue
        
        try:
            # Run the dynamic simulation logic
            # The simulator expects the raw trajectory and the model
            # It handles the token budget, context floor, and layer selection internally
            result = run_dynamic_simulation(
                raw_trajectory=raw_data,
                model=model,
                config=config,
                fallback_flag=fallback_flag
            )
            
            if result:
                simulation_results.append(result)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(test_records)} trajectories.")
                
        except Exception as e:
            logger.error(f"Error simulating trajectory {tid}: {e}", exc_info=True)
            # Continue with other trajectories, log the error
            simulation_results.append({
                "trajectory_id": tid,
                "status": "error",
                "error_message": str(e)
            })
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Simulation complete. Processed {len(simulation_results)} trajectories in {duration:.2f}s.")
    
    # 4. Write Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump({
            "metadata": {
                "task_id": "T017",
                "condition": "dynamic",
                "total_trajectories": len(test_records),
                "successful_simulations": len(simulation_results),
                "duration_seconds": duration,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            "results": simulation_results
        }, f, indent=2)
    
    logger.info(f"Results written to {OUTPUT_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
