"""
Analysis module for User Story 3 and T023.
Computes MSE between injected ground-truth and recovered posterior means.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from src.state_manager import calculate_file_hash, save_state_file

logger = logging.getLogger(__name__)

def load_inference_results(results_path: Path) -> List[Dict[str, Any]]:
    """
    Load inference results from a JSON file.
    Expects a list of dictionaries, each containing:
    - 'injected_params': dict with ground truth (chirp_mass, spin, distance, snr)
    - 'posterior_means': dict with recovered means (chirp_mass, spin, distance)
    - 'converged': bool
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        # Assume it's a single result or malformed, return as list
        return [data] if isinstance(data, dict) else []

def calculate_mse_single(injected: Dict[str, float], recovered: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate MSE for a single signal between injected and recovered parameters.
    Returns a dict with MSE for each parameter.
    """
    mse = {}
    params = ['chirp_mass', 'spin', 'distance']
    
    for param in params:
        if param in injected and param in recovered:
            diff = injected[param] - recovered[param]
            mse[param] = float(diff ** 2)
        else:
            logger.warning(f"Missing parameter {param} in injection or recovery")
            mse[param] = float('nan')
    
    return mse

def compute_mse_metrics(results_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Compute MSE metrics for the entire dataset.
    
    Args:
        results_path: Path to the inference results JSON file
        output_path: Path to save the MSE metrics JSON file
    
    Returns:
        Dictionary containing MSE metrics aggregated by bit-depth and SNR bin
    """
    logger.info(f"Loading inference results from {results_path}")
    results = load_inference_results(results_path)
    
    logger.info(f"Processing {len(results)} inference results")
    
    # Initialize storage for metrics
    metrics = {
        'individual': [],
        'aggregated_by_bit_depth': {},
        'aggregated_by_snr_bin': {},
        'global': {}
    }
    
    # Process individual results
    for i, result in enumerate(results):
        if not result.get('converged', False):
            logger.debug(f"Skipping non-converged result {i}")
            continue
        
        injected = result.get('injected_params', {})
        recovered = result.get('posterior_means', {})
        
        if not injected or not recovered:
            logger.warning(f"Result {i} missing injected or recovered params")
            continue
        
        mse = calculate_mse_single(injected, recovered)
        
        # Store individual result
        individual_record = {
            'index': i,
            'bit_depth': result.get('bit_depth'),
            'snr_bin': result.get('snr_bin'),
            'snr': injected.get('snr'),
            'mse': mse
        }
        metrics['individual'].append(individual_record)
        
        # Aggregate by bit depth
        bit_depth = result.get('bit_depth', 'unknown')
        if bit_depth not in metrics['aggregated_by_bit_depth']:
            metrics['aggregated_by_bit_depth'][bit_depth] = {
                'chirp_mass': [], 'spin': [], 'distance': [], 'count': 0
            }
        
        for param in ['chirp_mass', 'spin', 'distance']:
            if not np.isnan(mse.get(param, float('nan'))):
                metrics['aggregated_by_bit_depth'][bit_depth][param].append(mse[param])
        metrics['aggregated_by_bit_depth'][bit_depth]['count'] += 1
        
        # Aggregate by SNR bin
        snr_bin = result.get('snr_bin', 'unknown')
        if snr_bin not in metrics['aggregated_by_snr_bin']:
            metrics['aggregated_by_snr_bin'][snr_bin] = {
                'chirp_mass': [], 'spin': [], 'distance': [], 'count': 0
            }
        
        for param in ['chirp_mass', 'spin', 'distance']:
            if not np.isnan(mse.get(param, float('nan'))):
                metrics['aggregated_by_snr_bin'][snr_bin][param].append(mse[param])
        metrics['aggregated_by_snr_bin'][snr_bin]['count'] += 1
    
    # Compute averages
    def compute_avg_metrics(data_dict):
        result = {}
        for key, values in data_dict.items():
            if isinstance(values, list) and len(values) > 0:
                result[key] = float(np.mean(values))
            else:
                result[key] = float('nan')
        return result
    
    # Aggregate global metrics
    all_chirp_mass = []
    all_spin = []
    all_distance = []
    
    for bit_data in metrics['aggregated_by_bit_depth'].values():
        all_chirp_mass.extend(bit_data['chirp_mass'])
        all_spin.extend(bit_data['spin'])
        all_distance.extend(bit_data['distance'])
    
    metrics['global'] = {
        'chirp_mass_mse': float(np.mean(all_chirp_mass)) if all_chirp_mass else float('nan'),
        'spin_mse': float(np.mean(all_spin)) if all_spin else float('nan'),
        'distance_mse': float(np.mean(all_distance)) if all_distance else float('nan'),
        'total_converged': len(metrics['individual'])
    }
    
    # Convert lists to averages for output
    output_metrics = {
        'individual': metrics['individual'],
        'aggregated_by_bit_depth': {},
        'aggregated_by_snr_bin': {},
        'global': metrics['global']
    }
    
    for bit_depth, data in metrics['aggregated_by_bit_depth'].items():
        output_metrics['aggregated_by_bit_depth'][bit_depth] = {
            'chirp_mass_mse': float(np.mean(data['chirp_mass'])) if data['chirp_mass'] else float('nan'),
            'spin_mse': float(np.mean(data['spin'])) if data['spin'] else float('nan'),
            'distance_mse': float(np.mean(data['distance'])) if data['distance'] else float('nan'),
            'count': data['count']
        }
    
    for snr_bin, data in metrics['aggregated_by_snr_bin'].items():
        output_metrics['aggregated_by_snr_bin'][snr_bin] = {
            'chirp_mass_mse': float(np.mean(data['chirp_mass'])) if data['chirp_mass'] else float('nan'),
            'spin_mse': float(np.mean(data['spin'])) if data['spin'] else float('nan'),
            'distance_mse': float(np.mean(data['distance'])) if data['distance'] else float('nan'),
            'count': data['count']
        }
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_metrics, f, indent=2)
    
    logger.info(f"MSE metrics saved to {output_path}")
    
    # Record state
    state_path = output_path.parent / 'state.yaml'
    record_state(output_path, state_path)
    
    return output_metrics

def record_state(output_path: Path, state_path: Path):
    """Record the state of the output file."""
    file_hash = calculate_file_hash(output_path)
    
    state_data = {
        'phase': 'T023',
        'timestamp': str(np.datetime64('now')),
        'artifacts': {
            str(output_path): {
                'hash': file_hash,
                'size': output_path.stat().st_size
            }
        }
    }
    
    save_state_file(state_path, state_data)
    logger.info(f"State recorded to {state_path}")

def main():
    """Main entry point for T023: Compute MSE metrics."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compute MSE between injected and recovered parameters')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to inference results JSON file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to save MSE metrics JSON file')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    try:
        metrics = compute_mse_metrics(input_path, output_path)
        logger.info("MSE computation completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Error computing MSE: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    exit(main())
