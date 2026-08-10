import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper
from src.analysis.control_run import (
    load_sample_text,
    tokenize_sequences,
    extract_activations,
    compute_coherence_metric,
    run_baseline_forward_pass,
    run_oscillatory_forward_pass,
    save_activations,
)
from src.analysis.spectral import compute_welch_psd, calculate_snr
import yaml

def load_config(config_path: str = "config/default.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def run_frequency_sweep(
    model: DistilBERTWrapper,
    tokenizer,
    sequences: List[str],
    frequency_range: List[int],
    output_path: str,
) -> pd.DataFrame:
    """
    Iterate relative frequencies across a range of cycle counts per sequence.
    
    Args:
        model: The base DistilBERT model.
        tokenizer: The tokenizer for the model.
        sequences: List of input text sequences.
        frequency_range: List of relative frequencies (cycles per sequence) to test.
        output_path: Path to save the results CSV.
        
    Returns:
        DataFrame containing the sweep results.
    """
    results = []
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting frequency sweep with {len(frequency_range)} frequencies...")
    
    for freq in frequency_range:
        print(f"  Processing frequency: {freq} cycles/sequence")
        
        # Run oscillatory forward pass with current frequency
        activations = run_oscillatory_forward_pass(
            model=model,
            tokenizer=tokenizer,
            sequences=sequences,
            frequency=freq,
        )
        
        # Calculate metrics for each layer/head if available
        # For simplicity, we aggregate across layers/heads for the sweep
        # In a more detailed implementation, we could store per-head data
        
        # Compute spectral features
        if activations and len(activations) > 0:
            # Example: aggregate activations (assuming shape [batch, seq_len, hidden])
            # We'll compute PSD on the mean activation across batch and hidden dims
            mean_activations = np.mean(activations, axis=(0, 2))  # Shape: [seq_len]
            
            if len(mean_activations) > 1:
                # Compute Welch PSD
                freqs, psd = compute_welch_psd(mean_activations, fs=1.0)  # fs=1 for relative frequency
                
                # Calculate SNR if possible
                # Assuming we have a target band (e.g., around the injected frequency)
                # This is a simplified approach; a real implementation would define bands more carefully
                try:
                    snr_db = calculate_snr(psd, freqs, target_freq=freq, bandwidth=2.0)
                except Exception as e:
                    snr_db = np.nan
                    
                results.append({
                    "frequency_cycles_per_seq": freq,
                    "snr_db": snr_db,
                    "psd_peak_freq": freqs[np.argmax(psd)] if len(psd) > 0 else np.nan,
                    "psd_peak_power": float(np.max(psd)) if len(psd) > 0 else np.nan,
                    "status": "success"
                })
            else:
                results.append({
                    "frequency_cycles_per_seq": freq,
                    "snr_db": np.nan,
                    "psd_peak_freq": np.nan,
                    "psd_peak_power": np.nan,
                    "status": "insufficient_data"
                })
        else:
            results.append({
                "frequency_cycles_per_seq": freq,
                "snr_db": np.nan,
                "psd_peak_freq": np.nan,
                "psd_peak_power": np.nan,
                "status": "no_activations"
            })
            
    # Create DataFrame and save
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    print(f"Sweep results saved to {output_path}")
    
    return df_results

def main():
    """Main entry point for the frequency sweep experiment."""
    # Load configuration
    config = load_config()
    
    # Extract parameters
    seed = config.get("seed", 42)
    np.random.seed(seed)
    
    # Frequency range for the sweep (cycles per sequence)
    # Based on reviewer feedback, we test a range to find the optimal frequency
    frequency_range = config.get("frequency_sweep", {
        "min": 1,
        "max": 20,
        "step": 1
    })
    freq_min = frequency_range.get("min", 1)
    freq_max = frequency_range.get("max", 20)
    freq_step = frequency_range.get("step", 1)
    frequencies = list(range(freq_min, freq_max + 1, freq_step))
    
    # Output path
    output_path = config.get("output_paths", {}).get("sweep_results", "data/processed/sweep_results.csv")
    
    # Load sample text
    sample_text = load_sample_text()
    if not sample_text:
        print("Error: No sample text loaded. Exiting.")
        return
        
    # Tokenize sequences
    sequences = tokenize_sequences(sample_text, max_length=512)
    if not sequences:
        print("Error: No sequences generated. Exiting.")
        return
        
    # Load model
    print("Loading DistilBERT model...")
    model = load_distilbert_cpu()
    if model is None:
        print("Error: Failed to load model. Exiting.")
        return
        
    tokenizer = model.tokenizer  # Assuming DistilBERTWrapper has tokenizer attribute
    
    # Run frequency sweep
    print(f"Running frequency sweep from {freq_min} to {freq_max} cycles/sequence...")
    df_results = run_frequency_sweep(
        model=model,
        tokenizer=tokenizer,
        sequences=sequences,
        frequency_range=frequencies,
        output_path=output_path,
    )
    
    # Print summary
    print("\nSweep Summary:")
    print(df_results.to_string(index=False))
    
    # Check for successful runs
    successful_runs = df_results[df_results["status"] == "success"]
    if len(successful_runs) > 0:
        best_snr_idx = successful_runs["snr_db"].idxmax()
        best_freq = df_results.loc[best_snr_idx, "frequency_cycles_per_seq"]
        best_snr = df_results.loc[best_snr_idx, "snr_db"]
        print(f"\nBest frequency: {best_freq} cycles/sequence with SNR: {best_snr:.2f} dB")
    else:
        print("\nNo successful runs found in the sweep.")

if __name__ == "__main__":
    main()