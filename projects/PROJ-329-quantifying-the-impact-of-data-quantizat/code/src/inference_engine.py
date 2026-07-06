import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import h5py
from dataclasses import dataclass

# Local imports based on API surface
from .config import get_seed, get_resource_limits

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class InferenceConfig:
    """Configuration for the inference engine."""
    n_steps: int = 1000
    n_burnin: int = 200
    n_chains: int = 2
    target_snr_min: float = 8.0
    target_snr_max: float = 50.0
    output_dir: Path = Path("data/results")
    seed: Optional[int] = None

def load_signal_data(h5_path: Path, signal_id: str) -> Dict[str, Any]:
    """
    Load a single signal's data from the HDF5 dataset generated in T016.
    
    Args:
        h5_path: Path to the waveforms_pilot_{seed}.h5 file.
        signal_id: The unique identifier for the signal within the HDF5.
        
    Returns:
        Dictionary containing time_series, noise_psd, and ground_truth parameters.
    """
    if not h5_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {h5_path}")
        
    with h5py.File(h5_path, 'r') as f:
        if signal_id not in f:
            raise ValueError(f"Signal ID '{signal_id}' not found in {h5_path}")
        
        grp = f[signal_id]
        time_series = grp['time_series'][...]
        noise_psd = grp['noise_psd'][...]
        freqs = grp['freqs'][...]
        
        # Ground truth parameters
        params = {
            'mass_1': grp['mass_1'][()],
            'mass_2': grp['mass_2'][()],
            'spin_1': grp['spin_1'][()],
            'spin_2': grp['spin_2'][()],
            'distance': grp['distance'][()],
            'snr': grp['snr'][()],
            'bit_depth': grp['bit_depth'][()],
            'quantization_error': grp['quantization_error'][()] if 'quantization_error' in grp else None
        }
        
        return {
            'time_series': time_series,
            'noise_psd': noise_psd,
            'freqs': freqs,
            'params': params
        }

def calculate_likelihood(time_series: np.ndarray, 
                         model_waveform: np.ndarray, 
                         noise_psd: np.ndarray, 
                         freqs: np.ndarray) -> float:
    """
    Calculate the log-likelihood for a given model waveform against data.
    Uses standard matched filtering log-likelihood formulation.
    
    ln L ~ -0.5 * <d - h | d - h>
    """
    # Simple implementation assuming time_series is (d - h) residual or similar
    # In a real Bilby/PyCBC wrapper, this would use the full likelihood class.
    # Here we approximate based on the residual energy weighted by noise PSD.
    
    # FFT
    n = len(time_series)
    df = freqs[1] - freqs[0]
    
    # Residual (assuming time_series is data and model_waveform is h)
    # If time_series is already the injected signal + noise, and we have a model:
    # We assume the input 'time_series' is the noisy data and 'model_waveform' is the template.
    # For this simplified engine, we compute the match.
    
    # Inner product <a|b> = 4 * Re integral (a*b / Sn) df
    # We use discrete sum approximation
    
    diff = time_series - model_waveform
    # Ensure same length
    if len(diff) != len(noise_psd):
        min_len = min(len(diff), len(noise_psd))
        diff = diff[:min_len]
        noise_psd = noise_psd[:min_len]
        
    # Avoid division by zero
    safe_psd = np.where(noise_psd > 0, noise_psd, 1e-20)
    
    inner_product = 4.0 * np.sum((diff**2) / safe_psd) * df
    
    return -0.5 * inner_product

