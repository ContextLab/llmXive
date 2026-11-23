import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress
import json
import logging
import argparse
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def damped_sinusoid(t, A, lambda_decay, omega, phi, C):
    """
    Damped sinusoid model for energy decay:
    E(t) = A * exp(-lambda * t) * cos(omega * t + phi) + C
    
    Parameters:
    -----------
    t : array_like
        Time points
    A : float
        Amplitude of the oscillation
    lambda_decay : float
        Decay rate (positive for dissipation, negative for resonance)
    omega : float
        Angular frequency
    phi : float
        Phase shift
    C : float
        Offset/constant term
        
    Returns:
    --------
    array_like
        Modeled energy values
    """
    return A * np.exp(-lambda_decay * t) * np.cos(omega * t + phi) + C

def extract_decay_rate(t, energy, initial_guess=None):
    """
    Extract decay rate from energy time series by fitting a damped sinusoid.
    
    Parameters:
    -----------
    t : array_like
        Time points (must be post-transient, t > 100)
    energy : array_like
        Energy values corresponding to time points
    initial_guess : tuple, optional
        Initial guess for (A, lambda, omega, phi, C)
        
    Returns:
    --------
    dict
        Dictionary containing:
        - 'decay_rate': fitted lambda value
        - 'r_squared': goodness of fit (R²)
        - 'params': fitted parameters (A, lambda, omega, phi, C)
        - 'status': 'dissipative' if lambda >= 0, 'resonant' if lambda < 0
    """
    t = np.asarray(t)
    energy = np.asarray(energy)
    
    if len(t) != len(energy):
        raise ValueError("Time and energy arrays must have the same length")
    
    if len(t) < 3:
        raise ValueError("Not enough data points for fitting")
    
    # Normalize time for better numerical stability
    t_normalized = t - t[0]
    
    # Initial guesses if not provided
    if initial_guess is None:
        # Estimate amplitude from data range
        A_guess = (energy.max() - energy.min()) / 2
        # Estimate decay rate (assume moderate decay)
        lambda_guess = 0.01
        # Estimate frequency (assume typical oscillator frequency)
        omega_guess = 1.0
        # Phase guess
        phi_guess = 0.0
        # Offset guess
        C_guess = energy.mean()
        
        initial_guess = (A_guess, lambda_guess, omega_guess, phi_guess, C_guess)
    
    try:
        # Fit the model
        popt, pcov = curve_fit(
            damped_sinusoid, 
            t_normalized, 
            energy,
            p0=initial_guess,
            maxfev=10000
        )
        
        A, lambda_decay, omega, phi, C = popt
        
        # Calculate R²
        residuals = energy - damped_sinusoid(t_normalized, *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((energy - np.mean(energy))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Determine status based on decay rate
        # Negative decay rate indicates resonance (energy increasing or not decaying)
        if lambda_decay < 0:
            status = 'resonant'
        else:
            status = 'dissipative'
        
        return {
            'decay_rate': float(lambda_decay),
            'r_squared': float(r_squared),
            'params': {
                'A': float(A),
                'lambda': float(lambda_decay),
                'omega': float(omega),
                'phi': float(phi),
                'C': float(C)
            },
            'status': status
        }
        
    except Exception as e:
        logger.warning(f"Fit failed: {str(e)}")
        # Return failure result
        return {
            'decay_rate': None,
            'r_squared': None,
            'params': None,
            'status': 'fit_failed',
            'error': str(e)
        }

def process_simulation_data(simulation_results, transient_threshold=100):
    """
    Process simulation results to extract decay rates and determine resonance status.
    
    Parameters:
    -----------
    simulation_results : list of dict
        List of simulation result dictionaries, each containing:
        - 'graph_id': unique identifier for the graph
        - 'time': array of time points
        - 'energy': array of energy values
        - 'class': topological class of the graph
        - 'metrics': dict of network metrics
    transient_threshold : float
        Time threshold to separate transient from steady-state (default: 100)
        
    Returns:
    --------
    list of dict
        Processed results with decay rates and resonance status
    """
    processed_results = []
    
    for result in simulation_results:
        graph_id = result.get('graph_id')
        time = np.array(result.get('time', []))
        energy = np.array(result.get('energy', []))
        
        if len(time) == 0 or len(energy) == 0:
            logger.warning(f"No data for graph {graph_id}, skipping")
            continue
        
        # Filter for post-transient phase
        post_transient_mask = time > transient_threshold
        t_post = time[post_transient_mask]
        e_post = energy[post_transient_mask]
        
        if len(t_post) < 3:
            logger.warning(f"Not enough post-transient data for graph {graph_id}")
            processed_results.append({
                'graph_id': graph_id,
                'decay_rate': None,
                'r_squared': None,
                'status': 'insufficient_data',
                'class': result.get('class'),
                'metrics': result.get('metrics', {})
            })
            continue
        
        # Extract decay rate
        decay_result = extract_decay_rate(t_post, e_post)
        
        # Combine with original metadata
        processed_result = {
            'graph_id': graph_id,
            'class': result.get('class'),
            'metrics': result.get('metrics', {}),
            'decay_rate': decay_result['decay_rate'],
            'r_squared': decay_result['r_squared'],
            'status': decay_result['status']
        }
        
        # Add fit parameters if available
        if decay_result['params']:
            processed_result['fit_params'] = decay_result['params']
        
        processed_results.append(processed_result)
        logger.info(f"Processed graph {graph_id}: decay_rate={decay_result['decay_rate']:.4f}, "
                   f"status={decay_result['status']}, R²={decay_result['r_squared']:.4f}")
    
    return processed_results

def main():
    """
    Main function to process simulation results and extract decay rates.
    This script is designed to be run after simulation results are generated.
    """
    parser = argparse.ArgumentParser(description='Extract energy decay rates from simulation results')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to simulation results JSON file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output JSON file with decay rates')
    parser.add_argument('--transient-threshold', type=float, default=100.0,
                      help='Time threshold for transient phase (default: 100)')
    
    args = parser.parse_args()
    
    # Load simulation results
    try:
        with open(args.input, 'r') as f:
            simulation_results = json.load(f)
        logger.info(f"Loaded {len(simulation_results)} simulation results from {args.input}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    # Process results
    processed_results = process_simulation_data(simulation_results, args.transient_threshold)
    
    # Count statuses
    status_counts = {}
    for result in processed_results:
        status = result.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    logger.info(f"Status distribution: {status_counts}")
    
    # Save results
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(args.output, 'w') as f:
            json.dump(processed_results, f, indent=2)
        logger.info(f"Saved processed results to {args.output}")
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")
        sys.exit(1)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total graphs processed: {len(processed_results)}")
    print(f"  Resonant instances: {status_counts.get('resonant', 0)}")
    print(f"  Dissipative instances: {status_counts.get('dissipative', 0)}")
    print(f"  Failed fits: {status_counts.get('fit_failed', 0)}")
    print(f"  Insufficient data: {status_counts.get('insufficient_data', 0)}")

if __name__ == '__main__':
    main()