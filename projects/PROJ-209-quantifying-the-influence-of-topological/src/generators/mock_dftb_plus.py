"""
Mock DFTB+ Computation Logic for T012a.

This module simulates DFTB+ computations for missing fracture energy values.
It accepts a list of defect IDs, simulates a computation with a hard timeout,
and returns physically constrained values or a TIMEOUT status.
"""

import os
import csv
import json
import time
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MOCK_TIMEOUT_SECONDS = 300
DETERMINISTIC_SEED = 42
OUTPUT_RESULTS_PATH = "data/processed/mock_dftb_results.csv"
OUTPUT_EXCLUSIONS_PATH = "data/state/mock_dftb_exclusions.json"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def ensure_output_directories() -> None:
    """Ensure output directories exist."""
    project_root = get_project_root()
    os.makedirs(project_root / "data" / "processed", exist_ok=True)
    os.makedirs(project_root / "data" / "state", exist_ok=True)


def compute_physical_value(defect_density: float, defect_type: str, seed: int) -> float:
    """
    Compute a physically constrained fracture energy value based on defect density and type.

    This is a deterministic formula simulating DFTB+ output.
    Formula: E = E0 * (1 - alpha * density^beta) + noise_factor
    Where E0 is base energy, alpha and beta are material-specific constants.
    """
    random.seed(seed)
    
    # Base parameters (simulated material constants)
    E0 = 10.0  # Base fracture energy in J/m^2
    
    # Material-specific factors
    if "graphene" in defect_type.lower():
        alpha = 0.5
        beta = 0.8
    elif "mos2" in defect_type.lower():
        alpha = 0.3
        beta = 0.7
    else:
        alpha = 0.4
        beta = 0.75
    
    # Ensure defect_density is positive
    density = max(defect_density, 1e-6)
    
    # Compute value with physical constraints (must be positive)
    value = E0 * (1 - alpha * (density ** beta))
    
    # Add small deterministic noise based on seed
    noise = random.uniform(-0.01, 0.01)
    value += noise
    
    # Ensure physical constraint: value must be positive
    value = max(value, 0.1)
    
    return round(value, 6)


def simulate_dftb_computation(
    defect_id: str,
    defect_density: float,
    defect_type: str,
    timeout_seconds: int = MOCK_TIMEOUT_SECONDS
) -> Tuple[Optional[float], str]:
    """
    Simulate a DFTB+ computation with a hard timeout.
    
    Args:
        defect_id: Unique identifier for the defect
        defect_density: Defect density value
        defect_type: Type of defect (e.g., 'vacancy', 'substitution')
        timeout_seconds: Hard timeout in seconds
        
    Returns:
        Tuple of (computed_value, status) where status is 'SUCCESS' or 'TIMEOUT'
    """
    start_time = time.time()
    
    try:
        # Simulate computation time (usually very fast for mock, but we respect timeout)
        # In a real scenario, this would be the actual DFTB+ computation time
        # For mock purposes, we'll simulate a short computation
        computation_time = random.uniform(0.01, 0.1)  # 10-100ms for mock
        
        if computation_time > timeout_seconds:
            # This should rarely happen in mock, but handle it
            logger.warning(f"Simulated computation for {defect_id} exceeded timeout")
            return None, "TIMEOUT"
        
        # Simulate the computation
        time.sleep(computation_time)
        
        # Compute the physical value
        value = compute_physical_value(defect_density, defect_type, DETERMINISTIC_SEED)
        
        elapsed = time.time() - start_time
        logger.info(f"Computation for {defect_id} completed in {elapsed:.2f}s with value {value}")
        
        return value, "SUCCESS"
        
    except Exception as e:
        logger.error(f"Error during computation for {defect_id}: {str(e)}")
        return None, "TIMEOUT"


