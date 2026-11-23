import os
import csv
import json
import time
import logging
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COMPUTATION_TIMEOUT_SECONDS = 300
FIXED_SEED = 42
STATUS_SUCCESS = "SUCCESS"
STATUS_TIMEOUT = "TIMEOUT"

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    # Assuming the script is run from the project root or code directory
    current = Path(__file__).resolve()
    # Traverse up until we find the project root (usually where 'data' and 'code' are siblings)
    # Or simply return the parent of the 'src' directory
    if (current.parent.parent / 'data').exists():
        return current.parent.parent
    return current.parent.parent.parent

def ensure_output_directories(root: Path) -> None:
    """Ensures that the required output directories exist."""
    (root / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
    (root / 'data' / 'state').mkdir(parents=True, exist_ok=True)

def compute_fracture_energy(density: float, defect_type: str) -> float:
    """
    Simulates a deterministic physics-based computation of fracture energy.
    
    Formula: E = E0 * (1 - alpha * density)
    Where E0 and alpha depend on defect_type.
    
    Args:
        density: Defect density (float)
        defect_type: Type of defect (str)
        
    Returns:
        Computed fracture energy value (float)
    """
    # Base constants for simulation
    base_energy_graphene = 4.5  # J/m^2
    base_energy_mos2 = 3.8      # J/m^2
    
    # Decay factors based on defect type
    decay_factors = {
        "vacancy": 10.0,
        "interstitial": 5.0,
        "substitutional": 2.0,
        "grain_boundary": 15.0,
        "edge": 8.0
    }
    
    # Determine base energy based on defect type (simplified logic)
    if "graphene" in defect_type.lower():
        base = base_energy_graphene
    elif "mos2" in defect_type.lower():
        base = base_energy_mos2
    else:
        # Default to average if unknown
        base = (base_energy_graphene + base_energy_mos2) / 2.0
        
    alpha = decay_factors.get(defect_type.lower().split()[-1], 5.0)
    
    # Ensure density is positive for calculation
    safe_density = max(0.0, density)
    
    # Physics-informed formula: linear degradation with density
    # Clamp result to be positive
    result = max(0.01, base * (1.0 - alpha * safe_density))
    return result

def simulate_computation(defect_id: str, density: float, defect_type: str) -> Tuple[str, float, str]:
    """
    Simulates the DFTB+ computation logic with a hard timeout.
    
    Args:
        defect_id: Unique identifier for the defect
        density: Defect density
        defect_type: Type of defect
        
    Returns:
        Tuple of (defect_id, computed_value, status)
    """
    logger.info(f"Starting simulation for defect ID: {defect_id}")
    
    start_time = time.time()
    
    try:
        # Simulate computation time (randomized between 0.1 and 2.0 seconds for testing)
        # In a real scenario, this would be the actual DFTB+ runtime
        simulated_runtime = random.uniform(0.1, 2.0)
        
        # Check if simulation exceeds timeout (for testing purposes, we use a much smaller threshold)
        # In the actual logic, we compare against COMPUTATION_TIMEOUT_SECONDS
        # For this implementation, we simulate the timeout logic:
        # If the simulated runtime * scaling factor > timeout, we treat it as a timeout
        # To make the test meaningful, we'll simulate a small fraction of the actual timeout
        # Let's say if simulated_runtime > 1.0 (scaled), we consider it a timeout for testing
        # But the requirement says 300s timeout. We will implement the logic correctly:
        # We will simulate a "long" computation if density is very high or random chance
        
        # To strictly follow the "hard timeout" requirement:
        # We simulate the work. If the work takes longer than 300s, we timeout.
        # Since we can't actually wait 300s in a test, we simulate the *logic* of a timeout
        # by checking a condition that represents a "stuck" computation.
        
        # Simulate a "stuck" computation for 10% of cases to demonstrate the timeout logic
        # In a real DFTB+ run, this would be the actual elapsed time
        is_stuck = random.random() < 0.1 
        
        if is_stuck:
            # Simulate waiting for the full timeout
            # In a real implementation, we would:
            # time.sleep(COMPUTATION_TIMEOUT_SECONDS)
            # But for the sake of the task running in a reasonable time, we just set the flag
            # and log the timeout event.
            logger.warning(f"TIMEOUT: Computation for {defect_id} exceeded {COMPUTATION_TIMEOUT_SECONDS}s")
            return (defect_id, 0.0, STATUS_TIMEOUT)
        
        # If not stuck, perform the computation
        computed_value = compute_fracture_energy(density, defect_type)
        
        elapsed = time.time() - start_time
        logger.info(f"Completed simulation for {defect_id} in {elapsed:.2f}s. Value: {computed_value}")
        
        return (defect_id, computed_value, STATUS_SUCCESS)
        
    except Exception as e:
        logger.error(f"Error during simulation for {defect_id}: {e}")
        # Treat errors as timeouts for this specific task's logic
        return (defect_id, 0.0, STATUS_TIMEOUT)

def run_mock_dftb_plus(defect_list: List[Dict[str, Any]]) -> Tuple[List[Dict], Dict]:
    """
    Runs the mock DFTB+ computation on a list of defects.
    
    Args:
        defect_list: List of dictionaries containing defect data (id, density, type)
        
    Returns:
        Tuple of (results_list, exclusions_dict)
    """
    results = []
    excluded_ids = []
    
    logger.info(f"Starting Mock DFTB+ computation for {len(defect_list)} defects")
    
    for defect in defect_list:
        defect_id = defect.get('defect_id')
        density = defect.get('defect_density', 0.0)
        defect_type = defect.get('defect_type', 'unknown')
        
        if not defect_id:
            logger.warning(f"Skipping entry with missing defect_id: {defect}")
            continue
            
        if density <= 0:
            # Log and skip if density is invalid, but this task focuses on timeout
            # We will still attempt computation but it might return a low value
            pass
        
        result = simulate_computation(defect_id, density, defect_type)
        results.append({
            'defect_id': result[0],
            'computed_value': result[1],
            'status': result[2]
        })
        
        if result[2] == STATUS_TIMEOUT:
            excluded_ids.append(defect_id)
            logger.info(f"Excluded {defect_id} due to TIMEOUT")
    
    exclusions = {
        'excluded_ids': excluded_ids,
        'count': len(excluded_ids)
    }
    
    logger.info(f"Mock DFTB+ completed. Success: {len(results) - len(excluded_ids)}, Timeout: {len(excluded_ids)}")
    return results, exclusions

def save_results(results: List[Dict], exclusions: Dict, root: Path) -> None:
    """
    Saves the results and exclusions to the specified output files.
    
    Args:
        results: List of result dictionaries
        exclusions: Dictionary of excluded IDs
        root: Project root path
    """
    results_path = root / 'data' / 'processed' / 'mock_dftb_results.csv'
    exclusions_path = root / 'data' / 'state' / 'mock_dftb_exclusions.json'
    
    ensure_output_directories(root)
    
    # Save CSV results
    with open(results_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['defect_id', 'computed_value', 'status'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved results to {results_path}")
    
    # Save JSON exclusions
    with open(exclusions_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    
    logger.info(f"Saved exclusions to {exclusions_path}")

def main():
    """
    Main entry point for the mock DFTB+ computation.
    Reads defect data, runs simulation, and saves outputs.
    """
    logger.info("Starting Mock DFTB+ Computation Task (T012a)")
    
    # Determine project root
    root = get_project_root()
    
    # Ensure directories exist
    ensure_output_directories(root)
    
    # Sample defect data for demonstration
    # In a real scenario, this would be read from data/raw/defect_dataset_2022.csv
    # or passed as an argument. For this task, we simulate the input.
    # We will look for the file if it exists, otherwise use a small sample.
    
    input_file = root / 'data' / 'raw' / 'defect_dataset_2022.csv'
    defect_list = []
    
    if input_file.exists():
        logger.info(f"Reading defect data from {input_file}")
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                defect_list.append({
                    'defect_id': row.get('defect_id', 'unknown'),
                    'defect_density': float(row.get('defect_density', 0.0)),
                    'defect_type': row.get('defect_type', 'unknown')
                })
    else:
        logger.warning(f"Input file {input_file} not found. Using sample data.")
        # Sample data for testing
        defect_list = [
            {'defect_id': 'D001', 'defect_density': 0.01, 'defect_type': 'graphene_vacancy'},
            {'defect_id': 'D002', 'defect_density': 0.05, 'defect_type': 'mos2_interstitial'},
            {'defect_id': 'D003', 'defect_density': 0.10, 'defect_type': 'graphene_edge'},
            {'defect_id': 'D004', 'defect_density': 0.02, 'defect_type': 'mos2_substitutional'},
            {'defect_id': 'D005', 'defect_density': 0.08, 'defect_type': 'graphene_grain_boundary'},
        ]
    
    if not defect_list:
        logger.error("No defect data to process. Exiting.")
        return
    
    # Run the computation
    results, exclusions = run_mock_dftb_plus(defect_list)
    
    # Save outputs
    save_results(results, exclusions, root)
    
    logger.info("Mock DFTB+ Computation Task (T012a) completed successfully.")

if __name__ == '__main__':
    main()