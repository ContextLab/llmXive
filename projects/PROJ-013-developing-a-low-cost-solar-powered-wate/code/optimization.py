"""
Optimization module for Pareto Frontier analysis.
Implements loading of simulation results, filtering valid solutions,
and preparing data for Pareto frontier calculation.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from utils import get_project_root, get_data_dir, ensure_dir, setup_logging

# Setup logging
logger = setup_logging(__name__)

def load_simulation_results(filepath: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load simulation results from the CSV file generated in T025.
    
    Args:
        filepath: Optional path to the CSV file. Defaults to 
                 'data/processed/simulation_results.csv'.
                
    Returns:
        List of dictionaries containing simulation results.
        
    Raises:
        FileNotFoundError: If the simulation results file does not exist.
        ValueError: If the CSV is empty or missing required columns.
    """
    if filepath is None:
        project_root = get_project_root()
        filepath = project_root / "data" / "processed" / "simulation_results.csv"
    else:
        filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            f"Simulation results file not found: {filepath}. "
            "Ensure T025 (generate_simulation_results) has been completed first."
        )

    results = []
    required_columns = {'material_id', 'geometry_id', 'steady_state_efficiency', 
                       'total_cost', 'convergence_status'}

    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate columns
        if not required_columns.issubset(set(reader.fieldnames or [])):
            missing = required_columns - set(reader.fieldnames or [])
            raise ValueError(f"Missing required columns in {filepath}: {missing}")

        for row_num, row in enumerate(reader, start=2):
            try:
                # Parse numeric fields
                efficiency = float(row['steady_state_efficiency'])
                cost = float(row['total_cost'])
                status = row['convergence_status'].strip().lower()
                
                # Filter for valid (converged) solutions as per T023/T025 logic
                # Only valid solutions should be considered for optimization
                if status != 'valid' and status != 'converged':
                    logger.debug(f"Skipping row {row_num}: invalid convergence status '{status}'")
                    continue
                    
                results.append({
                    'material_id': row['material_id'],
                    'geometry_id': row['geometry_id'],
                    'efficiency': efficiency,
                    'cost': cost,
                    'convergence_status': row['convergence_status']
                })
                
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed row {row_num}: {e}")
                continue

    if not results:
        raise ValueError(
            f"No valid simulation results found in {filepath}. "
            "Check that T023 validation passed and T025 generated data."
        )

    logger.info(f"Loaded {len(results)} valid simulation results from {filepath}")
    return results

def filter_non_dominated_solutions(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter results to keep only non-dominated (potentially Pareto-optimal) solutions.
    
    A solution A dominates solution B if:
    - A.efficiency >= B.efficiency AND A.cost <= B.cost
    - AND at least one of these inequalities is strict (A is strictly better in one dimension)
    
    Since we want to MAXIMIZE efficiency and MINIMIZE cost:
    - A dominates B if A has higher or equal efficiency AND lower or equal cost,
      with at least one strict inequality.
      
    Args:
        results: List of result dictionaries with 'efficiency' and 'cost' keys.
                
    Returns:
        List of non-dominated solutions.
    """
    if not results:
        return []

    non_dominated = []
    
    for candidate in results:
        is_dominated = False
        
        for other in results:
            if candidate is other:
                continue
                
            # Check if 'other' dominates 'candidate'
            # 'other' dominates if:
            #   other.efficiency >= candidate.efficiency AND other.cost <= candidate.cost
            #   AND (other.efficiency > candidate.efficiency OR other.cost < candidate.cost)
            
            eff_other = other['efficiency']
            cost_other = other['cost']
            eff_cand = candidate['efficiency']
            cost_cand = candidate['cost']
            
            if (eff_other >= eff_cand and cost_other <= cost_cand and
                (eff_other > eff_cand or cost_other < cost_cand)):
                is_dominated = True
                break
        
        if not is_dominated:
            non_dominated.append(candidate)
            
    logger.info(f"Filtered {len(non_dominated)} non-dominated solutions from {len(results)} total")
    return non_dominated

def main():
    """
    Main entry point for T029: Load and filter simulation results for optimization.
    
    This function:
    1. Loads simulation results from data/processed/simulation_results.csv
    2. Filters for valid (converged) solutions
    3. Identifies non-dominated solutions
    4. Logs summary statistics
    
    Output: Prints summary to logs; prepares data for subsequent Pareto analysis.
    """
    logger.info("Starting T029: Load and filter simulation results for optimization")
    
    try:
        # Load results
        results = load_simulation_results()
        logger.info(f"Total valid results loaded: {len(results)}")
        
        # Filter non-dominated
        non_dominated = filter_non_dominated_solutions(results)
        logger.info(f"Non-dominated solutions: {len(non_dominated)}")
        
        if non_dominated:
            eff_values = [r['efficiency'] for r in non_dominated]
            cost_values = [r['cost'] for r in non_dominated]
            
            logger.info(f"Efficiency range: [{min(eff_values):.4f}, {max(eff_values):.4f}]")
            logger.info(f"Cost range: [{min(cost_values):.2f}, {max(cost_values):.2f}]")
            
            # Log the non-dominated solutions for verification
            logger.info("Non-dominated solutions:")
            for sol in non_dominated:
                logger.info(f"  {sol['material_id']}/{sol['geometry_id']}: "
                          f"eff={sol['efficiency']:.4f}, cost={sol['cost']:.2f}")
        else:
            logger.warning("No non-dominated solutions found. Check input data quality.")
            
        logger.info("T029 completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during T029: {e}")
        raise

if __name__ == "__main__":
    main()