def run_mock_dftb_analysis(
    defect_ids: List[str],
    defect_data: Dict[str, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run mock DFTB+ analysis on a list of defect IDs.
    
    Args:
        defect_ids: List of defect IDs to process
        defect_data: Dictionary mapping defect_id to its properties (density, type, etc.)
        
    Returns:
        Tuple of (results_list, exclusions_dict)
    """
    results = []
    excluded_ids = []
    
    logger.info(f"Starting mock DFTB+ analysis for {len(defect_ids)} defects")
    
    for defect_id in defect_ids:
        if defect_id not in defect_data:
            logger.warning(f"Defect ID {defect_id} not found in defect_data, skipping")
            continue
        
        data = defect_data[defect_id]
        defect_density = data.get('defect_density', 0.0)
        defect_type = data.get('defect_type', 'unknown')
        
        # Simulate computation
        computed_value, status = simulate_dftb_computation(
            defect_id=defect_id,
            defect_density=defect_density,
            defect_type=defect_type,
            timeout_seconds=MOCK_TIMEOUT_SECONDS
        )
        
        result_entry = {
            'defect_id': defect_id,
            'computed_value': computed_value if computed_value is not None else None,
            'status': status
        }
        results.append(result_entry)
        
        if status == "TIMEOUT":
            excluded_ids.append(defect_id)
            logger.warning(f"Defect {defect_id} timed out and will be excluded")
        
        # Log status as required by task
        if status == "TIMEOUT":
            logger.info(f"[MISSING: timeout] for defect {defect_id}")
    
    exclusions_dict = {
        'excluded_ids': excluded_ids,
        'count': len(excluded_ids)
    }
    
    logger.info(f"Mock DFTB+ analysis complete. {len(excluded_ids)} defects excluded due to timeout.")
    
    return results, exclusions_dict


def save_results_to_csv(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Save results to CSV file."""
    project_root = get_project_root()
    full_path = project_root / output_path
    
    with open(full_path, 'w', newline='') as csvfile:
        fieldnames = ['defect_id', 'computed_value', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    logger.info(f"Results saved to {full_path}")


def save_exclusions_to_json(
    exclusions: Dict[str, Any],
    output_path: str
) -> None:
    """Save exclusions to JSON file."""
    project_root = get_project_root()
    full_path = project_root / output_path
    
    with open(full_path, 'w') as jsonfile:
        json.dump(exclusions, jsonfile, indent=2)
    
    logger.info(f"Exclusions saved to {full_path}")


def load_defect_data_from_csv(csv_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load defect data from CSV file.
    
    Args:
        csv_path: Path to the CSV file containing defect data
        
    Returns:
        Dictionary mapping defect_id to its properties
    """
    project_root = get_project_root()
    full_path = project_root / csv_path
    
    defect_data = {}
    
    if not full_path.exists():
        logger.error(f"Defect data file not found: {full_path}")
        return defect_data
    
    with open(full_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            defect_id = row.get('defect_id')
            if defect_id:
                defect_data[defect_id] = {
                    'defect_density': float(row.get('defect_density', 0.0)),
                    'defect_type': row.get('defect_type', 'unknown'),
                    'fracture_energy': row.get('fracture_energy', None)
                }
    
    return defect_data


def main():
    """
    Main function to run the mock DFTB+ analysis.
    
    This function:
    1. Loads defect data from the raw defect dataset
    2. Identifies defects with missing fracture energy
    3. Runs mock DFTB+ computation for those defects
    4. Saves results and exclusions to output files
    """
    ensure_output_directories()
    
    # Load defect data
    defect_data_path = "data/raw/defect_dataset_2022.csv"
    defect_data = load_defect_data_from_csv(defect_data_path)
    
    if not defect_data:
        logger.warning("No defect data found. Creating empty results.")
        # Create empty results
        save_results_to_csv([], OUTPUT_RESULTS_PATH)
        save_exclusions_to_json({'excluded_ids': [], 'count': 0}, OUTPUT_EXCLUSIONS_PATH)
        return
    
    # Identify defects with missing fracture energy
    missing_fracture_energy_ids = [
        defect_id for defect_id, data in defect_data.items()
        if data.get('fracture_energy') is None or data.get('fracture_energy') == ''
    ]
    
    logger.info(f"Found {len(missing_fracture_energy_ids)} defects with missing fracture energy")
    
    if not missing_fracture_energy_ids:
        logger.info("No defects with missing fracture energy. Creating empty results.")
        save_results_to_csv([], OUTPUT_RESULTS_PATH)
        save_exclusions_to_json({'excluded_ids': [], 'count': 0}, OUTPUT_EXCLUSIONS_PATH)
        return
    
    # Run mock DFTB+ analysis
    results, exclusions = run_mock_dftb_analysis(missing_fracture_energy_ids, defect_data)
    
    # Save results
    save_results_to_csv(results, OUTPUT_RESULTS_PATH)
    save_exclusions_to_json(exclusions, OUTPUT_EXCLUSIONS_PATH)
    
    logger.info("Mock DFTB+ analysis completed successfully")


if __name__ == "__main__":
    main()