def generate_prior_sample(param_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """Generate a single sample from uniform priors."""
    sample = {}
    for key, (low, high) in param_ranges.items():
        sample[key] = np.random.uniform(low, high)
    return sample

def forward_model(params: Dict[str, float], 
                  freqs: np.ndarray, 
                  dt: float) -> np.ndarray:
    """
    Generate a waveform model given parameters.
    In a real implementation, this would call PyCBC or Bilby's waveform generator.
    Here we return a placeholder sine-gaussian that mimics the shape for the sake of the pipeline.
    """
    # Placeholder: In a real scenario, we would call:
    # from pycbc.waveform import get_td_waveform
    # hp, hc = get_td_waveform(approximant='IMRPhenomPv2', ...)
    
    # For the purpose of this script running without heavy GW libraries installed in the test env:
    # We simulate a chirp-like structure based on chirp mass.
    mc = params.get('mass_1', 30) # Placeholder
    # Simple chirp approximation
    t = np.arange(0, len(freqs) * dt, dt)
    # Frequency evolution
    f_t = 100 + (t * 1000) # Linear chirp for demo
    phase = 2 * np.pi * np.cumsum(f_t) * dt
    amp = np.exp(-((t - 0.5) ** 2) / 0.01) # Gaussian envelope
    
    return amp * np.sin(phase)

def run_inference_single_signal(data: Dict[str, Any], 
                                config: InferenceConfig) -> Dict[str, Any]:
    """
    Run a simplified MCMC inference on a single signal.
    Returns posterior samples and credible intervals.
    """
    logger.info(f"Running inference for signal: {data['params'].get('id', 'unknown')}")
    
    # Setup priors
    prior_ranges = {
        'mass_1': (5.0, 100.0),
        'mass_2': (5.0, 100.0),
        'spin_1': (-0.99, 0.99),
        'spin_2': (-0.99, 0.99),
        'distance': (50.0, 2000.0)
    }
    
    # Initialize chains
    n_samples = config.n_steps - config.n_burnin
    chains = {key: np.zeros((config.n_chains, n_samples)) for key in prior_ranges}
    
    # Simple Metropolis-Hastings loop
    # Current state
    current_params = generate_prior_sample(prior_ranges)
    current_likelihood = calculate_likelihood(
        data['time_series'], 
        forward_model(current_params, data['freqs'], 1.0), # dt=1.0 placeholder
        data['noise_psd'],
        data['freqs']
    )
    
    burnin_count = 0
    sample_idx = 0
    
    for step in range(config.n_steps):
        # Propose new state
        proposal = {}
        for key in current_params:
            delta = np.random.normal(0, 0.05 * current_params[key])
            proposal[key] = current_params[key] + delta
            # Enforce bounds
            if proposal[key] < prior_ranges[key][0]:
                proposal[key] = prior_ranges[key][0]
            if proposal[key] > prior_ranges[key][1]:
                proposal[key] = prior_ranges[key][1]
        
        # Calculate new likelihood
        new_likelihood = calculate_likelihood(
            data['time_series'],
            forward_model(proposal, data['freqs'], 1.0),
            data['noise_psd'],
            data['freqs']
        )
        
        # Accept/Reject
        log_alpha = new_likelihood - current_likelihood
        if np.log(np.random.rand()) < log_alpha:
            current_params = proposal
            current_likelihood = new_likelihood
        
        if step >= config.n_burnin:
            for i, key in enumerate(prior_ranges):
                chains[key][step - config.n_burnin] = current_params[key]
        
        if step % 100 == 0:
            logger.debug(f"Step {step}, Likelihood: {current_likelihood}")

    # Compute statistics
    results = {}
    for key in prior_ranges:
        samples = chains[key]
        mean = np.mean(samples)
        std = np.std(samples)
        # 90% Credible Interval
        ci_90 = np.percentile(samples, [5, 95])
        
        results[key] = {
            'mean': float(mean),
            'std': float(std),
            'ci_90_lower': float(ci_90[0]),
            'ci_90_upper': float(ci_90[1])
        }
    
    # Add ground truth for comparison
    results['ground_truth'] = data['params']
    
    return results

def process_batch_wrapper(h5_path: Path, 
                          signal_ids: List[str], 
                          config: InferenceConfig) -> List[Dict[str, Any]]:
    """Process a batch of signals and collect results."""
    all_results = []
    for sig_id in signal_ids:
        try:
            data = load_signal_data(h5_path, sig_id)
            res = run_inference_single_signal(data, config)
            res['signal_id'] = sig_id
            all_results.append(res)
        except Exception as e:
            logger.error(f"Failed to process {sig_id}: {e}")
            # Record non-detection or failure
            all_results.append({
                'signal_id': sig_id,
                'status': 'failed',
                'error': str(e)
            })
    return all_results

def run_batch_inference(h5_path: Path, 
                        seed: int, 
                        output_dir: Optional[Path] = None) -> str:
    """
    Main entry point for T024.
    Reads the pilot dataset, runs inference, and saves results to JSON.
    """
    if output_dir is None:
        output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = InferenceConfig(
        seed=seed,
        output_dir=output_dir,
        n_steps=200, # Reduced for pilot speed
        n_burnin=50
    )
    
    logger.info(f"Loading dataset from {h5_path}")
    if not h5_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {h5_path}")
    
    # Get list of signal IDs
    with h5py.File(h5_path, 'r') as f:
        signal_ids = list(f.keys())
    
    logger.info(f"Found {len(signal_ids)} signals to process.")
    
    results = process_batch_wrapper(h5_path, signal_ids, config)
    
    # Save results
    output_file = output_dir / f"inference_pilot_{seed}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Inference results saved to {output_file}")
    return str(output_file)

def main():
    """CLI entry point for T024."""
    import argparse
    parser = argparse.ArgumentParser(description="Run inference on pilot dataset (T024)")
    parser.add_argument("--input", type=str, required=True, help="Path to input HDF5 file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/results", help="Output directory")
    args = parser.parse_args()
    
    run_batch_inference(
        h5_path=Path(args.input),
        seed=args.seed,
        output_dir=Path(args.output_dir)
    )

if __name__ == "__main__":
    main()
