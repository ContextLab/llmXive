import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from utils import get_project_root, get_data_dir, ensure_dir, setup_logging

# Constants for Duffie & Beckman reference
DUFFIE_BECKMAN_MEAN_EFFICIENCY = 0.45
EFFICIENCY_TOLERANCE_FRACTION = 0.10  # ±10%

logger = logging.getLogger(__name__)

def calculate_energy_balance_closure(result: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Perform Primary Validation: Check Energy Balance Closure.
    Input Energy ≈ Output Energy + Losses.
    
    Args:
        result: Simulation result dictionary containing energy terms.
        
    Returns:
        Tuple of (is_closed, relative_error).
        is_closed is True if relative error < 1e-6 (strict closure).
    """
    input_energy = result.get('input_energy', 0.0)
    output_energy = result.get('output_energy', 0.0)
    losses = result.get('losses', 0.0)
    
    if input_energy <= 0:
        logger.warning("Input energy is zero or negative, cannot calculate closure.")
        return False, float('inf')
        
    total_output = output_energy + losses
    relative_error = abs(input_energy - total_output) / input_energy
    
    is_closed = relative_error < 1e-6
    return is_closed, relative_error

def check_efficiency_against_duffie_beckman(
    efficiency: float, 
    tolerance_fraction: float = EFFICIENCY_TOLERANCE_FRACTION,
    mean_efficiency: float = DUFFIE_BECKMAN_MEAN_EFFICIENCY
) -> bool:
    """
    Perform Secondary Check: Log if calculated efficiency falls within ±10% 
    of the mean efficiency (0.45) from Duffie & Beckman as a warning.
    
    NOTE: This check is for logging/warning purposes ONLY. 
    It does NOT exclude the data point from results.
    
    Args:
        efficiency: Calculated time-averaged thermal efficiency.
        tolerance_fraction: Fractional tolerance (default 0.10 for ±10%).
        mean_efficiency: Reference mean efficiency from Duffie & Beckman.
        
    Returns:
        True if efficiency is within the tolerance range, False otherwise.
    """
    lower_bound = mean_efficiency * (1 - tolerance_fraction)
    upper_bound = mean_efficiency * (1 + tolerance_fraction)
    
    is_within_range = lower_bound <= efficiency <= upper_bound
    
    if is_within_range:
        logger.warning(
            f"Efficiency {efficiency:.4f} is within ±10% of Duffie & Beckman "
            f"mean ({mean_efficiency}). Range: [{lower_bound:.4f}, {upper_bound:.4f}]. "
            "This is a warning only; data point is NOT excluded."
        )
    else:
        logger.info(
            f"Efficiency {efficiency:.4f} is outside ±10% of Duffie & Beckman "
            f"mean ({mean_efficiency}). Range: [{lower_bound:.4f}, {upper_bound:.4f}]. "
            "Data point retained as per spec."
        )
        
    return is_within_range

def validate_simulation_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single simulation result by performing both primary and secondary checks.
    
    Primary Check (T023): Energy Balance Closure - EXCLUDES data if failed.
    Secondary Check (T024): Duffie & Beckman comparison - LOGS warning only.
    
    Args:
        result: Dictionary containing simulation results and metadata.
        
    Returns:
        Dictionary with validation status and metrics.
        If primary check fails, 'is_valid' is False.
    """
    validation_result = {
        'is_valid': True,
        'energy_balance_closed': False,
        'energy_balance_error': float('inf'),
        'duffie_beckman_warning': False,
        'efficiency': result.get('steady_state_efficiency', result.get('time_averaged_efficiency', 0.0))
    }
    
    # Primary Check: Energy Balance Closure
    is_closed, error = calculate_energy_balance_closure(result)
    validation_result['energy_balance_closed'] = is_closed
    validation_result['energy_balance_error'] = error
    
    if not is_closed:
        validation_result['is_valid'] = False
        logger.error(
            f"Energy balance closure FAILED for {result.get('material_id', 'unknown')} "
            f"x {result.get('geometry_id', 'unknown')}. Error: {error:.2e}. "
            "Data point EXCLUDED."
        )
        return validation_result
        
    logger.info(
        f"Energy balance closure PASSED for {result.get('material_id', 'unknown')} "
        f"x {result.get('geometry_id', 'unknown')}. Error: {error:.2e}."
    )
    
    # Secondary Check: Duffie & Beckman comparison (WARNING ONLY)
    if validation_result['efficiency'] > 0:
        within_range = check_efficiency_against_duffie_beckman(validation_result['efficiency'])
        validation_result['duffie_beckman_warning'] = within_range
    else:
        logger.warning(
            f"Cannot compare efficiency (value is 0) for {result.get('material_id', 'unknown')} "
            f"x {result.get('geometry_id', 'unknown')} against Duffie & Beckman."
        )
        
    return validation_result

def run_batch_validation(results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run validation on a batch of simulation results.
    
    Args:
        results: List of simulation result dictionaries.
        
    Returns:
        Tuple of (valid_results, invalid_results).
    """
    valid_results = []
    invalid_results = []
    
    for result in results:
        validation = validate_simulation_result(result)
        if validation['is_valid']:
            valid_results.append(result)
        else:
            invalid_results.append(result)
            
    logger.info(f"Batch validation complete: {len(valid_results)} valid, {len(invalid_results)} excluded.")
    return valid_results, invalid_results

def save_validation_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save validation results to a CSV file.
    
    Args:
        results: List of validated result dictionaries.
        output_path: Path to the output CSV file.
    """
    ensure_dir(os.path.dirname(output_path))
    
    fieldnames = [
        'material_id', 'geometry_id', 'steady_state_efficiency', 
        'total_cost', 'convergence_status', 'is_valid',
        'energy_balance_closed', 'energy_balance_error', 'duffie_beckman_warning'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row = {
                'material_id': result.get('material_id', ''),
                'geometry_id': result.get('geometry_id', ''),
                'steady_state_efficiency': result.get('steady_state_efficiency', 0.0),
                'total_cost': result.get('total_cost', 0.0),
                'convergence_status': result.get('convergence_status', ''),
                'is_valid': True,  # Only valid results should be passed here
                'energy_balance_closed': True,
                'energy_balance_error': 0.0,
                'duffie_beckman_warning': False
            }
            # Update with actual validation data if available
            if 'validation' in result:
                row.update({
                    'energy_balance_closed': result['validation'].get('energy_balance_closed', False),
                    'energy_balance_error': result['validation'].get('energy_balance_error', 0.0),
                    'duffie_beckman_warning': result['validation'].get('duffie_beckman_warning', False)
                })
            writer.writerow(row)

def main():
    """
    Main entry point for validation script.
    Loads simulation results, performs validation, and saves filtered results.
    """
    setup_logging()
    project_root = get_project_root()
    
    # Paths
    input_path = project_root / 'data' / 'processed' / 'simulation_results_unvalidated.csv'
    output_path = project_root / 'data' / 'processed' / 'simulation_results.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("Skipping validation. Ensure T022 has generated the unvalidated results file.")
        return
        
    # Load results
    results = []
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['steady_state_efficiency'] = float(row.get('steady_state_efficiency', 0.0))
            row['total_cost'] = float(row.get('total_cost', 0.0))
            row['input_energy'] = float(row.get('input_energy', 0.0))
            row['output_energy'] = float(row.get('output_energy', 0.0))
            row['losses'] = float(row.get('losses', 0.0))
            results.append(row)
    
    logger.info(f"Loaded {len(results)} simulation results for validation.")
    
    # Run validation
    valid_results, invalid_results = run_batch_validation(results)
    
    # Save valid results
    if valid_results:
        save_validation_results(valid_results, str(output_path))
        logger.info(f"Saved {len(valid_results)} valid results to {output_path}")
    else:
        logger.warning("No valid results after validation. Output file not created.")
        
    logger.info(f"Excluded {len(invalid_results)} results due to failed energy balance closure.")

if __name__ == '__main__':
    main()